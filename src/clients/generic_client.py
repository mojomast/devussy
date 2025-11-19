"""Generic OpenAI-compatible client using aiohttp.

Works with any provider that implements the OpenAI-compatible
Chat Completions API at <base_url>/v1/chat/completions.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Iterable, List
import logging

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient


class GenericOpenAIClient(LLMClient):
    """Generic client for OpenAI-compatible endpoints."""

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        self._api_key = getattr(llm, "api_key", None)
        self._base_url = getattr(llm, "base_url", None)
        self._model = getattr(llm, "model", "gpt-4")
        self._temperature = getattr(llm, "temperature", 0.7)
        self._max_tokens = getattr(llm, "max_tokens", 4096)
        
        # Check for debug/verbose mode
        self._debug = getattr(config, "debug", False) or getattr(llm, "debug", False)
        # Expose last usage metadata for UI/diagnostics
        self.last_usage_metadata: dict | None = None

        retry_cfg = getattr(config, "retry", None)
        self._max_attempts = getattr(retry_cfg, "max_attempts", 3) or 3
        self._initial_delay = getattr(retry_cfg, "initial_delay", 1.0) or 1.0
        self._max_delay = getattr(retry_cfg, "max_delay", 60.0) or 60.0
        self._exp_base = getattr(retry_cfg, "exponential_base", 2.0) or 2.0
        
        self._logger = logging.getLogger(__name__)

    @property
    def _endpoint(self) -> str:
        """Return the OpenAI-compatible chat completions endpoint."""
        if not self._base_url:
            raise ValueError("base_url is required for generic provider")
        base = self._base_url.rstrip("/")
        return f"{base}/v1/chat/completions"

    async def _post_chat(self, prompt: str, **kwargs: Any) -> str:
        """Post to OpenAI-compatible chat completions endpoint."""
        import json
        
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "User-Agent": "DevUssY/1.0",
        }
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if top_p is not None:
            payload["top_p"] = top_p

        # DEBUG LOGGING
        if self._debug:
            print("\n" + "="*80)
            print("[GENERIC DEBUG] Making API call")
            print(f"Endpoint: {self._endpoint}")
            print(f"Model: {model}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            dbg_payload = dict(payload)
            dbg_payload["messages"] = [{"role": "user", "content": f"{prompt[:100]}..."}]
            print(f"Payload: {json.dumps(dbg_payload, indent=2)}")
            print("="*80 + "\n")
        
        self._logger.info(f"[GENERIC] Calling {self._endpoint} with model {model}")
        
        timeout_seconds = kwargs.get("api_timeout", getattr(self._config, "api_timeout", 60))
        try:
            timeout_seconds = int(timeout_seconds) if timeout_seconds is not None else 60
        except Exception:
            timeout_seconds = 60
        
        timeout = aiohttp.ClientTimeout(
            total=timeout_seconds,
            connect=30,
            sock_connect=30,
            sock_read=timeout_seconds,
        )
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self._endpoint, json=payload, headers=headers
                ) as resp:
                    if resp.status >= 400:
                        error_body = await resp.text()
                        if self._debug:
                            print("\n" + "="*80)
                            print(f"[GENERIC ERROR] Response status: {resp.status}")
                            print(f"[GENERIC ERROR] Response body: {error_body}")
                            print("="*80 + "\n")
                        self._logger.error(f"[GENERIC ERROR] {resp.status}: {error_body}")
                        raise Exception(
                            f"Generic API error {resp.status}: {error_body}\n"
                            f"Request model: {model}\n"
                            f"Endpoint: {self._endpoint}"
                        )
                    
                    data = await resp.json()
                    
                    # OpenAI format: choices[0].message.content
                    content = (
                        data.get("choices", [{}])[0].get("message", {}).get("content")
                    ) or ""
                    
                    # Record usage metadata if present
                    try:
                        usage = data.get("usage")
                        if usage:
                            self.last_usage_metadata = {
                                "prompt_tokens": usage.get("prompt_tokens"),
                                "completion_tokens": usage.get("completion_tokens"),
                                "total_tokens": usage.get("total_tokens"),
                                "model": model,
                            }
                    except Exception:
                        self.last_usage_metadata = None
                    
                    # DEBUG LOGGING - Success response
                    if self._debug:
                        print("\n" + "="*80)
                        print(f"[GENERIC DEBUG] Response status: {resp.status}")
                        print(f"[GENERIC DEBUG] Response data keys: {list(data.keys())}")
                        print(f"[GENERIC DEBUG] Content length: {len(content)} chars")
                        print(f"[GENERIC DEBUG] Content preview: {content[:200]}...")
                        print("="*80 + "\n")
                    
                    self._logger.info(f"[GENERIC] Success: {resp.status}, content length: {len(content)} chars")
                    
                    if not content:
                        self._logger.error(f"[GENERIC ERROR] Empty content in response! Full response: {data}")
                        print(f"\n{'='*80}\n[GENERIC ERROR] Empty content received!\nFull response: {json.dumps(data, indent=2)}\n{'='*80}\n")
                    
                    return content
        except asyncio.TimeoutError as te:
            self._logger.error(
                f"[GENERIC TIMEOUT] Request exceeded timeout of {timeout_seconds}s for model {model} at {self._endpoint}"
            )
            raise te
        except aiohttp.ClientError as ce:
            self._logger.error(f"[GENERIC CLIENT ERROR] {type(ce).__name__}: {ce}")
            raise

    async def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(
                multiplier=self._initial_delay,
                max=self._max_delay,
                exp_base=self._exp_base,
            ),
        ):
            with attempt:
                return await self._post_chat(prompt, **kwargs)

    async def generate_multiple(self, prompts: Iterable[str]) -> List[str]:
        concurrency = getattr(self._config, "max_concurrent_requests", 5) or 5
        semaphore = asyncio.Semaphore(concurrency)

        async def _one(p: str) -> str:
            async with semaphore:
                return await self.generate_completion(p)

        return await asyncio.gather(*(_one(p) for p in prompts))

    async def _post_chat_streaming(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Internal streaming chat method for generic OpenAI-compatible endpoints."""
        print("DEBUG: GenericOpenAIClient._post_chat_streaming called")
        import json
        
        model = kwargs.get("model", self._model)
        # ... (rest of setup) ...
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "User-Agent": "DevUssY/1.0",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,  # Enable streaming
        }
        if top_p is not None:
            payload["top_p"] = top_p

        timeout = aiohttp.ClientTimeout(
            total=getattr(self._config, "api_timeout", 60)
        )

        full_content = ""
        print(f"DEBUG: Generic client connecting to {self._endpoint}")
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._endpoint, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                print(f"DEBUG: Generic client connected. Status: {resp.status}")

                # Handle Server-Sent Events (SSE) streaming
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            print("DEBUG: Generic client received [DONE]")
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    # print(f"DEBUG: Generic token: {content[:5]}")
                                    full_content += content
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(content)
                                    else:
                                        callback(content)
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks
                            continue
        
        print(f"DEBUG: Generic stream finished. Total chars: {len(full_content)}")
        return full_content

    async def generate_completion_streaming(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Generate completion with streaming for generic OpenAI-compatible APIs."""
        print("DEBUG: GenericOpenAIClient.generate_completion_streaming called")
        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(
                multiplier=self._initial_delay,
                max=self._max_delay,
                exp_base=self._exp_base,
            ),
        ):
            with attempt:
                return await self._post_chat_streaming(prompt, callback, **kwargs)
