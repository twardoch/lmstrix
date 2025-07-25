"""Model loading and scanning functionality."""

from pathlib import Path

from loguru import logger

from lmstrix.api.client import LMStudioClient
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
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
    logger.info(f"Read {len(registry)} models from {registry_path}")
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


def scan_and_update_registry(
    rescan_failed: bool = False,
    rescan_all: bool = False,
    verbose: bool = False,
) -> ModelRegistry:
    """Scan for downloaded LM Studio models and update the local registry.

    Args:
        rescan_failed: Only re-scan models that previously failed.
        rescan_all: Re-scan all models (clear existing test data).
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
        logger.info(f"Found {len(discovered_models)} models in LM Studio.")
    except Exception as e:
        logger.error(f"Failed to scan for models: {e}")
        return registry

    # Update existing models and add new ones
    for model_data in discovered_models:
        model_id = model_data["id"]
        model_path = str(Path(model_data.get("path", "")))
        existing_model = registry.get_model(model_path)

        if existing_model:
            logger.debug(f"Updating existing model: {model_path}")
            # Update potentially changed data
            existing_model.id = model_id  # Update ID in case it changed
            existing_model.path = model_path  # Ensure path is consistent
            existing_model.size = model_data.get("size_bytes", existing_model.size)
            existing_model.context_limit = model_data.get(
                "context_length",
                existing_model.context_limit,
            )
            existing_model.supports_tools = model_data.get(
                "has_tools",
                existing_model.supports_tools,
            )
            existing_model.supports_vision = model_data.get(
                "has_vision",
                existing_model.supports_vision,
            )

            # Handle rescan options
            if rescan_all:
                # Clear all test data
                logger.info(f"Clearing test data for {model_path} (--all flag)")
                existing_model.tested_max_context = None
                existing_model.loadable_max_context = None
                existing_model.context_test_status = ContextTestStatus.UNTESTED
                existing_model.context_test_log = None
                existing_model.context_test_date = None
            elif rescan_failed and existing_model.context_test_status == ContextTestStatus.FAILED:
                # Clear test data only for failed models
                logger.info(f"Clearing test data for failed model {model_path} (--failed flag)")
                existing_model.tested_max_context = None
                existing_model.loadable_max_context = None
                existing_model.context_test_status = ContextTestStatus.UNTESTED
                existing_model.context_test_log = None
                existing_model.context_test_date = None

            # Update the model in the registry using the correct path
            registry.update_model(model_path, existing_model)
        else:
            logger.info(f"Discovered new model: {model_path}")
            model_file_path = Path(model_data.get("path", ""))
            # Generate short_id: filename without extension
            short_id = model_file_path.stem if model_file_path.name else model_id
            new_model = Model(
                id=model_id,
                short_id=short_id,
                path=model_path,
                size_bytes=model_data.get("size_bytes", 0),
                ctx_in=model_data.get("context_length", 8192),
                ctx_out=4096,  # Default output context
                has_tools=model_data.get("has_tools", False),
                has_vision=model_data.get("has_vision", False),
            )
            registry.update_model(model_path, new_model)

    # Remove models that are no longer present
    registry_paths = {str(model.path) for model in registry.list_models()}
    discovered_paths = {str(Path(model["path"])) for model in discovered_models}

    deleted_paths = registry_paths - discovered_paths
    for model_path in deleted_paths:
        logger.info(f"Removing deleted model: {model_path}")
        registry.remove_model(model_path)

    # Save the updated registry
    save_model_registry(registry)
    logger.info("Model registry updated successfully.")

    return registry
