"""Model loading and scanning functionality."""

from pathlib import Path

from lmstrix.api.client import LMStudioClient
from lmstrix.api.exceptions import APIConnectionError
from lmstrix.core.models import (
    ContextTestStatus,
    Model,
    ModelRegistry,
    ModelRegistryError,
)
from lmstrix.utils.logging import logger
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

    try:
        registry.save()
        return save_path
    except ModelRegistryError as e:
        logger.error(f"Failed to save registry due to validation errors: {e}")
        raise


def _validate_discovered_model(model_data: dict) -> bool:
    """Validate that discovered model data is reasonable before processing."""
    try:
        # Check required fields
        if not model_data.get("id"):
            logger.warning("Model missing ID field")
            return False

        if not model_data.get("path"):
            logger.warning(f"Model {model_data['id']} missing path field")
            return False

        # Check for embedding models (they shouldn't be processed as LLMs)
        model_id = model_data["id"].lower()
        if "embedding" in model_id or "embed" in model_id:
            logger.info(f"Skipping embedding model: {model_data['id']}")
            return False

        # Validate context length
        context_length = model_data.get("context_length", 0)
        if context_length <= 0:
            logger.warning(f"Model {model_data['id']} has invalid context_length: {context_length}")
            return False

        if context_length > 10_000_000:  # 10M tokens seems unreasonable
            logger.warning(
                f"Model {model_data['id']} has suspiciously large context_length: {context_length}",
            )
            return False

        # Validate size
        size = model_data.get("size_bytes", 0)
        if size < 0:
            logger.warning(f"Model {model_data['id']} has negative size: {size}")
            return False

        return True

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Error validating model data: {e}")
        return False


def _update_existing_model(
    existing_model: Model,
    model_data: dict,
    rescan_all: bool,
    rescan_failed: bool,
) -> Model:
    """Update an existing model's data and handle rescan options."""
    logger.debug(f"Updating existing model: {existing_model.path}")

    # Only update fields if the new data is valid
    if model_data.get("id"):
        existing_model.id = model_data["id"]

    # Update size if provided and reasonable
    new_size = model_data.get("size_bytes")
    if new_size is not None and new_size >= 0:
        existing_model.size = new_size

    # Update context limit if provided and reasonable
    new_context = model_data.get("context_length")
    if new_context and new_context > 0 and new_context <= 10_000_000:
        existing_model.context_limit = new_context

    # Update capabilities
    if "has_tools" in model_data:
        existing_model.supports_tools = model_data["has_tools"]
    if "has_vision" in model_data:
        existing_model.supports_vision = model_data["has_vision"]

    if rescan_all:
        logger.info(f"Clearing test data for {existing_model.path} (--all flag)")
        existing_model.reset_test_data()
    elif rescan_failed and existing_model.context_test_status == ContextTestStatus.FAILED:
        logger.info(f"Clearing test data for failed model {existing_model.path} (--failed flag)")
        existing_model.reset_test_data()

    # Fix status for models where tested_max_context equals context_limit but status is still "testing"
    if (
        existing_model.tested_max_context is not None
        and existing_model.tested_max_context == existing_model.context_limit
        and existing_model.context_test_status == ContextTestStatus.TESTING
    ):
        logger.info(
            f"Fixing status for {existing_model.path}: tested_max_context equals context_limit, changing status from 'testing' to 'completed'",
        )
        existing_model.context_test_status = ContextTestStatus.COMPLETED

    return existing_model


def _add_new_model(model_data: dict) -> Model | None:
    """Create a new model entry from discovered data."""
    try:
        model_path = Path(model_data.get("path", ""))
        logger.info(f"Discovered new model: {model_path}")
        short_id = model_path.stem if model_path.name else model_data["id"]

        new_model = Model(
            id=model_data["id"],
            short_id=short_id,
            path=str(model_path),
            size_bytes=model_data.get("size_bytes", 0),
            ctx_in=model_data.get("context_length", 8192),
            ctx_out=4096,
            has_tools=model_data.get("has_tools", False),
            has_vision=model_data.get("has_vision", False),
        )

        # Validate the new model
        if not new_model.validate_integrity():
            logger.warning(f"New model {model_data['id']} failed integrity check")
            return None

        return new_model

    except (KeyError, ValueError, TypeError, ModelRegistryError) as e:
        logger.error(f"Failed to create model from data {model_data.get('id', 'unknown')}: {e}")
        return None


