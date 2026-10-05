"""
logging_setup.py - Shared logging configuration.
================================================

Each pipeline gets its own log file so the SQL run and the CSV run
never mix their records.

The loggers write to the file only. The console is reserved for the
data itself, so a run never mixes log lines with DataFrame previews.
"""

import logging
from typing import Optional

from common.paths import ensure_directories


def get_logger(
    name: str,
    log_file,
    level: int = logging.INFO,
    console: bool = False,
) -> logging.Logger:
    """
    Return a logger that writes to `log_file`.

    Parameters
    ----------
    name:
        Logger name, e.g. ``"csv_pipeline"``.
    log_file:
        Destination log file.
    level:
        Minimum level recorded.
    console:
        Also mirror the records to the console. Off by default so the
        terminal shows the data rather than the log.
    """
    ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Keep the records out of the root logger, otherwise Python's
    # fallback handler would print them to the console again.
    logger.propagate = False

    # Avoid attaching the same handlers twice when re-imported.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
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