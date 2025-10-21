"""
Logging configuration for the DevPlan Orchestrator.

Provides console and file logging with configurable levels and formatting.
"""

import logging
from pathlib import Path
from typing import Optional


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
    # Default format if not provided
    if log_format is None:
        log_format = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file is provided)
    if log_file:
        log_path = Path(log_file)
        # Create logs directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
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
