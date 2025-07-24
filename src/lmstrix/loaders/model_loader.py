# this_file: src/lmstrix/loaders/model_loader.py
"""Model loading functionality."""

from pathlib import Path
from typing import Optional

from loguru import logger

from lmstrix.core.models import ModelRegistry


def load_model_registry(
    json_path: Optional[Path] = None,
    verbose: bool = False,
) -> ModelRegistry:
    """Load models from a JSON file into a ModelRegistry.

    Args:
        json_path: Path to the JSON file. If None, uses default location.
        verbose: Enable verbose logging.

    Returns:
        ModelRegistry instance with loaded models.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    # Use default path if not provided
    if json_path is None:
        # Look in common locations
        candidates = [
            Path("lmsm.json"),
            Path(__file__).parent.parent.parent.parent / "lmsm.json",
            Path.home() / ".lmstrix" / "lmsm.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                json_path = candidate
                logger.info(f"Found model registry at {json_path}")
                break
        else:
            logger.warning("No model registry file found in default locations")
            return ModelRegistry()

    # Create and return registry
    registry = ModelRegistry(models_file=json_path)
    logger.info(f"Loaded {len(registry)} models from {json_path}")

    return registry


def save_model_registry(
    registry: ModelRegistry,
    json_path: Optional[Path] = None,
) -> Path:
    """Save a ModelRegistry to a JSON file.

    Args:
        registry: ModelRegistry to save.
        json_path: Path to save to. If None, uses registry's default path.

    Returns:
        Path where the registry was saved.
    """
    if json_path:
        registry.models_file = json_path

    registry.save()
    return registry.models_file
