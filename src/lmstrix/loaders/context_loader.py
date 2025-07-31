"""Context file loading functionality."""

from pathlib import Path

import tiktoken

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.utils.logging import logger


def load_context(
    file_path: str | Path,
    encoding: str = "utf-8",
    verbose: bool = False,
) -> str:
    """Load context text from a file.

    Args:
        file_path: Path to the context file.
        encoding: File encoding (default: utf-8).
        verbose: Enable verbose logging.

    Returns:
        Content of the file as a string.

    Raises:
        ConfigurationError: If the file cannot be read.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    # Convert to Path object
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        raise ConfigurationError(
            "context_file",
            f"Context file not found: {path}",
            {"path": str(path)},
        )

    # Read the file
    try:
        content = path.read_text(encoding=encoding)
    except Exception as e:
        raise ConfigurationError(
            "context_file",
            f"Failed to read context file: {e}",
            {"path": str(path), "encoding": encoding, "error": str(e)},
        ) from e

    # Log statistics
    size_bytes = len(content.encode(encoding))
    size_mb = size_bytes / (1024 * 1024)
    line_count = content.count("\n") + 1

    logger.info(
        f"Loaded context from {path}: {size_bytes:,} bytes ({size_mb:.2f} MB), "
        f"{line_count:,} lines",
    )

    return content


def load_multiple_contexts(
    file_paths: list[str | Path],
    separator: str = "\n\n",
    encoding: str = "utf-8",
    verbose: bool = False,
) -> str:
    """Load and concatenate multiple context files.

    Args:
        file_paths: List of paths to context files.
        separator: String to use between concatenated files.
        encoding: File encoding (default: utf-8).
        verbose: Enable verbose logging.

    Returns:
        Concatenated content of all files.

    Raises:
        ConfigurationError: If any file cannot be read.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    contents = []
    total_size = 0

    for file_path in file_paths:
        content = load_context(file_path, encoding=encoding, verbose=False)
        contents.append(content)
        total_size += len(content.encode(encoding))

    # Join contents
    combined = separator.join(contents)

    logger.info(
        f"Loaded {len(file_paths)} context files, "
        f"total size: {total_size:,} bytes ({total_size / (1024 * 1024):.2f} MB)",
    )

    return combined


def estimate_tokens(
    text: str,
    model_encoding: str = "cl100k_base",
) -> int:
    """Estimate the number of tokens in a text.

    Args:
        text: Text to estimate tokens for.
        model_encoding: Tiktoken encoding to use.

    Returns:
        Estimated number of tokens.
    """
    try:
        encoder = tiktoken.get_encoding(model_encoding)
        tokens = encoder.encode(text, disallowed_special=())
        return len(tokens)
    except (ValueError, KeyError) as e:
        logger.warning(f"Failed to estimate tokens with tiktoken: {e}")
        # Fallback: rough estimate of 1 token per 4 characters
        return len(text) // 4


def load_context_with_limit(
    file_path: str | Path,
    out_ctx: int,
    encoding: str = "utf-8",
    model_encoding: str = "cl100k_base",
    verbose: bool = False,
) -> tuple[str, int, bool]:
    """Load context with a token limit.

    Args:
        file_path: Path to the context file.
        out_ctx: Maximum number of tokens to load.
        encoding: File encoding (default: utf-8).
        model_encoding: Tiktoken encoding for token counting.
        verbose: Enable verbose logging.

    Returns:
        Tuple of (content, actual_tokens, was_truncated).

    Raises:
        ConfigurationError: If the file cannot be read.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    # Load full content
    content = load_context(file_path, encoding=encoding, verbose=False)

    # Estimate tokens
    total_tokens = estimate_tokens(content, model_encoding)

    if total_tokens <= out_ctx:
        logger.info(f"Context fits within limit: {total_tokens} tokens <= {out_ctx} tokens")
        return content, total_tokens, False

    # Need to truncate
    logger.warning(
        f"Context exceeds limit: {total_tokens} tokens > {out_ctx} tokens, truncating",
    )

    # Binary search to find the right truncation point
    encoder = tiktoken.get_encoding(model_encoding)
    tokens = encoder.encode(content, disallowed_special=())

    # Truncate tokens and decode
    truncated_tokens = tokens[:out_ctx]
    truncated_content = encoder.decode(truncated_tokens)

    logger.info(f"Truncated context from {total_tokens} to {out_ctx} tokens")

    return truncated_content, out_ctx, True


def save_context(
    content: str,
    file_path: str | Path,
    encoding: str = "utf-8",
) -> None:
    """Save context to a file.

    Args:
        content: Content to save.
        file_path: Path where to save the file.
        encoding: File encoding (default: utf-8).
    """
    path = Path(file_path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write content
    path.write_text(content, encoding=encoding)

    size_bytes = len(content.encode(encoding))
    logger.info(f"Saved context to {path}: {size_bytes:,} bytes")
