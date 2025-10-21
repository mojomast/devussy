"""Requesty client implementation.

This is a placeholder implementation for a provider referred to as
"Requesty". It assumes a simple JSON API with an endpoint like:

POST <base_url>/v1/generate
{
  "prompt": "...",
  "model": "model-id",
  "temperature": 0.7,
  "max_tokens": 1024,
  "top_p": 1.0
}

Response:
{
  "text": "generated content..."
}
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, List

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient


class RequestyClient(LLMClient):
    """Client for the Requesty API (hypothetical)."""

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        self._api_key = getattr(llm, "api_key", None)
        self._base_url = getattr(llm, "base_url", None) or ""
        self._model = getattr(llm, "model", "default")
        self._temperature = getattr(llm, "temperature", 0.7)
        self._max_tokens = getattr(llm, "max_tokens", 1024)

        retry_cfg = getattr(config, "retry", None)
        self._max_attempts = getattr(retry_cfg, "max_attempts", 3) or 3
        self._initial_delay = getattr(retry_cfg, "initial_delay", 1.0) or 1.0
        self._max_delay = getattr(retry_cfg, "max_delay", 60.0) or 60.0
        self._exp_base = getattr(retry_cfg, "exponential_base", 2.0) or 2.0

    @property
    def _endpoint(self) -> str:
        base = self._base_url.rstrip("/")
        return f"{base}/v1/generate"

    async def _post_generate(self, prompt: str, **kwargs: Any) -> str:
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if top_p is not None:
            payload["top_p"] = top_p

        timeout = aiohttp.ClientTimeout(
            total=getattr(self._config.llm, "api_timeout", 60)
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._endpoint, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # Prefer `text`, fallback to OpenAI-like shape if present
                text = data.get("text")
                if isinstance(text, str):
                    return text
                return (
                    data.get("choices", [{}])[0].get("message", {}).get("content")
                ) or ""

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
                return await self._post_generate(prompt, **kwargs)

    async def generate_multiple(self, prompts: Iterable[str]) -> List[str]:
        concurrency = getattr(self._config, "max_concurrent_requests", 5) or 5
        semaphore = asyncio.Semaphore(concurrency)

        async def _one(p: str) -> str:
            async with semaphore:
                return await self.generate_completion(p)

        return await asyncio.gather(*(_one(p) for p in prompts))
