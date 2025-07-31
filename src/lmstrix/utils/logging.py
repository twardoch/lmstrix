"""Logging configuration for LMStrix."""

# this_file: src/lmstrix/utils/logging.py  # noqa: ERA001

import sys
from typing import Any

from loguru import logger

# Export logger so it can be imported from this module
__all__ = ["logger", "setup_logging"]


def setup_logging(verbose: bool = False) -> None:
    """Configure loguru logging based on verbose flag.

    Args:
        verbose: Enable verbose output with DEBUG level logging.
    """
    # Remove default logger
    logger.remove()

    def format_log(record: Any) -> str:
        """Custom formatter for colored output with level shortcuts."""
        level_name = record["level"].name

        # Level colors and shortcuts
        level_formats = {
            "SUCCESS": ("<green>[S]</green>", "<green>"),
            "ERROR": ("<red>[E]</red>", "<red>"),
            "WARNING": ("<yellow>[W]</yellow>", "<yellow>"),
            "INFO": ("<white>[I]</white>", "<white>"),
            "DEBUG": ("<dim>[D]</dim>", "<dim>"),
        }

        default_format = ("<white>[?]</white>", "<white>")
        level_tag, color_tag = level_formats.get(level_name, default_format)
        close_tag = color_tag.replace("<", "</").split(">")[0] + ">"

        message = f"{level_tag} {color_tag}{record['message']}{close_tag}"

        if verbose:
            name = record["name"]
            func = str(record["function"])
            func = func.replace("<", r"\<").replace(">", r"\>")
            line = record["line"]
            message += f" <dim>{name}:{func}:{line}</dim>"

        return message + "\n"

    if verbose:
        # Verbose mode: show all DEBUG and above messages with function+line
        logger.add(
            sys.stderr,
            level="DEBUG",
            format=format_log,
        )
    else:
        # Normal mode: show only INFO and above
        logger.add(
            sys.stderr,
            level="INFO",
            format=format_log,
        )
