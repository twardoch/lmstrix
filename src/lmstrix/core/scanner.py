"""Model scanning functionality for LM Studio."""

from pathlib import Path

from lmstrix.core.models import Model, ModelRegistry
from lmstrix.utils import get_lmstudio_path
from lmstrix.utils.logging import logger


class ModelScanner:
    """Scans LM Studio for available models."""

    def __init__(self) -> None:
        """Initialize scanner."""
        self.lms_path = get_lmstudio_path()
        self.models_dir = self.lms_path / "models"

    def _get_model_size(self, model_path: Path) -> int:
        """Get size of model file(s)."""
        if model_path.is_file():
            return model_path.stat().st_size
        if model_path.is_dir():
            # For directories (like MLX models), sum all files
            total = 0
            for file in model_path.rglob("*"):
                if file.is_file():
                    total += file.stat().st_size
            return total
        return 0

    def _extract_model_info(self, model_path: Path) -> dict | None:
        """Extract model information from path.

        Args:
            model_path: Path to model file or directory.

        Returns:
            Model info dict or None if not a valid model.
        """
        # Skip hidden files and non-model files
        if model_path.name.startswith("."):
            return None

        # Check if it's a model file or directory
        is_model = False

        # Common model file extensions
        model_extensions = {".gguf", ".ggml", ".bin"}
        if model_path.is_file() and model_path.suffix.lower() in model_extensions:
            is_model = True

        # MLX models are directories
        if model_path.is_dir() and (model_path / "config.json").exists():
            is_model = True

        if not is_model:
            return None

        # Create model ID from path
        # The model ID is the relative path from the LM Studio models directory.
        # This allows using the path directly to load the model in LM Studio.
        try:
            relative_path = model_path.relative_to(self.models_dir)
            model_id = str(relative_path).replace("\\", "/")
        except ValueError:
            # Model path is not inside models_dir (e.g., during testing)
            # Use the full path as the model ID
            model_id = str(model_path)

        # Create a short ID by removing the file extension
        model_path.stem if model_path.is_file() else model_path.name

        # Try to extract context info from filename or path
        # This is a heuristic - actual values come from model metadata
        ctx_in = 4096  # Default

        # Look for context indicators in path
        path_str = str(model_path).lower()
        if "128k" in path_str:
            ctx_in = 128 * 1024
        elif "64k" in path_str:
            ctx_in = 64 * 1024
        elif "32k" in path_str:
            ctx_in = 32 * 1024
        elif "16k" in path_str:
            ctx_in = 16 * 1024
        elif "8k" in path_str:
            ctx_in = 8 * 1024
        elif "1m" in path_str or "1048k" in path_str:
            ctx_in = 1024 * 1024

        return {
            "id": model_id,
            "path": str(model_path),
            "size_bytes": self._get_model_size(model_path),
            "ctx_in": ctx_in,
            "ctx_out": 4096,  # Default
            "has_tools": False,  # Would need to load model to determine
            "has_vision": "vision" in path_str or "vl" in path_str,  # Heuristic
        }

    def scan_models(self) -> dict[str, dict]:
        """Scan for all models in LM Studio.

        Returns:
            Dictionary of model_id -> model_info.
        """
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return {}

        logger.info(f"Scanning for models in {self.models_dir}")
        models = {}

        # Recursively find all potential model files
        for path in self.models_dir.rglob("*"):
            try:
                model_info = self._extract_model_info(path)
                if model_info:
                    models[model_info["id"]] = model_info
                    logger.debug(f"Found model: {model_info['id']}")
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Error scanning {path}: {e}")

        logger.info(f"Found {len(models)} models")
        return models

    def update_registry(self, registry: ModelRegistry | None = None) -> ModelRegistry:
        """Update model registry with scanned models.

        Args:
            registry: Existing registry to update. If None, creates new.

        Returns:
            Updated registry.
        """
        if registry is None:
            registry = ModelRegistry()

        # Get currently scanned models
        scanned_models = self.scan_models()

        # Get existing model IDs
        existing_ids = {model.id for model in registry.list_models()}
        scanned_ids = set(scanned_models.keys())

        # Remove models that no longer exist
        removed_ids = existing_ids - scanned_ids
        for model_id in removed_ids:
            logger.info(f"Removing non-existent model: {model_id}")
            registry.remove_model(model_id)

        # Add or update models
        new_ids = scanned_ids - existing_ids
        for model_id in new_ids:
            model_info = scanned_models[model_id]
            try:
                model = Model(**model_info)
                registry.update_model(model_id, model)
                logger.info(f"Added new model: {model_id}")
            except (TypeError, KeyError) as e:
                logger.error(f"Failed to add model {model_id}: {e}")

        # Update LMS path in registry
        registry.lms_path = self.lms_path

        # Save the updated registry
        registry.save()

        return registry

    def sync_with_registry(self, registry: ModelRegistry) -> tuple[list[str], list[str]]:
        """Sync scanned models with registry.

        Args:
            registry: Model registry to sync with.

        Returns:
            Tuple of (new_model_ids, removed_model_ids).
        """
        # Get currently scanned models
        scanned_models = self.scan_models()

        # Get existing model IDs
        existing_ids = {model.id for model in registry.list_models()}
        scanned_ids = set(scanned_models.keys())

        # Find differences
        new_ids = list(scanned_ids - existing_ids)
        removed_ids = list(existing_ids - scanned_ids)

        # Remove models that no longer exist
        for model_id in removed_ids:
            logger.info(f"Removing non-existent model: {model_id}")
            registry.remove_model(model_id)

        # Add new models
        for model_id in new_ids:
            model_info = scanned_models[model_id]
            try:
                model = Model(**model_info)
                registry.update_model(model_id, model)
                logger.info(f"Added new model: {model_id}")
            except (TypeError, KeyError) as e:
                logger.error(f"Failed to add model {model_id}: {e}")

        # Save the updated registry
        registry.save()

        return new_ids, removed_ids
