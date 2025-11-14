"""Concurrency controls for asynchronous operations.

Provides a simple manager around `asyncio.Semaphore` to cap the number of
concurrent coroutines executing at once. The limit defaults to
`config.max_concurrent_requests` when available, and falls back to 5.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Iterable, List, Optional, TypeVar

T = TypeVar("T")


class ConcurrencyManager:
    """Manage concurrency limits using an asyncio.Semaphore.

    Example:
        cm = ConcurrencyManager(config)
        result = await cm.run_with_limit(coro())
        results = await cm.gather_with_limit(coros)
    """

    def __init__(
        self, config: Any | None = None, max_concurrent: Optional[int] = None
    ) -> None:
        self._limit = (
            int(max_concurrent)
            if max_concurrent is not None
            else int(getattr(config, "max_concurrent_requests", 5) or 5)
        )
        self._semaphore = asyncio.Semaphore(self._limit)

    @property
    def limit(self) -> int:
        return self._limit

    @asynccontextmanager
    async def acquire(self):  # type: ignore[override]
        """Async context manager that acquires/releases the semaphore."""
        async with self._semaphore:
            yield

    async def run_with_limit(self, coro: Awaitable[T]) -> T:
        """Run a coroutine under the concurrency limit and return its result."""
        async with self._semaphore:
            return await coro

    async def gather_with_limit(self, coros: Iterable[Awaitable[T]]) -> List[T]:
        """Gather multiple coroutines under the concurrency limit.

        This schedules each coroutine to run, ensuring that at most `limit`
        are active concurrently.
        """

        async def _run(c: Awaitable[T]) -> T:
            async with self._semaphore:
                return await c

        return await asyncio.gather(*(_run(c) for c in coros))
