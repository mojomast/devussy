"""Aether AI client implementation.

Aether AI provides a unified API for multiple AI models and providers.
It uses an OpenAI-compatible API format with custom endpoints.

Endpoint: https://api.aether.ai/v1 (or custom)
Models: Various models from different providers
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, List

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient


class AetherClient(LLMClient):
    """Client for Aether AI - unified API for multiple AI models."""

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        self._api_key = getattr(llm, "api_key", None)
        self._base_url = getattr(llm, "base_url", None) or "https://api.aetherapi.dev"
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

    @property
    def _endpoint(self) -> str:
        """Return the Aether AI chat completions endpoint."""
        base = self._base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return f"{base}/chat/completions"

    async def _post_chat(self, prompt: str, **kwargs: Any) -> str:
        """Post to Aether AI chat completions endpoint."""
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        # For reasoning models (e.g., gpt-5), OpenAI-style APIs prefer max_output_tokens
        max_output_tokens = kwargs.get("max_output_tokens", max_tokens)
        reasoning_effort = kwargs.get("reasoning_effort", None)
        top_p = kwargs.get("top_p", None)

        # Add headers for Aether AI
        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "User-Agent": "DevUssY/1.0",  # Identify the client
        }
        
        # Debug: log the API key being used
        logger.debug(f"[AETHER] API Key set: {bool(self._api_key)}, Key prefix: {self._api_key[:20] if self._api_key else 'NONE'}")
        
        # Use OpenAI-compatible chat format
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Supply max_output_tokens for models that support reasoning-style limits
        payload["max_output_tokens"] = max_output_tokens
        # Resolve reasoning effort from kwargs or config and include for GPT-5 family only
        resolved_reasoning = kwargs.get(
            "reasoning_effort",
            getattr(getattr(self._config, "llm", None), "reasoning_effort", None),
        )
        if ("gpt-5" in model) and resolved_reasoning:
            payload["reasoning"] = {"effort": str(resolved_reasoning)}
        if top_p is not None:
            payload["top_p"] = top_p

        # VERBOSE DEBUG LOGGING - Only show if debug mode enabled
        if self._debug:
            print("\n" + "="*80)
            print("[AETHER DEBUG] Making API call")
            print(f"Endpoint: {self._endpoint}")
            print(f"Model: {model}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            dbg_payload = dict(payload)
            dbg_payload["messages"] = [{"role": "user", "content": f"{prompt[:100]}..."}]
            print(f"Payload: {json.dumps(dbg_payload, indent=2)}")
            print("="*80 + "\n")
        logger.info(f"[AETHER] Calling {self._endpoint} with model {model}")
        
        # Determine timeout settings. Allow per-call override via kwargs["api_timeout"].
        timeout_seconds = kwargs.get("api_timeout", getattr(self._config.llm, "api_timeout", 60))
        try:
            timeout_seconds = int(timeout_seconds) if timeout_seconds is not None else 60
        except Exception:
            timeout_seconds = 60
        
        # Use generous timeout settings for frontier models
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
                    # IMPROVED ERROR HANDLING - Capture Aether's error details
                    if resp.status >= 400:
                        error_body = await resp.text()
                        if self._debug:
                            print("\n" + "="*80)
                            print(f"[AETHER ERROR] Response status: {resp.status}")
                            print(f"[AETHER ERROR] Response body: {error_body}")
                            print("="*80 + "\n")
                        logger.error(f"[AETHER ERROR] {resp.status}: {error_body}")
                        raise Exception(
                            f"Aether API error {resp.status}: {error_body}\n"
                            f"Request model: {model}\n"
                            f"Endpoint: {self._endpoint}"
                        )
                    
                    data = await resp.json()
                    
                    # OpenAI format: choices[0].message.content
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
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
                    
                    # VERBOSE DEBUG LOGGING - Success response
                    if self._debug:
                        print("\n" + "="*80)
                        print(f"[AETHER DEBUG] Response status: {resp.status}")
                        print(f"[AETHER DEBUG] Response data keys: {list(data.keys())}")
                        print(f"[AETHER DEBUG] Content length: {len(content)} chars")
                        print(f"[AETHER DEBUG] Content preview: {content[:200]}...")
                        print("="*80 + "\n")
                    logger.info(f"[AETHER] Success: {resp.status}, content length: {len(content)} chars")
                    
                    # CRITICAL: Log warning if content is empty
                    if not content:
                        logger.error(f"[AETHER ERROR] Empty content in response! Full response: {data}")
                        print(f"\n{'='*80}\n[AETHER ERROR] Empty content received!\nFull response: {json.dumps(data, indent=2)}\n{'='*80}\n")
                    
                    return content
        except asyncio.TimeoutError as te:
            # Surface a clearer message for retries/UX
            logger.error(
                f"[AETHER TIMEOUT] Request exceeded timeout of {timeout_seconds}s for model {model} at {self._endpoint}"
            )
            raise te
        except aiohttp.ClientError as ce:
            # Network-level issues
            logger.error(f"[AETHER CLIENT ERROR] {type(ce).__name__}: {ce}")
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
        self, prompt: str, callback: Any, **kwargs: Any
    ) -> str:
        """Internal streaming chat method for Aether AI."""
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
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
            "stream": True,  # Enable streaming
        }
        if top_p is not None:
            payload["top_p"] = top_p

        timeout = aiohttp.ClientTimeout(
            total=getattr(self._config.llm, "api_timeout", 60)
        )

        full_content = ""
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._endpoint, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()

                # Handle Server-Sent Events (SSE) streaming
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    full_content += content
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(content)
                                    else:
                                        callback(content)
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks
                            continue

        return full_content

    async def generate_completion_streaming(
        self, prompt: str, callback: Any, **kwargs: Any
    ) -> str:
        """Generate completion with streaming for Aether AI."""
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
