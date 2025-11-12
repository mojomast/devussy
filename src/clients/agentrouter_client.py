from __future__ import annotations

import asyncio
from typing import Any, Iterable, List, Dict
import logging

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient


class AgentRouterClient(LLMClient):
    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        self._api_key = getattr(llm, "api_key", None)
        # AgentRouter OpenAI-compatible base (can be overridden)
        self._base_url = getattr(llm, "base_url", None) or "https://agentrouter.org"
        self._model = getattr(llm, "model", "gpt-4")
        self._temperature = getattr(llm, "temperature", 0.7)
        self._max_tokens = getattr(llm, "max_tokens", 4096)

        # Spoof profile: one of {"roocode", "claude-code", "codex"}
        # Default to roocode since docs emphasize OpenAI-compatible setup
        self._spoof_as = getattr(llm, "spoof_as", None) or getattr(config, "spoof_as", None) or "roocode"
        # Optional custom headers map to merge/override
        self._extra_headers: Dict[str, str] = getattr(llm, "extra_headers", None) or {}

        self._debug = getattr(config, "debug", False) or getattr(llm, "debug", False)
        self._logger = logging.getLogger(__name__)

        retry_cfg = getattr(config, "retry", None)
        self._max_attempts = getattr(retry_cfg, "max_attempts", 3) or 3
        self._initial_delay = getattr(retry_cfg, "initial_delay", 1.0) or 1.0
        self._max_delay = getattr(retry_cfg, "max_delay", 60.0) or 60.0
        self._exp_base = getattr(retry_cfg, "exponential_base", 2.0) or 2.0

    @property
    def _endpoint(self) -> str:
        base = self._base_url.rstrip("/")
        # OpenAI-compatible path
        if base.endswith("/chat"):
            return f"{base}/completions"
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def _spoof_headers(self) -> Dict[str, str]:
        # Minimal, plausible headers to mimic known tools
        profiles = {
            "roocode": {
                "User-Agent": "Mozilla/5.0 VSCode/RooCode",
                "X-Client-Name": "RooCode",
                "X-Extension-Name": "RooCode",
                "HTTP-Referer": "vscode://roocode",
                "X-Title": "RooCode",
            },
            "claude-code": {
                "User-Agent": "@anthropic-ai/claude-code",
                "X-Client-Name": "claude-code",
                "HTTP-Referer": "https://anthropic.com/claude-code",
                "X-Title": "Claude Code",
            },
            "codex": {
                "User-Agent": "@openai/codex-cli",
                "X-Client-Name": "codex",
                "HTTP-Referer": "https://openai.com/codex",
                "X-Title": "Codex",
            },
        }
        base_headers = profiles.get(str(self._spoof_as).lower(), profiles["roocode"]).copy()
        # Merge user-specified overrides
        base_headers.update(self._extra_headers or {})
        return base_headers

    async def _post_chat(self, prompt: str, **kwargs: Any) -> str:
        import json

        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self._spoof_headers())

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}] ,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if top_p is not None:
            payload["top_p"] = top_p

        # Reasoning effort pass-through for gpt-5 only
        resolved_reasoning = kwargs.get(
            "reasoning_effort",
            getattr(getattr(self._config, "llm", None), "reasoning_effort", None),
        )
        if ("gpt-5" in str(model)) and resolved_reasoning:
            payload["reasoning"] = {"effort": str(resolved_reasoning)}

        if self._debug:
            print("\n" + "=" * 80)
            print("[AGENTROUTER DEBUG] Making API call")
            print(f"Endpoint: {self._endpoint}")
            print(f"Model: {model}")
            dbg_headers = dict(headers)
            if "Authorization" in dbg_headers and isinstance(dbg_headers["Authorization"], str):
                dbg_headers["Authorization"] = dbg_headers["Authorization"][:24] + "…" if dbg_headers["Authorization"] else ""
            print(f"Headers: {json.dumps(dbg_headers, indent=2)}")
            dbg_payload = dict(payload)
            dbg_payload["messages"] = [{"role": "user", "content": f"{prompt[:100]}..."}]
            print(f"Payload: {json.dumps(dbg_payload, indent=2)}")
            print("=" * 80 + "\n")

        timeout_seconds = kwargs.get("api_timeout", getattr(self._config.llm, "api_timeout", 60))
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
                async with session.post(self._endpoint, json=payload, headers=headers) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        self._logger.error(f"[AGENTROUTER ERROR] {resp.status}: {text}")
                        raise Exception(
                            f"AgentRouter API error {resp.status}: {text}\nModel: {model}\nEndpoint: {self._endpoint}"
                        )
                    data = await resp.json()
                    content = (
                        data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    )
                    # Usage metadata
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
                    return content or ""
        except asyncio.TimeoutError:
            self._logger.error(
                f"[AGENTROUTER TIMEOUT] Exceeded {timeout_seconds}s for model {model} at {self._endpoint}"
            )
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

    async def _post_chat_streaming(self, prompt: str, callback: Any, **kwargs: Any) -> str:
        import json

        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json",
        }
        headers.update(self._spoof_headers())

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if top_p is not None:
            payload["top_p"] = top_p

        timeout = aiohttp.ClientTimeout(total=getattr(self._config.llm, "api_timeout", 60))

        full_content = ""
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self._endpoint, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
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
                            continue
        return full_content

    async def generate_completion_streaming(self, prompt: str, callback: Any, **kwargs: Any) -> str:
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