def _remove_deleted_models(registry: ModelRegistry, discovered_models: list[dict]) -> None:
    """Remove models from the registry that are no longer discovered."""
    registry_paths = {str(model.path) for model in registry.list_models()}
    discovered_paths = {
        str(Path(model["path"])) for model in discovered_models if model.get("path")
    }
    deleted_paths = registry_paths - discovered_paths

    for model_path in deleted_paths:
        logger.info(f"Removing deleted model: {model_path}")
        registry.remove_model(model_path)


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

    Raises:
        ModelRegistryError: If the registry becomes corrupted during the operation.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    client = LMStudioClient(verbose=verbose)
    registry = load_model_registry(verbose=verbose)

    # Keep track of the original registry size for validation
    original_model_count = len(registry)

    logger.info("Scanning for LM Studio models...")
    try:
        discovered_models = client.list_models()
        logger.info(f"Found {len(discovered_models)} models in LM Studio.")
    except APIConnectionError as e:
        logger.error(f"Failed to scan for models: {e}")
        return registry

    # Filter and validate discovered models before processing
    valid_discovered_models = []
    for model_data in discovered_models:
        if _validate_discovered_model(model_data):
            valid_discovered_models.append(model_data)
        else:
            logger.debug(f"Skipping invalid/incompatible model: {model_data.get('id', 'unknown')}")

    logger.info(
        f"Processing {len(valid_discovered_models)} valid models (filtered from {len(discovered_models)})",
    )

    # Track updates for validation
    updates_made = 0
    errors_encountered = 0

    for model_data in valid_discovered_models:
        try:
            model_path = str(Path(model_data.get("path", "")))
            existing_model = registry.get_model(model_path)

            if existing_model:
                updated_model = _update_existing_model(
                    existing_model,
                    model_data,
                    rescan_all,
                    rescan_failed,
                )

                # Update the model in registry using model path as key (preserving original structure)
                registry.update_model(model_path, updated_model)
                updates_made += 1
            else:
                new_model = _add_new_model(model_data)
                if new_model:
                    registry.update_model(model_path, new_model)
                    updates_made += 1
                else:
                    errors_encountered += 1

        except (KeyError, ValueError, TypeError, ModelRegistryError) as e:
            logger.error(f"Error processing model {model_data.get('id', 'unknown')}: {e}")
            errors_encountered += 1
            continue

    # Only remove deleted models if we successfully processed the scan
    if errors_encountered == 0:
        _remove_deleted_models(registry, valid_discovered_models)
    else:
        logger.warning(
            f"Skipping deletion of models due to {errors_encountered} errors during scan",
        )

    # Final validation
    try:
        # Attempt to save to validate the registry
        save_model_registry(registry)
        logger.info(
            f"Model registry updated successfully. Original: {original_model_count}, Final: {len(registry)}, Updates: {updates_made}, Errors: {errors_encountered}",
        )
    except ModelRegistryError as e:
        logger.error(f"Registry validation failed after scan: {e}")
        logger.error("The registry may be in an inconsistent state. Please check backup files.")
        raise

    return registry


def reset_test_data(
    model_identifier: str,
    verbose: bool = False,
) -> bool:
    """Reset test data for a specific model.

    Args:
        model_identifier: Model ID or short ID to reset
        verbose: Enable verbose logging

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    try:
        registry = load_model_registry(verbose=verbose)
        model = registry.find_model(model_identifier)

        if not model:
            logger.error(f"Model '{model_identifier}' not found in registry")
            return False

        logger.info(f"Resetting test data for model: {model.id}")
        model.reset_test_data()

        # Validate before saving
        if not model.validate_integrity():
            logger.error(f"Model {model.id} failed integrity check after reset")
            return False

        registry.update_model(str(model.path), model)
        logger.info(f"Successfully reset test data for {model.id}")
        return True

    except (ModelRegistryError, ValueError) as e:
        logger.error(f"Failed to reset test data for {model_identifier}: {e}")
        return False
