"""Rate limiting handler for LLM API requests.

This module provides RateLimiter class to handle HTTP 429 responses
with intelligent backoff strategies and user feedback.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Exception raised when rate limits are exceeded and cannot be handled."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Handle rate limiting for LLM API requests with intelligent backoff.

    Provides various backoff strategies and user feedback during wait periods.
    """

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        show_progress: bool = True,
    ):
        """Initialize the rate limiter.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            show_progress: Whether to show progress during waits
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.show_progress = show_progress
        self._attempt_count = 0

    def reset_attempts(self) -> None:
        """Reset the attempt counter for a new request sequence."""
        self._attempt_count = 0

    def get_backoff_delay(
        self, attempt: int, retry_after: Optional[int] = None
    ) -> float:
        """Calculate backoff delay for a given attempt.

        Args:
            attempt: Current attempt number (0-based)
            retry_after: Server-suggested retry delay from Retry-After header

        Returns:
            Delay in seconds
        """
        if retry_after is not None:
            # Respect server's suggestion, but cap it
            delay = min(float(retry_after), self.max_delay)
            logger.info(f"Using server-suggested delay: {delay}s")
            return delay

        # Exponential backoff
        delay = self.base_delay * (self.backoff_multiplier**attempt)

        # Add jitter if enabled
        if self.jitter:
            import random

            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor

        # Cap the delay
        delay = min(delay, self.max_delay)

        return delay

    async def wait_with_feedback(self, delay: float, attempt: int) -> None:
        """Wait for the specified delay with user feedback.

        Args:
            delay: Delay in seconds
            attempt: Current attempt number
        """
        if not self.show_progress:
            await asyncio.sleep(delay)
            return

        logger.info(
            f"Rate limited - attempt {attempt + 1}/{self.max_retries + 1}. "
            f"Waiting {delay:.1f}s..."
        )

        # Show progress in chunks for long waits
        if delay > 10:
            chunk_size = min(10, delay / 4)
            remaining = delay

            while remaining > 0:
                wait_time = min(chunk_size, remaining)
                await asyncio.sleep(wait_time)
                remaining -= wait_time

                if remaining > 0:
                    print(f"  ... {remaining:.1f}s remaining", flush=True)
        else:
            await asyncio.sleep(delay)

        logger.info("Resuming request...")

    async def handle_rate_limit(
        self,
        status_code: int,
        headers: Optional[Dict[str, Any]] = None,
        response_text: Optional[str] = None,
    ) -> bool:
        """Handle a rate limit response.

        Args:
            status_code: HTTP status code (should be 429)
            headers: Response headers (may contain Retry-After)
            response_text: Response text for additional context

        Returns:
            True if should retry, False if should give up

        Raises:
            RateLimitError: If max retries exceeded
        """
        if status_code != 429:
            return False

        if self._attempt_count >= self.max_retries:
            raise RateLimitError(
                f"Rate limit exceeded after {self.max_retries} attempts",
                retry_after=self._extract_retry_after(headers),
            )

        # Extract retry-after from headers
        retry_after = self._extract_retry_after(headers)

        # Calculate backoff delay
        delay = self.get_backoff_delay(self._attempt_count, retry_after)

        # Log context if available
        if response_text:
            logger.warning(f"Rate limit response: {response_text}")

        # Wait with feedback
        await self.wait_with_feedback(delay, self._attempt_count)

        self._attempt_count += 1
        return True

    def _extract_retry_after(self, headers: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract retry-after value from response headers.

        Args:
            headers: Response headers

        Returns:
            Retry-after value in seconds, or None if not found
        """
        if not headers:
            return None

        # Check various header formats
        for key in ["retry-after", "Retry-After", "x-ratelimit-retry-after"]:
            value = headers.get(key)
            if value:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    # Handle HTTP date format or invalid values
                    continue

        return None

    def should_retry(self, exception: Exception) -> bool:
        """Check if an exception indicates we should retry with rate limiting.

        Args:
            exception: The exception that occurred

        Returns:
            True if this looks like a rate limit error
        """
        # Check for common rate limit indicators
        error_message = str(exception).lower()

        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
            "throttled",
            "rate_limit_exceeded",
        ]

        return any(indicator in error_message for indicator in rate_limit_indicators)

    async def execute_with_rate_limiting(self, func, *args, **kwargs) -> Any:
        """Execute a function with automatic rate limit handling.

        Args:
            func: The async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The function's return value

        Raises:
            RateLimitError: If rate limits cannot be handled
        """
        self.reset_attempts()

        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if not self.should_retry(e):
                    # Not a rate limit error, re-raise
                    raise

                # Try to handle as rate limit
                try:
                    should_retry = await self.handle_rate_limit(429)
                    if not should_retry:
                        raise
                except RateLimitError:
                    logger.error("Rate limiting failed, giving up")
                    raise e


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts to observed rate limit patterns."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._request_times = []
        self._rate_limit_times = []
        self._adaptive_delay = 0.0

    def record_request(self) -> None:
        """Record a successful request timestamp."""
        current_time = time.time()
        self._request_times.append(current_time)

        # Keep only recent requests (last 5 minutes)
        cutoff = current_time - 300
        self._request_times = [t for t in self._request_times if t > cutoff]

    def record_rate_limit(self) -> None:
        """Record a rate limit occurrence."""
        current_time = time.time()
        self._rate_limit_times.append(current_time)

        # Keep only recent rate limits (last 10 minutes)
        cutoff = current_time - 600
        self._rate_limit_times = [t for t in self._rate_limit_times if t > cutoff]

        # Increase adaptive delay
        self._adaptive_delay = min(self._adaptive_delay + 1.0, 30.0)

    def get_request_rate(self) -> float:
        """Calculate current request rate (requests per second)."""
        if len(self._request_times) < 2:
            return 0.0

        time_span = self._request_times[-1] - self._request_times[0]
        return len(self._request_times) / max(time_span, 1.0)

    async def pre_request_delay(self) -> None:
        """Add adaptive delay before making requests."""
        if self._adaptive_delay > 0:
            logger.debug(f"Adaptive pre-request delay: {self._adaptive_delay:.1f}s")
            await asyncio.sleep(self._adaptive_delay)

            # Gradually reduce adaptive delay
            self._adaptive_delay = max(0.0, self._adaptive_delay - 0.1)

    async def handle_rate_limit(
        self,
        status_code: int,
        headers: Optional[Dict[str, Any]] = None,
        response_text: Optional[str] = None,
    ) -> bool:
        """Handle rate limit with adaptive learning."""
        self.record_rate_limit()
        return await super().handle_rate_limit(status_code, headers, response_text)


# Global rate limiter instance for easy use
default_rate_limiter = RateLimiter()
adaptive_rate_limiter = AdaptiveRateLimiter()
