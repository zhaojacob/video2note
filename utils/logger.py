"""
Logging configuration for the video note system
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import LOGGING_CONFIG, OUTPUT_DIR


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = None
) -> logging.Logger:
    """
    Setup a logger with console and file handlers

    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level
    log_level = level or LOGGING_CONFIG.get("level", "INFO")
    logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        LOGGING_CONFIG.get(
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_path = log_file or LOGGING_CONFIG.get("file")
    if file_path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger"""
    return setup_logger(name)


# Module-level loggers
system_logger = get_logger("video_note_system")
