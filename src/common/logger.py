"""Logging utilities for AI Short Factory."""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import Config


def setup_logger(
    name: str = "ai_short_factory",
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """Set up and return a logger instance.

    Args:
        name: Logger name
        log_file: Optional log file name (saved to OUTPUT_DIR/logs)
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        Config.ensure_output_dirs()
        log_path = Config.LOGS_DIR / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger
