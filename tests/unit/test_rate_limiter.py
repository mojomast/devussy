"""Tests for rate limiting functionality."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.rate_limiter import (
    AdaptiveRateLimiter,
    RateLimitError,
    RateLimiter,
    adaptive_rate_limiter,
    default_rate_limiter,
)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization_defaults(self):
        """Test rate limiter initialization with defaults."""
        limiter = RateLimiter()

        assert limiter.max_retries == 5
        assert limiter.base_delay == 1.0
        assert limiter.max_delay == 300.0
        assert limiter.backoff_multiplier == 2.0
        assert limiter.jitter is True
        assert limiter.show_progress is True
        assert limiter._attempt_count == 0

    def test_initialization_custom_params(self):
        """Test rate limiter initialization with custom parameters."""
        limiter = RateLimiter(
            max_retries=3,
            base_delay=2.0,
            max_delay=100.0,
            backoff_multiplier=1.5,
            jitter=False,
            show_progress=False,
        )

        assert limiter.max_retries == 3
        assert limiter.base_delay == 2.0
        assert limiter.max_delay == 100.0
        assert limiter.backoff_multiplier == 1.5
        assert limiter.jitter is False
        assert limiter.show_progress is False

    def test_reset_attempts(self):
        """Test resetting attempt counter."""
        limiter = RateLimiter()
        limiter._attempt_count = 5

        limiter.reset_attempts()

        assert limiter._attempt_count == 0

    def test_get_backoff_delay_with_retry_after(self):
        """Test backoff delay calculation with server-provided retry-after."""
        limiter = RateLimiter()

        # Should use retry_after value
        delay = limiter.get_backoff_delay(0, retry_after=10)
        assert delay == 10.0

        # Should cap retry_after to max_delay
        delay = limiter.get_backoff_delay(0, retry_after=500)
        assert delay == 300.0  # max_delay

    def test_get_backoff_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        limiter = RateLimiter(jitter=False)

        # First attempt: 1.0 * (2.0 ** 0) = 1.0
        delay = limiter.get_backoff_delay(0)
        assert delay == 1.0

        # Second attempt: 1.0 * (2.0 ** 1) = 2.0
        delay = limiter.get_backoff_delay(1)
        assert delay == 2.0

        # Third attempt: 1.0 * (2.0 ** 2) = 4.0
        delay = limiter.get_backoff_delay(2)
        assert delay == 4.0

    def test_get_backoff_delay_with_jitter(self):
        """Test backoff delay with jitter enabled."""
        limiter = RateLimiter(jitter=True)

        # With jitter, delay should be randomized but within reasonable bounds
        delays = [limiter.get_backoff_delay(0) for _ in range(10)]

        # Should have variation
        assert len(set(delays)) > 1

        # All delays should be positive and capped
        assert all(0 < d <= limiter.max_delay for d in delays)

    def test_get_backoff_delay_capped(self):
        """Test that backoff delay is capped at max_delay."""
        limiter = RateLimiter(jitter=False, max_delay=10.0)

        # High attempt should still be capped
        delay = limiter.get_backoff_delay(20)
        assert delay == 10.0

    @pytest.mark.asyncio
    async def test_wait_with_feedback_no_progress(self):
        """Test waiting without progress feedback."""
        limiter = RateLimiter(show_progress=False)

        start = time.time()
        await limiter.wait_with_feedback(0.1, 0)
        elapsed = time.time() - start

        # Should wait approximately the requested time
        assert 0.08 <= elapsed <= 0.15

    @pytest.mark.asyncio
    async def test_wait_with_feedback_short_delay(self):
        """Test waiting with progress for short delays."""
        limiter = RateLimiter(show_progress=True)

        start = time.time()
        await limiter.wait_with_feedback(0.1, 0)
        elapsed = time.time() - start

        # Should wait approximately the requested time
        assert 0.08 <= elapsed <= 0.15

    @pytest.mark.asyncio
    async def test_wait_with_feedback_long_delay(self):
        """Test waiting with progress for long delays (chunked)."""
        limiter = RateLimiter(show_progress=True)

        start = time.time()
        # Use a moderately long delay to test chunking
        await limiter.wait_with_feedback(0.5, 0)
        elapsed = time.time() - start

        # Should wait approximately the requested time
        assert 0.4 <= elapsed <= 0.7

    @pytest.mark.asyncio
    async def test_handle_rate_limit_success(self):
        """Test successful rate limit handling."""
        limiter = RateLimiter(max_retries=3, base_delay=0.1, jitter=False)

        should_retry = await limiter.handle_rate_limit(429)

        assert should_retry is True
        assert limiter._attempt_count == 1

    @pytest.mark.asyncio
    async def test_handle_rate_limit_with_headers(self):
        """Test rate limit handling with retry-after header."""
        limiter = RateLimiter(max_retries=3, base_delay=0.1)

        headers = {"Retry-After": "1"}
        should_retry = await limiter.handle_rate_limit(429, headers=headers)

        assert should_retry is True
        assert limiter._attempt_count == 1

    @pytest.mark.asyncio
    async def test_handle_rate_limit_max_retries_exceeded(self):
        """Test rate limit handling when max retries exceeded."""
        limiter = RateLimiter(max_retries=2, base_delay=0.1)
        limiter._attempt_count = 2  # Already at max

        with pytest.raises(RateLimitError) as exc_info:
            await limiter.handle_rate_limit(429)

        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.retry_after is None

    @pytest.mark.asyncio
    async def test_handle_rate_limit_non_429_status(self):
        """Test that non-429 status codes return False."""
        limiter = RateLimiter()

        should_retry = await limiter.handle_rate_limit(200)
        assert should_retry is False

        should_retry = await limiter.handle_rate_limit(500)
        assert should_retry is False

    def test_extract_retry_after_from_headers(self):
        """Test extracting retry-after value from headers."""
        limiter = RateLimiter()

        # Test standard header
        headers = {"Retry-After": "60"}
        assert limiter._extract_retry_after(headers) == 60

        # Test case variation
        headers = {"retry-after": "30"}
        assert limiter._extract_retry_after(headers) == 30

        # Test x-ratelimit header
        headers = {"x-ratelimit-retry-after": "45"}
        assert limiter._extract_retry_after(headers) == 45

    def test_extract_retry_after_missing(self):
        """Test extracting retry-after when not present."""
        limiter = RateLimiter()

        # No headers
        assert limiter._extract_retry_after(None) is None

        # Empty headers
        assert limiter._extract_retry_after({}) is None

        # Different headers
        headers = {"Content-Type": "application/json"}
        assert limiter._extract_retry_after(headers) is None

    def test_extract_retry_after_invalid_value(self):
        """Test handling invalid retry-after values."""
        limiter = RateLimiter()

        # Non-numeric value
        headers = {"Retry-After": "invalid"}
        assert limiter._extract_retry_after(headers) is None

        # HTTP date format (not supported, returns None)
        headers = {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}
        assert limiter._extract_retry_after(headers) is None

    def test_should_retry_rate_limit_errors(self):
        """Test identifying rate limit errors."""
        limiter = RateLimiter()

        # Test various rate limit error messages
        assert limiter.should_retry(Exception("rate limit exceeded")) is True
        assert limiter.should_retry(Exception("Too many requests")) is True
        assert limiter.should_retry(Exception("HTTP 429 error")) is True
        assert limiter.should_retry(Exception("quota exceeded")) is True
        assert limiter.should_retry(Exception("throttled by server")) is True
        assert limiter.should_retry(Exception("rate_limit_exceeded")) is True

    def test_should_retry_non_rate_limit_errors(self):
        """Test that non-rate-limit errors are not retried."""
        limiter = RateLimiter()

        assert limiter.should_retry(Exception("Connection failed")) is False
        assert limiter.should_retry(Exception("Invalid API key")) is False
        assert limiter.should_retry(Exception("Internal server error")) is False

    @pytest.mark.asyncio
    async def test_execute_with_rate_limiting_success(self):
        """Test successful execution without rate limiting."""
        limiter = RateLimiter()

        async def mock_func():
            return "success"

        result = await limiter.execute_with_rate_limiting(mock_func)

        assert result == "success"
        assert limiter._attempt_count == 0

    @pytest.mark.asyncio
    async def test_execute_with_rate_limiting_retry_then_success(self):
        """Test execution that fails once with rate limit then succeeds."""
        limiter = RateLimiter(base_delay=0.1, jitter=False)

        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("rate limit exceeded")
            return "success"

        result = await limiter.execute_with_rate_limiting(mock_func)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_rate_limiting_non_rate_limit_error(self):
        """Test that non-rate-limit errors are not retried."""
        limiter = RateLimiter()

        async def mock_func():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            await limiter.execute_with_rate_limiting(mock_func)

    @pytest.mark.asyncio
    async def test_execute_with_rate_limiting_max_retries(self):
        """Test that max retries are respected."""
        limiter = RateLimiter(max_retries=2, base_delay=0.05, jitter=False)

        async def mock_func():
            raise Exception("rate limit exceeded")

        with pytest.raises(Exception, match="rate limit"):
            await limiter.execute_with_rate_limiting(mock_func)


class TestAdaptiveRateLimiter:
    """Tests for AdaptiveRateLimiter class."""

    def test_initialization(self):
        """Test adaptive rate limiter initialization."""
        limiter = AdaptiveRateLimiter()

        assert limiter.max_retries == 5
        assert limiter._request_times == []
        assert limiter._rate_limit_times == []
        assert limiter._adaptive_delay == 0.0

    def test_record_request(self):
        """Test recording successful requests."""
        limiter = AdaptiveRateLimiter()

        limiter.record_request()
        assert len(limiter._request_times) == 1

        limiter.record_request()
        assert len(limiter._request_times) == 2

    def test_record_request_cleanup_old(self):
        """Test that old request records are cleaned up."""
        limiter = AdaptiveRateLimiter()

        # Add old timestamp
        old_time = time.time() - 400  # 6+ minutes ago
        limiter._request_times.append(old_time)

        # Record new request
        limiter.record_request()

        # Old timestamp should be removed
        assert len(limiter._request_times) == 1
        assert limiter._request_times[0] > old_time

    def test_record_rate_limit(self):
        """Test recording rate limit occurrences."""
        limiter = AdaptiveRateLimiter()

        initial_delay = limiter._adaptive_delay

        limiter.record_rate_limit()

        assert len(limiter._rate_limit_times) == 1
        assert limiter._adaptive_delay > initial_delay

    def test_record_rate_limit_increases_delay(self):
        """Test that recording rate limits increases adaptive delay."""
        limiter = AdaptiveRateLimiter()

        for _ in range(5):
            limiter.record_rate_limit()

        # Adaptive delay should increase
        assert limiter._adaptive_delay >= 5.0

    def test_record_rate_limit_capped(self):
        """Test that adaptive delay is capped."""
        limiter = AdaptiveRateLimiter()

        # Record many rate limits
        for _ in range(100):
            limiter.record_rate_limit()

        # Should be capped at 30.0
        assert limiter._adaptive_delay == 30.0

    def test_record_rate_limit_cleanup_old(self):
        """Test that old rate limit records are cleaned up."""
        limiter = AdaptiveRateLimiter()

        # Add old timestamp
        old_time = time.time() - 700  # 11+ minutes ago
        limiter._rate_limit_times.append(old_time)

        # Record new rate limit
        limiter.record_rate_limit()

        # Old timestamp should be removed
        assert len(limiter._rate_limit_times) == 1
        assert limiter._rate_limit_times[0] > old_time

    def test_get_request_rate_insufficient_data(self):
        """Test request rate calculation with insufficient data."""
        limiter = AdaptiveRateLimiter()

        # No requests
        assert limiter.get_request_rate() == 0.0

        # One request
        limiter.record_request()
        assert limiter.get_request_rate() == 0.0

    def test_get_request_rate_calculation(self):
        """Test request rate calculation."""
        limiter = AdaptiveRateLimiter()

        # Simulate requests over time
        base_time = time.time()
        limiter._request_times = [
            base_time,
            base_time + 1,
            base_time + 2,
            base_time + 3,
            base_time + 4,
        ]

        rate = limiter.get_request_rate()

        # 5 requests over 4 seconds = 1.25 requests/second
        assert 1.2 <= rate <= 1.3

    @pytest.mark.asyncio
    async def test_pre_request_delay_no_delay(self):
        """Test pre-request delay when adaptive delay is zero."""
        limiter = AdaptiveRateLimiter()

        start = time.time()
        await limiter.pre_request_delay()
        elapsed = time.time() - start

        # Should complete quickly with no delay
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_pre_request_delay_with_delay(self):
        """Test pre-request delay with adaptive delay set."""
        limiter = AdaptiveRateLimiter()
        limiter._adaptive_delay = 0.2

        start = time.time()
        await limiter.pre_request_delay()
        elapsed = time.time() - start

        # Should wait approximately the adaptive delay
        assert 0.15 <= elapsed <= 0.3

    @pytest.mark.asyncio
    async def test_pre_request_delay_gradual_reduction(self):
        """Test that adaptive delay is gradually reduced."""
        limiter = AdaptiveRateLimiter()
        limiter._adaptive_delay = 1.0

        await limiter.pre_request_delay()

        # Delay should be reduced by 0.1
        assert limiter._adaptive_delay == pytest.approx(0.9, abs=0.01)

    @pytest.mark.asyncio
    async def test_pre_request_delay_not_negative(self):
        """Test that adaptive delay doesn't go negative."""
        limiter = AdaptiveRateLimiter()
        limiter._adaptive_delay = 0.05

        await limiter.pre_request_delay()

        # Should be clamped to 0
        assert limiter._adaptive_delay == 0.0

    @pytest.mark.asyncio
    async def test_handle_rate_limit_records(self):
        """Test that handling rate limits records the event."""
        limiter = AdaptiveRateLimiter(base_delay=0.05, jitter=False)

        initial_count = len(limiter._rate_limit_times)

        await limiter.handle_rate_limit(429)

        # Should record the rate limit
        assert len(limiter._rate_limit_times) == initial_count + 1


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_initialization_basic(self):
        """Test basic RateLimitError initialization."""
        error = RateLimitError("Rate limit exceeded")

        assert str(error) == "Rate limit exceeded"
        assert error.retry_after is None

    def test_initialization_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)

        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60


class TestGlobalInstances:
    """Tests for global rate limiter instances."""

    def test_default_rate_limiter_exists(self):
        """Test that default_rate_limiter is available."""
        assert default_rate_limiter is not None
        assert isinstance(default_rate_limiter, RateLimiter)

    def test_adaptive_rate_limiter_exists(self):
        """Test that adaptive_rate_limiter is available."""
        assert adaptive_rate_limiter is not None
        assert isinstance(adaptive_rate_limiter, AdaptiveRateLimiter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
