"""Centralized logging configuration for xScanner."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logging_configured = False


THIRD_PARTY_LOGGERS: tuple[str, ...] = (
    # HTTP clients
    "urllib3",
    "urllib3.connectionpool",
    "requests",
    "httpx",
    "httpcore",
    "httpcore.connection",
    # ASGI / web stack
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "fastapi",
    "starlette",
    "multipart",
    "python_multipart",
    "python_multipart.multipart",
    # Integrations / SDKs
    "openai",
    "google",
    "google.generativeai",
    # IO / infrastructure
    "aiofiles",
    "redis",
    # Imaging
    "PIL",
)


def setup_logging() -> None:
    global _logging_configured

    if _logging_configured:
        return

    import logging

    from ..server.config import LoggingConfig

    config = LoggingConfig.from_env()
    log_level = getattr(logging, config.level, logging.INFO)

    # Create log directory if not exists
    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Rotating file handler (rotates when file reaches max_bytes)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=config.max_bytes, backupCount=config.backup_count
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
    for logger_name in THIRD_PARTY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    import logging

    setup_logging()
    return logging.getLogger(name)
