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

        # Determine the effective base root for Requesty.
        # Rules:
        # - Default MUST include `/v1`:
        #       https://router.requesty.ai/v1
        # - If user provides REQUESTY_BASE_URL / llm.base_url:
        #       * If it already ends with '/v1' (or '/v1/'), use as-is (normalized).
        #       * If it is exactly 'https://router.requesty.ai', append '/v1'.
        #       * If it already includes '/chat/completions', we will detect that in _endpoint.
        raw_base = getattr(llm, "base_url", None)
        if not raw_base:
            # Strong default with /v1
            raw_base = "https://router.requesty.ai/v1"
        raw_base = raw_base.strip()
        lower = raw_base.lower().rstrip("/")

        if lower == "https://router.requesty.ai":
            # If user only gave host, fix to /v1
            effective = "https://router.requesty.ai/v1"
        else:
            effective = raw_base.rstrip("/")

        self._base_url = effective

        self._model = getattr(llm, "model", "openai/gpt-4o-mini")
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
        """Return the Requesty chat completions endpoint.

        Guarantees:
        - Default: https://router.requesty.ai/v1/chat/completions
        - If self._base_url already ends with '/chat/completions', use it as-is.
        - Otherwise, append '/chat/completions' to the normalized base.
        """
        base = (self._base_url or "https://router.requesty.ai/v1").rstrip("/")
        lower = base.lower()

        # If caller configured full endpoint, don't double-append.
        if lower.endswith("/chat/completions"):
            return base

        # Always append /chat/completions to the base root (which for default includes /v1).
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
        # For reasoning models (e.g., gpt-5), OpenAI-style APIs prefer max_output_tokens
        max_output_tokens = kwargs.get("max_output_tokens", max_tokens)
        reasoning_effort = kwargs.get("reasoning_effort", None)
        top_p = kwargs.get("top_p", None)

        # Add recommended headers for better analytics
        headers = {
            "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://devussy.app",  # Optional but improves analytics
            "X-Title": "DevUssY",  # Optional but improves analytics
        }
        
        # Debug: log the API key being used
        logger.debug(f"[REQUESTY] API Key set: {bool(self._api_key)}, Key prefix: {self._api_key[:20] if self._api_key else 'NONE'}")
        
        # Use OpenAI chat format
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
            print("[REQUESTY DEBUG] Making API call")
            print(f"Endpoint: {self._endpoint}")
            print(f"Model: {model}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            dbg_payload = dict(payload)
            dbg_payload["messages"] = [{"role": "user", "content": f"{prompt[:100]}..."}]
            print(f"Payload: {json.dumps(dbg_payload, indent=2)}")
            print("="*80 + "\n")
        logger.info(f"[REQUESTY] Calling {self._endpoint} with model {model}")
        
        # Determine timeout settings. Allow per-call override via kwargs["api_timeout"].
        timeout_seconds = kwargs.get("api_timeout", getattr(self._config.llm, "api_timeout", 60))
        try:
            timeout_seconds = int(timeout_seconds) if timeout_seconds is not None else 60
        except Exception:
            timeout_seconds = 60
        
        # Important: Many frontier models can take >60s to return a response.
        # Use a generous total timeout and explicit sock_read/connect timeouts.
        # We keep 'total' so the whole request can take up to timeout_seconds.
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
                    # IMPROVED ERROR HANDLING - Capture Requesty's error details
                    if resp.status >= 400:
                        error_body = await resp.text()
                        if self._debug:
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
                        print(f"[REQUESTY DEBUG] Response status: {resp.status}")
                        print(f"[REQUESTY DEBUG] Response data keys: {list(data.keys())}")
                        print(f"[REQUESTY DEBUG] Content length: {len(content)} chars")
                        print(f"[REQUESTY DEBUG] Content preview: {content[:200]}...")
                        print("="*80 + "\n")
                    logger.info(f"[REQUESTY] Success: {resp.status}, content length: {len(content)} chars")
                    
                    # CRITICAL: Log warning if content is empty
                    if not content:
                        logger.error(f"[REQUESTY ERROR] Empty content in response! Full response: {data}")
                        print(f"\n{'='*80}\n[REQUESTY ERROR] Empty content received!\nFull response: {json.dumps(data, indent=2)}\n{'='*80}\n")
                    
                    return content
        except asyncio.TimeoutError as te:
            # Surface a clearer message for retries/UX
            logger.error(
                f"[REQUESTY TIMEOUT] Request exceeded timeout of {timeout_seconds}s for model {model} at {self._endpoint}"
            )
            raise te
        except aiohttp.ClientError as ce:
            # Network-level issues
            logger.error(f"[REQUESTY CLIENT ERROR] {type(ce).__name__}: {ce}")
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
