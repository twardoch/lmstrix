# this_file: src/lmstrix/utils/paths.py
"""Path utilities for LMStrix."""

from pathlib import Path

from loguru import logger


def get_lmstudio_path() -> Path:
    """Get the LM Studio installation path.

    Returns:
        Path to LM Studio directory.

    Raises:
        RuntimeError: If LM Studio path cannot be determined.
    """
    # Check for .lmstudio-home-pointer file
    home_pointer = Path.home() / ".lmstudio-home-pointer"

    if home_pointer.exists():
        try:
            lms_path = Path(home_pointer.read_text().strip().splitlines()[0])
            if lms_path.exists():
                logger.debug(f"Found LM Studio at {lms_path}")
                return lms_path
        except Exception as e:
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

    raise RuntimeError(
        "Could not find LM Studio installation. "
        "Please ensure LM Studio is installed and has been run at least once."
    )


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


def get_models_registry_path() -> Path:
    """Get the path to the models registry JSON file.

    Returns:
        Path to models.json file.
    """
    # First check for existing lmsm.json in LM Studio root
    lms_path = get_lmstudio_path()
    legacy_path = lms_path / "lmsm.json"

    if legacy_path.exists():
        logger.info(f"Using existing registry at {legacy_path}")
        return legacy_path

    # Otherwise use new location
    return get_lmstrix_data_dir() / "models.json"


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
