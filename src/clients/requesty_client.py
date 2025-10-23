"""Requesty client implementation.

Requesty is an OpenAI-compatible API gateway that routes requests to 300+ models.
It uses the standard OpenAI chat completions API format.

Endpoint: https://router.requesty.ai/v1/chat/completions
Models: Use format "provider/model" (e.g., "openai/gpt-4o", "anthropic/claude-3-opus")
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, List

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..llm_client import LLMClient


class RequestyClient(LLMClient):
    """Client for Requesty AI - OpenAI-compatible API gateway."""

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        llm = getattr(config, "llm", None)
        self._api_key = getattr(llm, "api_key", None)
        self._base_url = getattr(llm, "base_url", None) or "https://router.requesty.ai/v1"
        self._model = getattr(llm, "model", "openai/gpt-4o-mini")
        self._temperature = getattr(llm, "temperature", 0.7)
        self._max_tokens = getattr(llm, "max_tokens", 1024)

        retry_cfg = getattr(config, "retry", None)
        self._max_attempts = getattr(retry_cfg, "max_attempts", 3) or 3
        self._initial_delay = getattr(retry_cfg, "initial_delay", 1.0) or 1.0
        self._max_delay = getattr(retry_cfg, "max_delay", 60.0) or 60.0
        self._exp_base = getattr(retry_cfg, "exponential_base", 2.0) or 2.0

    @property
    def _endpoint(self) -> str:
        """Return the OpenAI-compatible chat completions endpoint."""
        base = self._base_url.rstrip("/")
        return f"{base}/chat/completions"

    async def _post_chat(self, prompt: str, **kwargs: Any) -> str:
        """Post to OpenAI-compatible chat completions endpoint."""
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        model = kwargs.get("model", self._model)
        
        # VALIDATE MODEL FORMAT - Requesty requires provider/model format
        if "/" not in model:
            error_msg = (
                f"Invalid model format for Requesty: '{model}'. "
                f"Must use provider/model format (e.g., 'openai/gpt-4o', 'anthropic/claude-3-5-sonnet'). "
                f"See https://docs.requesty.ai/models for available models."
            )
            logger.error(f"[REQUESTY ERROR] {error_msg}")
            raise ValueError(error_msg)
        
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        top_p = kwargs.get("top_p", None)

        # Add recommended headers for better analytics
        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://devussy.app",  # Optional but improves analytics
            "X-Title": "DevUssY",  # Optional but improves analytics
        }
        
        # Use OpenAI chat format
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if top_p is not None:
            payload["top_p"] = top_p

        # VERBOSE DEBUG LOGGING - User requested this!
        print("\n" + "="*80)
        print("[REQUESTY DEBUG] Making API call")
        print(f"Endpoint: {self._endpoint}")
        print(f"Model: {model}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps({**payload, 'messages': [{'role': 'user', 'content': f'{prompt[:100]}...'}]}, indent=2)}")
        print("="*80 + "\n")
        logger.info(f"[REQUESTY] Calling {self._endpoint} with model {model}")

        timeout = aiohttp.ClientTimeout(
            total=getattr(self._config.llm, "api_timeout", 60)
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._endpoint, json=payload, headers=headers
            ) as resp:
                # IMPROVED ERROR HANDLING - Capture Requesty's error details
                if resp.status >= 400:
                    error_body = await resp.text()
                    print("\n" + "="*80)
                    print(f"[REQUESTY ERROR] Response status: {resp.status}")
                    print(f"[REQUESTY ERROR] Response body: {error_body}")
                    print("="*80 + "\n")
                    logger.error(f"[REQUESTY ERROR] {resp.status}: {error_body}")
                    raise Exception(
                        f"Requesty API error {resp.status}: {error_body}\n"
                        f"Request model: {model}\n"
                        f"Endpoint: {self._endpoint}"
                    )
                
                data = await resp.json()
                
                # VERBOSE DEBUG LOGGING - Success response
                print("\n" + "="*80)
                print(f"[REQUESTY DEBUG] Response status: {resp.status}")
                print(f"[REQUESTY DEBUG] Response preview: {str(data)[:200]}...")
                print("="*80 + "\n")
                logger.info(f"[REQUESTY] Success: {resp.status}")
                
                # OpenAI format: choices[0].message.content
                return (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

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
