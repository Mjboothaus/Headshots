"""Logging setup and configuration using loguru."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ..constants import LOG_FORMAT


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week"
) -> None:
    """
    Set up logging configuration with loguru.
    
    Args:
        log_level: Minimum log level to capture
        log_file: Optional log file path. If None, only logs to console
        rotation: Log file rotation policy
        retention: Log file retention policy
    """
    # Remove default logger
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=log_level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            format=LOG_FORMAT,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    logger.info(f"Logging initialized with level: {log_level}")


def get_logger(name: str):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)