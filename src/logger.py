"""Logging configuration for the DevPlan Orchestrator.

This module centralizes logging setup for both file and console handlers.
File logs keep the full, detailed format for debugging, while console logs
use a user-friendly, emoji-aware formatter that integrates with
``ui_tokens.render``.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .ui_tokens import render


class ConsoleEmojiFormatter(logging.Formatter):
    """Console formatter with short timestamps and emoji rendering.

    Console output is intentionally lightweight:

    - Prefixes each line with ``[HH:MM]`` (local time)
    - Omits logger name/module noise
    - Lowercases the level name and exposes it as a token so callers can
      include tags like ``[INFO]`` or higher-level UI tags which are then
      passed through :func:`ui_tokens.render`.
    """

    default_time_format = "%H:%M"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        # Build a minimal time prefix without touching the underlying record
        created_dt = datetime.fromtimestamp(record.created)
        time_str = created_dt.strftime(self.default_time_format)

        # Base message uses the record's message only
        message = super().format(record)

        # Apply ui token rendering so tags like [ROCKET], [OK], etc. show as emojis
        rendered_message = render(message)

        return f"[{time_str}] {rendered_message}"


class DeduplicatingFilter(logging.Filter):
    """Filter that suppresses consecutive duplicate INFO-level messages.

    This keeps the console from spamming the same status line repeatedly
    while leaving the underlying log records untouched for file logging.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self._last_msg: Optional[str] = None
        self._last_level: Optional[int] = None

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        msg = record.getMessage()
        if record.levelno == logging.INFO and self._last_level == logging.INFO and msg == self._last_msg:
            return False

        self._last_msg = msg
        self._last_level = record.levelno
        return True


class ConsoleSilencerFilter(logging.Filter):
    """Filter that hides records explicitly marked for console suppression."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        return not getattr(record, "suppress_console", False)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/devussy.log",
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only console logging is used.
        log_format: Custom log format string. If None, uses default format.

    Returns:
        Configured root logger
    """
    # Default *file* format if not provided. The console handler uses a
    # friendlier formatter regardless of this value.
    if log_format is None:
        log_format = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter used for file logs (fully detailed)
    file_formatter = logging.Formatter(log_format)

    # Console handler with emoji-aware, compact formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ConsoleEmojiFormatter("%(message)s"))
    console_handler.addFilter(ConsoleSilencerFilter())
    console_handler.addFilter(DeduplicatingFilter())
    root_logger.addHandler(console_handler)

    # File handler (if log_file is provided)
    if log_file:
        log_path = Path(log_file)
        # Create logs directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function to configure logging from config dict
def configure_logging_from_config(config: dict) -> logging.Logger:
    """
    Configure logging from a configuration dictionary.

    Args:
        config: Configuration dictionary containing log_level, log_file, log_format

    Returns:
        Configured root logger
    """
    log_level = config.get("log_level", "INFO")
    log_file = config.get("log_file", "logs/devussy.log")
    log_format = config.get("log_format")

    return setup_logging(log_level=log_level, log_file=log_file, log_format=log_format)
