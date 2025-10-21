"""Abstract LLM client interface for provider-agnostic usage.

This module defines the core asynchronous interface that all concrete
LLM provider clients must implement. Implementations should be
non-blocking (async-first) and expose a simple sync wrapper for
convenience when used outside of async contexts.
"""

from __future__ import annotations

import abc
import asyncio
from typing import Any, Callable, Iterable, List


class LLMClient(abc.ABC):
    """Abstract base class for all LLM clients.

    Concrete implementations should accept a configuration object in their
    constructor (e.g., an instance with `.llm`, `.retry`, and other fields),
    but the exact type is intentionally kept generic here to avoid tight
    coupling to config models.
    """

    def __init__(self, config: Any) -> None:
        self._config = config

    @abc.abstractmethod
    async def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generate a single completion for the provided prompt.

        Args:
            prompt: The input prompt to send to the model.
            **kwargs: Provider-specific generation parameters. Common keys
                may include: `model`, `temperature`, `max_tokens`, `top_p`.

        Returns:
            The generated text content from the provider.
        """

    async def generate_multiple(self, prompts: Iterable[str]) -> List[str]:
        """Generate completions for multiple prompts concurrently.

        This default implementation uses an asyncio.Semaphore based on
        `config.max_concurrent_requests` if available. Providers may
        override for custom batching/optimizations.
        """
        concurrency = getattr(self._config, "max_concurrent_requests", 5) or 5
        semaphore = asyncio.Semaphore(concurrency)

        async def _one(p: str) -> str:
            async with semaphore:
                return await self.generate_completion(p)

        return await asyncio.gather(*(_one(p) for p in prompts))

    def generate_completion_sync(self, prompt: str, **kwargs: Any) -> str:
        """Synchronous wrapper for `generate_completion`.

        This must NOT be called from within a running event loop.
        If an event loop is detected, a RuntimeError is raised to avoid
        deadlocks or nested loop issues.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "generate_completion_sync() called inside an active event loop. "
                "Use the async `generate_completion` method instead."
            )

        return asyncio.run(self.generate_completion(prompt, **kwargs))

    async def generate_completion_streaming(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Generate completion with streaming token callback.

        This default implementation simulates streaming by calling the
        non-streaming method and chunking the result. Providers should
        override this for true streaming support.

        Args:
            prompt: The input prompt to send to the model.
            callback: Function called with each token/chunk as it arrives.
            **kwargs: Provider-specific generation parameters.

        Returns:
            The complete generated text content.
        """
        # Default implementation: simulate streaming
        full_response = await self.generate_completion(prompt, **kwargs)

        # Import here to avoid circular imports
        from .streaming import StreamingSimulator

        simulator = StreamingSimulator()
        await simulator.simulate_streaming(full_response, callback)

        return full_response

    def generate_completion_streaming_sync(
        self, prompt: str, callback: Callable[[str], Any], **kwargs: Any
    ) -> str:
        """Synchronous wrapper for streaming completion.

        Args:
            prompt: The input prompt to send to the model.
            callback: Function called with each token/chunk as it arrives.
            **kwargs: Provider-specific generation parameters.

        Returns:
            The complete generated text content.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "generate_completion_streaming_sync() called inside an active "
                "event loop. Use the async `generate_completion_streaming` "
                "method instead."
            )

        return asyncio.run(
            self.generate_completion_streaming(prompt, callback, **kwargs)
        )
