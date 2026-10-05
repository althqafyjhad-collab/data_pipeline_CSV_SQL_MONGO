"""
logging_setup.py - Shared logging configuration.
================================================

Each pipeline gets its own log file so the SQL run and the CSV run
never mix their records.
"""

import logging
from typing import Optional

from common.paths import ensure_directories


def get_logger(
    name: str,
    log_file,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Return a logger that writes to `log_file` and to the console.
    """
    ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid attaching the same handlers twice when re-imported.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_failure(
    logger: logging.Logger,
    step: str,
    error: Exception,
) -> None:
    """
    Record a failure consistently in the log file.
    """
    logger.error("[%s] failed: %s", step, error)