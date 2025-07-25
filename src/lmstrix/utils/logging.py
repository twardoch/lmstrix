"""Logging configuration for LMStrix."""

# this_file: src/lmstrix/utils/logging.py

import sys

from loguru import logger


def setup_logging(verbose: bool = False) -> None:
    """Configure loguru logging based on verbose flag.

    Args:
        verbose: Enable verbose output with DEBUG level logging.
    """
    # Remove default logger
    logger.remove()

    if verbose:
        # Verbose mode: show all DEBUG and above messages
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )
    else:
        # Normal mode: show only INFO and above
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        )
