"""OpenAI client implementation of LLMClient using AsyncOpenAI."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Iterable, List

from openai import AsyncOpenAI
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient
from ..rate_limiter import RateLimiter


class OpenAIClient(LLMClient):
    """LLM client backed by OpenAI's Chat Completions API.

    Notes:
        - Uses async-first API via `openai.AsyncOpenAI`.
        - Applies exponential backoff retry according to config.retry.
        - Supports common params: model, temperature, max_tokens, top_p.
    """

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        api_key = getattr(llm, "api_key", None)
        org = getattr(llm, "org_id", None)
        base_url = getattr(llm, "base_url", None)
        self._model = getattr(llm, "model", "gpt-4")
        # Expose last usage metadata for UI/diagnostics
        self.last_usage_metadata: dict | None = None

        # Async OpenAI client
        self._client = AsyncOpenAI(api_key=api_key, organization=org, base_url=base_url)

        # Retry settings
        retry_cfg = getattr(config, "retry", None)
        self._max_attempts = getattr(retry_cfg, "max_attempts", 3) or 3
        self._initial_delay = getattr(retry_cfg, "initial_delay", 1.0) or 1.0
        self._max_delay = getattr(retry_cfg, "max_delay", 60.0) or 60.0
        self._exp_base = getattr(retry_cfg, "exponential_base", 2.0) or 2.0

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            max_retries=self._max_attempts,
            base_delay=self._initial_delay,
            max_delay=self._max_delay,
        )

    async def _chat_completion(self, prompt: str, **kwargs: Any) -> str:
        model = kwargs.get("model", self._model)
        temperature = kwargs.get(
            "temperature", getattr(self._config, "temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", getattr(self._config, "max_tokens", 4096)
        )
        top_p = kwargs.get("top_p", None)

        resp = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **({"top_p": top_p} if top_p is not None else {}),
        )
        # Record usage if provided by API
        try:
            usage = getattr(resp, "usage", None)
            if usage is not None:
                self.last_usage_metadata = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                    "model": model,
                }
        except Exception:
            # Best-effort; ignore parsing issues
            self.last_usage_metadata = None
        content = resp.choices[0].message.content or ""
        return content

    async def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        # Use rate limiter for intelligent retry handling
        return await self._rate_limiter.execute_with_rate_limiting(
            self._chat_completion_with_retry, prompt, **kwargs
        )

    async def _chat_completion_with_retry(self, prompt: str, **kwargs: Any) -> str:
        # Tenacity-based retry with exponential backoff
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
                return await self._chat_completion(prompt, **kwargs)

    async def generate_multiple(self, prompts: Iterable[str]) -> List[str]:
        concurrency = getattr(self._config, "max_concurrent_requests", 5) or 5
        semaphore = asyncio.Semaphore(concurrency)

        async def _one(p: str) -> str:
            async with semaphore:
                return await self.generate_completion(p)

        return await asyncio.gather(*(_one(p) for p in prompts))

    async def _chat_completion_streaming(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Internal streaming chat completion method."""
        model = kwargs.get("model", self._model)
        temperature = kwargs.get(
            "temperature", getattr(self._config, "temperature", 0.7)
        )
        max_tokens = kwargs.get(
            "max_tokens", getattr(self._config, "max_tokens", 4096)
        )
        top_p = kwargs.get("top_p", None)

        stream = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **({"top_p": top_p} if top_p is not None else {}),
        )

        full_content = ""
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    token = delta.content
                    full_content += token
                    if asyncio.iscoroutinefunction(callback):
                        await callback(token)
                    else:
                        callback(token)

        return full_content

    async def generate_completion_streaming(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Generate completion with real OpenAI streaming."""
        # Use rate limiter for streaming as well
        return await self._rate_limiter.execute_with_rate_limiting(
            self._chat_completion_streaming_with_retry, prompt, callback, **kwargs
        )

    async def _chat_completion_streaming_with_retry(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Internal streaming method with tenacity retry."""
        # Tenacity-based retry with exponential backoff
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
                return await self._chat_completion_streaming(prompt, callback, **kwargs)
