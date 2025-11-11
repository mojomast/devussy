"""Concurrency control tests for DevPlan Orchestrator."""

import asyncio
import time
from unittest.mock import Mock

import pytest

from src.concurrency import ConcurrencyManager


@pytest.fixture
def mock_config():
    """Mock configuration with max_concurrent_requests."""
    config = Mock()
    config.max_concurrent_requests = 3
    return config


@pytest.fixture
def mock_config_none():
    """Mock configuration with None max_concurrent_requests."""
    config = Mock()
    config.max_concurrent_requests = None
    return config


class TestConcurrencyManager:
    """Test ConcurrencyManager class."""

    def test_init_with_config(self, mock_config):
        """Test initialization with config object."""
        cm = ConcurrencyManager(mock_config)
        assert cm.limit == 3

    def test_init_with_config_none_value(self, mock_config_none):
        """Test initialization with config having None value."""
        cm = ConcurrencyManager(mock_config_none)
        assert cm.limit == 5  # Should fall back to default

    def test_init_with_no_config(self):
        """Test initialization without config falls back to default."""
        cm = ConcurrencyManager()
        assert cm.limit == 5

    def test_init_with_explicit_max_concurrent(self):
        """Test initialization with explicit max_concurrent parameter."""
        cm = ConcurrencyManager(max_concurrent=10)
        assert cm.limit == 10

    def test_explicit_max_concurrent_overrides_config(self, mock_config):
        """Test explicit max_concurrent overrides config value."""
        cm = ConcurrencyManager(mock_config, max_concurrent=8)
        assert cm.limit == 8

    def test_init_with_zero_max_concurrent(self):
        """Test initialization with zero max_concurrent."""
        cm = ConcurrencyManager(max_concurrent=0)
        assert cm.limit == 0

    @pytest.mark.asyncio
    async def test_acquire_context_manager(self):
        """Test acquire context manager."""
        cm = ConcurrencyManager(max_concurrent=2)

        # Track if we're inside the context
        acquired = False

        async with cm.acquire():
            acquired = True
            assert acquired is True

        # After exiting context, we should still be able to use acquire again
        assert acquired is True

    @pytest.mark.asyncio
    async def test_run_with_limit_single_task(self):
        """Test running single task with limit."""
        cm = ConcurrencyManager(max_concurrent=2)

        async def task():
            await asyncio.sleep(0.01)
            return "completed"

        result = await cm.run_with_limit(task())
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_run_with_limit_respects_concurrency(self):
        """Test that run_with_limit respects concurrency limits."""
        cm = ConcurrencyManager(max_concurrent=2)

        active_tasks = []
        max_concurrent = 0

        async def tracking_task(task_id: int):
            nonlocal max_concurrent
            active_tasks.append(task_id)
            max_concurrent = max(max_concurrent, len(active_tasks))

            await asyncio.sleep(0.02)  # Simulate work

            active_tasks.remove(task_id)
            return f"task_{task_id}_done"

        # Run 5 tasks concurrently - only 2 should run at once
        tasks = [cm.run_with_limit(tracking_task(i)) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all("done" in result for result in results)
        assert max_concurrent == 2  # Should never exceed the limit

    @pytest.mark.asyncio
    async def test_gather_with_limit_basic(self):
        """Test basic gather_with_limit functionality."""
        cm = ConcurrencyManager(max_concurrent=3)

        async def simple_task(value: int):
            await asyncio.sleep(0.01)
            return value * 2

        tasks = [simple_task(i) for i in range(5)]
        results = await cm.gather_with_limit(tasks)

        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]

    @pytest.mark.asyncio
    async def test_gather_with_limit_respects_concurrency(self):
        """Test that gather_with_limit respects concurrency limits."""
        cm = ConcurrencyManager(max_concurrent=2)

        active_tasks = []
        max_concurrent_observed = 0

        async def monitoring_task(task_id: int):
            nonlocal max_concurrent_observed
            active_tasks.append(task_id)
            max_concurrent_observed = max(max_concurrent_observed, len(active_tasks))

            await asyncio.sleep(0.01)  # Simulate some work

            active_tasks.remove(task_id)
            return task_id

        # Create 6 tasks but only 2 should run concurrently
        tasks = [monitoring_task(i) for i in range(6)]
        results = await cm.gather_with_limit(tasks)

        assert len(results) == 6
        assert sorted(results) == list(range(6))
        assert max_concurrent_observed == 2  # Should not exceed limit

    @pytest.mark.asyncio
    async def test_gather_with_limit_empty_iterable(self):
        """Test gather_with_limit with empty iterable."""
        cm = ConcurrencyManager(max_concurrent=3)

        results = await cm.gather_with_limit([])
        assert results == []

    @pytest.mark.asyncio
    async def test_gather_with_limit_single_task(self):
        """Test gather_with_limit with single task."""
        cm = ConcurrencyManager(max_concurrent=3)

        async def single_task():
            return "single"

        results = await cm.gather_with_limit([single_task()])
        assert results == ["single"]

    @pytest.mark.asyncio
    async def test_concurrency_limit_zero(self):
        """Test behavior with concurrency limit of zero."""
        cm = ConcurrencyManager(max_concurrent=0)

        # With limit 0, the semaphore will block forever
        # This is actually expected behavior - let's test this with a timeout
        async def zero_limit_task():
            return "zero_limit"

        # This should timeout because semaphore with 0 permits blocks forever
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(cm.run_with_limit(zero_limit_task()), timeout=0.1)

    @pytest.mark.asyncio
    async def test_concurrent_access_to_acquire(self):
        """Test multiple concurrent accesses to acquire context manager."""
        cm = ConcurrencyManager(max_concurrent=2)

        acquired_count = 0
        max_acquired = 0

        async def acquire_task():
            nonlocal acquired_count, max_acquired
            async with cm.acquire():
                acquired_count += 1
                max_acquired = max(max_acquired, acquired_count)
                await asyncio.sleep(0.01)
                acquired_count -= 1

        # Start 4 tasks, but only 2 should be able to acquire at once
        tasks = [acquire_task() for _ in range(4)]
        await asyncio.gather(*tasks)

        assert max_acquired == 2
        assert acquired_count == 0  # All should have released

    @pytest.mark.asyncio
    async def test_exception_handling_in_run_with_limit(self):
        """Test exception handling in run_with_limit."""
        cm = ConcurrencyManager(max_concurrent=2)

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("Task failed")

        with pytest.raises(ValueError, match="Task failed"):
            await cm.run_with_limit(failing_task())

    @pytest.mark.asyncio
    async def test_exception_handling_in_gather_with_limit(self):
        """Test exception handling in gather_with_limit."""
        cm = ConcurrencyManager(max_concurrent=2)

        async def good_task(value: int):
            await asyncio.sleep(0.01)
            return value

        async def bad_task():
            await asyncio.sleep(0.01)
            raise RuntimeError("Bad task")

        tasks = [good_task(1), bad_task(), good_task(3)]

        with pytest.raises(RuntimeError, match="Bad task"):
            await cm.gather_with_limit(tasks)

    @pytest.mark.asyncio
    async def test_semaphore_releases_on_exception(self):
        """Test that semaphore is properly released when exception occurs."""
        cm = ConcurrencyManager(max_concurrent=1)

        # First, cause an exception to occur
        async def exception_task():
            await asyncio.sleep(0.01)
            raise ValueError("Expected exception")

        try:
            await cm.run_with_limit(exception_task())
        except ValueError:
            pass  # Expected

        # Now verify we can still run another task (semaphore was released)
        async def success_task():
            return "success"

        result = await cm.run_with_limit(success_task())
        assert result == "success"

    @pytest.mark.asyncio
    async def test_concurrent_run_with_limit_and_gather(self):
        """Test mixing run_with_limit and gather_with_limit calls."""
        cm = ConcurrencyManager(max_concurrent=2)

        results = []

        async def append_task(value: str):
            await asyncio.sleep(0.01)
            results.append(value)
            return value

        # Start some individual tasks
        task1 = cm.run_with_limit(append_task("individual1"))
        task2 = cm.run_with_limit(append_task("individual2"))

        # Start a gather operation
        gather_tasks = [append_task(f"gather{i}") for i in range(3)]
        task3 = cm.gather_with_limit(gather_tasks)

        # Wait for all to complete
        individual_results = await asyncio.gather(task1, task2)
        gather_results = await task3

        assert len(individual_results) == 2
        assert len(gather_results) == 3
        assert len(results) == 5  # All tasks should have completed

    @pytest.mark.asyncio
    async def test_performance_with_many_tasks(self):
        """Test performance characteristics with many concurrent tasks."""
        cm = ConcurrencyManager(max_concurrent=5)

        start_time = time.time()

        async def quick_task(task_id: int):
            await asyncio.sleep(0.001)  # Very short task
            return task_id

        # Run 50 tasks
        tasks = [quick_task(i) for i in range(50)]
        results = await cm.gather_with_limit(tasks)

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == 50
        assert sorted(results) == list(range(50))
        # Should complete reasonably quickly (less than 1 second for 50 tiny tasks)
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_limit_property_immutable(self):
        """Test that limit property reflects the configured limit."""
        cm = ConcurrencyManager(max_concurrent=7)
        assert cm.limit == 7

        # Limit should remain constant
        async def dummy_task():
            return "dummy"

        await cm.run_with_limit(dummy_task())
        assert cm.limit == 7  # Should not change after use

    def test_limit_property_with_various_configs(self):
        """Test limit property with various configuration scenarios."""
        # Test with integer config attribute
        config_int = Mock()
        config_int.max_concurrent_requests = 15
        cm_int = ConcurrencyManager(config_int)
        assert cm_int.limit == 15

        # Test with string config attribute (should be converted to int)
        config_str = Mock()
        config_str.max_concurrent_requests = "8"
        cm_str = ConcurrencyManager(config_str)
        assert cm_str.limit == 8

        # Test with no config attribute
        config_missing = Mock()
        del config_missing.max_concurrent_requests  # Remove the attribute entirely
        cm_missing = ConcurrencyManager(config_missing)
        assert cm_missing.limit == 5  # Default fallback

    @pytest.mark.asyncio
    async def test_very_high_concurrency_limit(self):
        """Test behavior with very high concurrency limit."""
        cm = ConcurrencyManager(max_concurrent=1000)

        async def fast_task(value: int):
            return value

        # Even with high limit, should work correctly
        tasks = [fast_task(i) for i in range(10)]
        results = await cm.gather_with_limit(tasks)

        assert len(results) == 10
        assert sorted(results) == list(range(10))
