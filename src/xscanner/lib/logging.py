"""Centralized logging configuration for xScanner."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logging_configured = False


def setup_logging() -> None:
    """Configure logging system from environment config.

    Should be called once at application startup.
    Creates rotating file handler and console handler for root logger.
    """
    global _logging_configured

    if _logging_configured:
        return

    from ..server.config import get_config

    config = get_config()
    log_level = getattr(logging, config.logging.level, logging.INFO)

    # Create log directory if not exists
    log_path = Path(config.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Rotating file handler (rotates when file reaches max_bytes)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=config.logging.max_bytes, backupCount=config.logging.backup_count
    )
    file_handler.setLevel(log_level)  # Use configured log level
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger.addHandler(file_handler)

    # Console handler for info level and above (disabled during tests)
    import sys

    is_pytest = "pytest" in sys.modules

    if not is_pytest:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)  # Use configured log level
        console_handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Automatically sets up logging if not already configured.

    Args:
        name: Name for the logger (usually module name or component name)

    Returns:
        Configured logger instance
    """
    setup_logging()
    return logging.getLogger(name)
