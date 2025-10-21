"""Retry utilities using tenacity with exponential backoff.

Provides a decorator factory `retry_with_backoff` that can be parameterized
from an application config object or explicit keyword arguments.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, TypeVar, cast

from tenacity import RetryCallState
from tenacity import retry as tenacity_retry
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def _log_retry(retry_state: RetryCallState) -> None:
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning("Retry attempt %s due to %r", attempt, exc)


def retry_with_backoff(
    *,
    config: Any | None = None,
    max_attempts: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_base: Optional[float] = None,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Create a tenacity-based retry decorator with exponential backoff.

    Parameters can be sourced from `config.retry` if provided and not
    overridden explicitly.
    """

    retry_cfg = getattr(config, "retry", None)
    attempts = int(
        max_attempts
        if max_attempts is not None
        else getattr(retry_cfg, "max_attempts", 3) or 3
    )
    init_delay = float(
        initial_delay
        if initial_delay is not None
        else getattr(retry_cfg, "initial_delay", 1.0) or 1.0
    )
    m_delay = float(
        max_delay
        if max_delay is not None
        else getattr(retry_cfg, "max_delay", 60.0) or 60.0
    )
    exp_base = float(
        exponential_base
        if exponential_base is not None
        else getattr(retry_cfg, "exponential_base", 2.0) or 2.0
    )

    def _decorator(func: F) -> F:
        wrapped = tenacity_retry(
            reraise=True,
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(
                multiplier=init_delay, max=m_delay, exp_base=exp_base
            ),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=_log_retry,
        )(func)
        return cast(F, wrapped)

    return _decorator
