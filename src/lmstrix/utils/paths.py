"""Path utilities for LMStrix."""

from pathlib import Path

from lmstrix.api.exceptions import LMStudioInstallationNotFoundError
from lmstrix.utils.logging import logger


def get_lmstudio_path() -> Path:
    """Get the LM Studio installation path.

    Returns:
        Path to LM Studio directory.

    Raises:
        LMStudioInstallationNotFoundError: If LM Studio path cannot be determined.
    """
    # Check for .lmstudio-home-pointer file
    home_pointer = Path.home() / ".lmstudio-home-pointer"

    if home_pointer.exists():
        try:
            lms_path = Path(home_pointer.read_text().strip().splitlines()[0])
            if lms_path.exists():
                logger.debug(f"Found LM Studio at {lms_path}")
                return lms_path
        except (OSError, IndexError) as e:
            logger.warning(f"Error reading home pointer: {e}")

    # Fallback to common locations
    common_paths = [
        Path.home() / ".cache" / "lm-studio",
        Path("/Users/Shared/lmstudio"),
        Path.home() / "Library" / "Application Support" / "LM Studio",
    ]

    for path in common_paths:
        if path.exists() and (path / "models").exists():
            logger.debug(f"Found LM Studio at {path}")
            return path

    raise LMStudioInstallationNotFoundError


def get_lmstrix_data_dir() -> Path:
    """Get the LMStrix data directory within LM Studio.

    Creates the directory if it doesn't exist.

    Returns:
        Path to LMStrix data directory.
    """
    lms_path = get_lmstudio_path()
    data_dir = lms_path / "lmstrix"

    if not data_dir.exists():
        logger.info(f"Creating LMStrix data directory at {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def get_default_models_file() -> Path:
    """Get the path to the lmstrix.json registry file.

    The file is stored directly in the LM Studio data directory.

    Returns:
        Path to the lmstrix.json file.
    """
    lms_path = get_lmstudio_path()
    return lms_path / "lmstrix.json"


def get_context_tests_dir() -> Path:
    """Get the directory for context test logs.

    Creates the directory if it doesn't exist.

    Returns:
        Path to context tests directory.
    """
    tests_dir = get_lmstrix_data_dir() / "context_tests"

    if not tests_dir.exists():
        logger.info(f"Creating context tests directory at {tests_dir}")
        tests_dir.mkdir(parents=True, exist_ok=True)

    return tests_dir


def get_context_test_log_path(model_id: str) -> Path:
    """Get the path for a specific model's context test log.

    Args:
        model_id: The model identifier.

    Returns:
        Path to the log file.
    """
    # Sanitize model ID for filename
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_id)
    return get_context_tests_dir() / f"{safe_id}_context_test.log"


def get_prompts_dir() -> Path:
    """Get the directory for prompts.

    Creates the directory if it doesn't exist.

    Returns:
        Path to prompts directory.
    """
    prompts_dir = get_lmstrix_data_dir() / "prompts"

    if not prompts_dir.exists():
        logger.info(f"Creating prompts directory at {prompts_dir}")
        prompts_dir.mkdir(parents=True, exist_ok=True)

    return prompts_dir


def get_contexts_dir() -> Path:
    """Get the directory for contexts.

    Creates the directory if it doesn't exist.

    Returns:
        Path to contexts directory.
    """
    contexts_dir = get_lmstrix_data_dir() / "contexts"

    if not contexts_dir.exists():
        logger.info(f"Creating contexts directory at {contexts_dir}")
        contexts_dir.mkdir(parents=True, exist_ok=True)

    return contexts_dir


def get_lmstrix_log_path() -> Path:
    """Get the path to the lmstrix.log.txt file.

    Returns:
        Path to the lmstrix.log.txt file in the LMStudio folder.
    """
    lms_path = get_lmstudio_path()
    return lms_path / "lmstrix.log.txt"
