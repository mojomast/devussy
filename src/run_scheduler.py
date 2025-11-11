"""Runtime scheduler for task queueing and batch execution."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, List, Optional, TypeVar

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RuntimeScheduler:
    """Schedule and execute tasks with concurrency control."""

    def __init__(self, max_concurrent: int = 5):
        """Initialize the scheduler.

        Args:
            max_concurrent: Maximum number of concurrent tasks
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.task_queue: List[Awaitable[Any]] = []
        logger.debug(f"RuntimeScheduler initialized (max_concurrent={max_concurrent})")

    def add_task(self, task: Awaitable[T]) -> None:
        """Add a task to the queue.

        Args:
            task: Async task to execute
        """
        self.task_queue.append(task)
        logger.debug(f"Added task to queue (total: {len(self.task_queue)})")

    async def execute_batch(
        self, callback: Optional[Callable[[int, Any], None]] = None
    ) -> List[Any]:
        """Execute all queued tasks with concurrency limit.

        Args:
            callback: Optional callback function called after each task completes.
                      Receives (task_index, result) as arguments.

        Returns:
            List of results from all tasks
        """
        if not self.task_queue:
            logger.warning("No tasks in queue to execute")
            return []

        logger.info(f"Executing batch of {len(self.task_queue)} tasks")

        async def _run_with_callback(idx: int, task: Awaitable[T]) -> T:
            async with self.semaphore:
                result = await task
                if callback:
                    callback(idx, result)
                return result

        tasks_with_idx = [
            _run_with_callback(i, task) for i, task in enumerate(self.task_queue)
        ]

        results = await asyncio.gather(*tasks_with_idx, return_exceptions=True)

        # Clear the queue after execution
        self.task_queue.clear()

        # Log any errors
        error_count = sum(1 for r in results if isinstance(r, Exception))
        if error_count > 0:
            logger.warning(f"Batch execution completed with {error_count} error(s)")
        else:
            logger.info("Batch execution completed successfully")

        return results

    async def execute_single(self, task: Awaitable[T]) -> T:
        """Execute a single task with concurrency limit.

        Args:
            task: Async task to execute

        Returns:
            Task result
        """
        async with self.semaphore:
            logger.debug("Executing single task")
            return await task

    def clear_queue(self) -> None:
        """Clear all queued tasks."""
        count = len(self.task_queue)
        self.task_queue.clear()
        logger.info(f"Cleared {count} task(s) from queue")

    @property
    def queue_size(self) -> int:
        """Get the current queue size."""
        return len(self.task_queue)
