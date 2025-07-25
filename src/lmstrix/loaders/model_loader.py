# this_file: src/lmstrix/loaders/model_loader.py
"""Model loading and scanning functionality."""

from pathlib import Path

from loguru import logger

from lmstrix.api.client import LMStudioClient
from lmstrix.core.models import Model, ModelRegistry
from lmstrix.utils.paths import get_default_models_file


def load_model_registry(
    json_path: Path | None = None,
    verbose: bool = False,
) -> ModelRegistry:
    """Load the model registry from a JSON file.

    Args:
        json_path: Path to the JSON file. If None, uses the default location.
        verbose: Enable verbose logging.

    Returns:
        A ModelRegistry instance.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    registry_path = json_path or get_default_models_file()

    if not registry_path.exists():
        logger.warning(f"Model registry not found at {registry_path}. Returning empty registry.")
        return ModelRegistry(models_file=registry_path)

    registry = ModelRegistry(models_file=registry_path)
    logger.info(f"Loaded {len(registry)} models from {registry_path}")
    return registry

def save_model_registry(
    registry: ModelRegistry,
    json_path: Path | None = None,
) -> Path:
    """Save a ModelRegistry to a JSON file.

    Args:
        registry: The ModelRegistry to save.
        json_path: Path to save to. If None, uses the registry's default path.

    Returns:
        The path where the registry was saved.
    """
    save_path = json_path or registry.models_file
    registry.save()
    return save_path

def scan_and_update_registry(verbose: bool = False) -> ModelRegistry:
    """Scan for downloaded LM Studio models and update the local registry.

    Args:
        verbose: Enable verbose logging.

    Returns:
        The updated ModelRegistry instance.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    client = LMStudioClient(verbose=verbose)
    registry = load_model_registry(verbose=verbose)

    logger.info("Scanning for LM Studio models...")
    try:
        discovered_models = client.list_models()
        discovered_ids = {model["id"] for model in discovered_models}
        logger.info(f"Found {len(discovered_models)} models in LM Studio.")
    except Exception as e:
        logger.error(f"Failed to scan for models: {e}")
        return registry

    # Update existing models and add new ones
    for model_data in discovered_models:
        model_id = model_data["id"]
        if registry.get_model(model_id):
            logger.debug(f"Updating existing model: {model_id}")
            # Update potentially changed data, but preserve test results
            existing_model = registry.get_model(model_id)
            if existing_model:
                existing_model.path = Path(model_data.get("path", existing_model.path))
                existing_model.size = model_data.get("size_bytes", existing_model.size)
        else:
            logger.info(f"Discovered new model: {model_id}")
            new_model = Model(
                id=model_id,
                path=Path(model_data.get("path", "")),
                size_bytes=model_data.get("size_bytes", 0),
                ctx_in=model_data.get("context_length", 8192),
            )
            registry.update_model(model_id, new_model)

    # Remove models that are no longer present
    registry_ids = set(model.id for model in registry.list_models())
    deleted_ids = registry_ids - discovered_ids
    for model_id in deleted_ids:
        logger.info(f"Removing deleted model: {model_id}")
        registry.remove_model(model_id)

    # Save the updated registry
    save_model_registry(registry)
    logger.info("Model registry updated successfully.")

    return registry
