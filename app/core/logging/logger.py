"""
Logging configuration for Orbit application.
"""

import logging
import sys
from pathlib import Path

def setup_logging(level: int = logging.INFO, log_file: Path | None = None) -> logging.Logger:
    """Configures application-wide logging output to stdout and optional file."""
    logger = logging.getLogger("orbit")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "orbit") -> logging.Logger:
    """Retrieves a logger instance for a subcomponent."""
    return logging.getLogger(name)
