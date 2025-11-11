"""Retry decorator tests for DevPlan Orchestrator."""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest

from src.retry import retry_with_backoff


@pytest.fixture
def mock_config():
    """Mock configuration with retry settings."""
    config = Mock()
    config.retry = Mock()
    config.retry.max_attempts = 3
    config.retry.initial_delay = 0.1  # Use small delays for tests
    config.retry.max_delay = 2.0
    config.retry.exponential_base = 2.0
    return config


@pytest.fixture
def mock_config_none():
    """Mock configuration with None retry settings."""
    config = Mock()
    config.retry = None
    return config


class TestRetryWithBackoff:
    """Test retry_with_backoff decorator."""

    def test_decorator_with_config(self, mock_config):
        """Test decorator initialization with config object."""
        call_count = 0

        @retry_with_backoff(config=mock_config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt fails")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_decorator_with_explicit_params(self):
        """Test decorator with explicit parameters."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=2, initial_delay=0.05, max_delay=1.0, exponential_base=1.5
        )
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("First attempt fails")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_decorator_no_config(self):
        """Test decorator with no config uses defaults."""
        call_count = 0

        @retry_with_backoff()
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt fails")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_decorator_config_none(self, mock_config_none):
        """Test decorator with config.retry = None uses defaults."""
        call_count = 0

        @retry_with_backoff(config=mock_config_none)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt fails")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_explicit_params_override_config(self, mock_config):
        """Test explicit parameters override config values."""
        call_count = 0

        @retry_with_backoff(config=mock_config, max_attempts=1)  # Override to 1
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            test_func()

        assert call_count == 1  # Only tried once due to override

    def test_max_attempts_reached(self, mock_config):
        """Test that function fails after max_attempts."""
        call_count = 0

        @retry_with_backoff(config=mock_config)  # max_attempts = 3
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")

        with pytest.raises(ValueError, match="Attempt 3 failed"):
            test_func()

        assert call_count == 3

    def test_no_retry_on_success(self, mock_config):
        """Test that successful function is not retried."""
        call_count = 0

        @retry_with_backoff(config=mock_config)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_exponential_backoff_timing(self):
        """Test exponential backoff timing behavior."""
        call_count = 0
        call_times = []

        @retry_with_backoff(max_attempts=3, initial_delay=0.1, exponential_base=2.0)
        def test_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise ValueError("Not ready yet")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count == 3
        assert len(call_times) == 3

        # Check that delays are approximately correct
        # First retry should wait ~0.1s, second retry ~0.2s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Allow some tolerance for timing
        assert 0.08 <= delay1 <= 0.15  # ~0.1s ± tolerance
        assert 0.18 <= delay2 <= 0.25  # ~0.2s ± tolerance

    def test_custom_exception_types(self):
        """Test retry behavior with custom exception types."""
        call_count = 0

        # Should retry on ValueError but not on TypeError
        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, retry_exceptions=(ValueError,)
        )
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Should retry")
            elif call_count == 2:
                raise TypeError("Should not retry")
            return "success"

        with pytest.raises(TypeError, match="Should not retry"):
            test_func()

        assert call_count == 2  # Retried once for ValueError, then failed on TypeError

    def test_async_function_retry(self):
        """Test retry decorator with async functions."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        async def async_test_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)  # Simulate async work
            if call_count < 2:
                raise ValueError("First attempt fails")
            return "async_success"

        async def run_test():
            result = await async_test_func()
            return result

        result = asyncio.run(run_test())
        assert result == "async_success"
        assert call_count == 2

    def test_return_value_preservation(self, mock_config):
        """Test that return values are preserved correctly."""

        @retry_with_backoff(config=mock_config)
        def return_dict():
            return {"key": "value", "number": 42}

        result = return_dict()
        assert result == {"key": "value", "number": 42}

        @retry_with_backoff(config=mock_config)
        def return_list():
            return [1, 2, 3, "test"]

        result = return_list()
        assert result == [1, 2, 3, "test"]

        @retry_with_backoff(config=mock_config)
        def return_none():
            return None

        result = return_none()
        assert result is None

    def test_function_arguments_preservation(self, mock_config):
        """Test that function arguments are preserved through retries."""
        call_count = 0
        received_args = []
        received_kwargs = []

        @retry_with_backoff(config=mock_config)
        def test_func_with_args(arg1, arg2, kwarg1=None, kwarg2="default"):
            nonlocal call_count
            call_count += 1
            received_args.append((arg1, arg2))
            received_kwargs.append({"kwarg1": kwarg1, "kwarg2": kwarg2})

            if call_count < 2:
                raise ValueError("First attempt fails")
            return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"

        result = test_func_with_args("a", "b", kwarg1="c", kwarg2="d")
        assert result == "a-b-c-d"
        assert call_count == 2
        assert len(received_args) == 2
        assert all(args == ("a", "b") for args in received_args)
        assert all(
            kwargs == {"kwarg1": "c", "kwarg2": "d"} for kwargs in received_kwargs
        )

    def test_zero_max_attempts(self):
        """Test behavior with zero max attempts."""
        call_count = 0

        @retry_with_backoff(max_attempts=0)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Should not retry")

        # With 0 attempts, function should not be called at all
        # But tenacity behavior with 0 attempts is to try once
        with pytest.raises(ValueError):
            test_func()

        assert call_count == 1

    def test_max_delay_enforcement(self):
        """Test that max delay is enforced."""
        call_count = 0
        call_times = []

        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.1,
            max_delay=0.15,  # Small max delay
            exponential_base=2.0,
        )
        def test_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 4:
                raise ValueError("Not ready yet")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 4

        # Verify that delays don't exceed max_delay
        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]
        for delay in delays:
            assert delay <= 0.2  # Allow some tolerance

    @patch("src.retry.logger")
    def test_retry_logging(self, mock_logger, mock_config):
        """Test that retry attempts are logged."""
        call_count = 0

        @retry_with_backoff(config=mock_config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt fails")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

        # Verify logging was called
        mock_logger.warning.assert_called_once()
        args, kwargs = mock_logger.warning.call_args
        assert "Retry attempt" in args[0]
        assert args[1] == 1  # First retry is attempt 1

    def test_nested_exceptions(self):
        """Test retry behavior with nested exceptions."""
        call_count = 0

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First exception")
            return "success"  # Should succeed on retry

        result = test_func()
        assert result == "success"
        assert call_count == 2  # Should retry once and succeed

    def test_complex_config_scenarios(self):
        """Test various configuration scenarios."""
        # Test with missing config attributes
        incomplete_config = Mock()
        incomplete_config.retry = Mock()
        # Only set some attributes
        incomplete_config.retry.max_attempts = 2
        # Set others to None to test defaults
        incomplete_config.retry.initial_delay = None
        incomplete_config.retry.max_delay = None
        incomplete_config.retry.exponential_base = None

        call_count = 0

        @retry_with_backoff(config=incomplete_config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry needed")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_string_config_values(self):
        """Test handling of string configuration values."""
        config = Mock()
        config.retry = Mock()
        config.retry.max_attempts = "3"  # String instead of int
        config.retry.initial_delay = "0.1"  # String instead of float
        config.retry.max_delay = "2.0"
        config.retry.exponential_base = "2.0"

        call_count = 0

        @retry_with_backoff(config=config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry needed")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2
