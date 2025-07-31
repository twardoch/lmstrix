"""Utility functions for parsing context parameters."""

from typing import Any

from lmstrix.utils.logging import logger


def parse_out_ctx(
    out_ctx: int | str,
    max_context: int,
    fallback_context: int | None = None,
) -> int:
    """Parse out_ctx parameter which can be an integer or percentage string.

    Args:
        out_ctx: Either an integer token count or a string like "80%" for percentage of max context
        max_context: Maximum context size (tested_max_context or context_limit)
        fallback_context: Fallback context size if max_context is None or 0

    Returns:
        Parsed token count as integer

    Examples:
        >>> parse_out_ctx(1000, 4096)
        1000
        >>> parse_out_ctx("50%", 4096)
        2048
        >>> parse_out_ctx("75%", 8192)
        6144
    """
    # Handle integer input
    if isinstance(out_ctx, int):
        return out_ctx

    # Handle string input
    if isinstance(out_ctx, str):
        out_ctx = out_ctx.strip()

        # Check if it's a percentage
        if out_ctx.endswith("%"):
            try:
                # Parse percentage value
                percentage_str = out_ctx[:-1].strip()
                percentage = float(percentage_str)

                if percentage < 0 or percentage > 100:
                    raise ValueError(f"Percentage must be between 0 and 100, got {percentage}")

                # Use fallback if max_context is not available
                effective_max = max_context if max_context and max_context > 0 else fallback_context

                if not effective_max or effective_max <= 0:
                    raise ValueError(
                        "No valid maximum context available for percentage calculation",
                    )

                # Calculate token count from percentage
                token_count = int((percentage / 100.0) * effective_max)

                logger.debug(
                    f"Parsed out_ctx '{out_ctx}' as {percentage}% of {effective_max} = {token_count} tokens",
                )

                return token_count

            except ValueError as e:
                raise ValueError(f"Invalid percentage format '{out_ctx}': {e}") from e

        # Try to parse as integer
        try:
            return int(out_ctx)
        except ValueError:
            raise ValueError(
                f"Invalid out_ctx format '{out_ctx}'. Expected integer or percentage (e.g., '80%')",
            )

    raise TypeError(f"out_ctx must be int or str, got {type(out_ctx).__name__}")


def get_model_max_context(model: Any, use_tested: bool = True) -> int | None:
    """Get the maximum context for a model.

    Args:
        model: Model object with context information
        use_tested: If True, prefer tested_max_context over declared context_limit

    Returns:
        Maximum context size or None if not available
    """
    if use_tested and hasattr(model, "tested_max_context") and model.tested_max_context:
        return model.tested_max_context

    if hasattr(model, "context_limit") and model.context_limit:
        return model.context_limit

    return None
