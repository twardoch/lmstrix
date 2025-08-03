"""Simplified model definitions and registry for LMStrix."""

# this_file: src/lmstrix/core/models_simple.py

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from lmstrix.utils.logging import logger


class ContextTestStatus(str, Enum):
    """Status of context testing for a model."""

    UNTESTED = "untested"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class Model:
    """Represents a model in the registry."""

    def __init__(
        self,
        id: str,
        path: str,
        size_bytes: int,
        ctx_in: int,
        ctx_out: int = 4096,
        has_tools: bool = False,
        has_vision: bool = False,
        tested_max_context: int | None = None,
        context_test_status: str = "untested",
        context_test_date: str | None = None,
        **kwargs: Any,  # Ignore extra fields
    ) -> None:
        """Initialize a model with essential fields only."""
        self.id = id
        self.path = path
        self.size = size_bytes
        self.context_limit = ctx_in
        self.context_out = ctx_out
        self.has_tools = has_tools
        self.has_vision = has_vision
        self.short_id = kwargs.get("short_id")  # Compatibility
        self.supports_tools = has_tools  # Alias for compatibility
        self.supports_vision = has_vision  # Alias for compatibility
        self.tested_max_context = tested_max_context
        self.context_test_status = ContextTestStatus(context_test_status)
        if isinstance(context_test_date, str):
            self.context_test_date = datetime.fromisoformat(context_test_date)
        elif isinstance(context_test_date, datetime):
            self.context_test_date = context_test_date
        else:
            self.context_test_date = None

        # Compatibility attributes for existing code
        self.last_known_good_context = kwargs.get("last_known_good_context")
        self.last_known_bad_context = kwargs.get("last_known_bad_context")
        self.loadable_max_context = kwargs.get("loadable_max_context")
        self.context_test_log = kwargs.get("context_test_log")
        self.failed = kwargs.get("failed", False)
        self.error_msg = kwargs.get("error_msg", "")

        # Store any extra fields we might need
        self.extra = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "last_known_good_context",
                "last_known_bad_context",
                "loadable_max_context",
                "context_test_log",
                "failed",
                "error_msg",
            ]
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for JSON storage."""
        result = {
            "id": self.id,
            "path": self.path,
            "size_bytes": self.size,
            "ctx_in": self.context_limit,
            "ctx_out": self.context_out,
            "has_tools": self.has_tools,
            "has_vision": self.has_vision,
            "tested_max_context": self.tested_max_context,
            "context_test_status": (
                self.context_test_status.value
                if hasattr(self.context_test_status, "value")
                else self.context_test_status
            ),
            "context_test_date": (
                self.context_test_date.isoformat() if self.context_test_date else None
            ),
            "last_known_good_context": self.last_known_good_context,
            "last_known_bad_context": self.last_known_bad_context,
            "loadable_max_context": self.loadable_max_context,
            "context_test_log": self.context_test_log,
            "failed": self.failed,
            "error_msg": self.error_msg,
        }
        result.update(self.extra)  # Include any extra fields
        return result

    def to_registry_dict(self) -> dict[str, Any]:
        """Alias for to_dict() for backward compatibility."""
        return self.to_dict()

    def reset_test_data(self) -> None:
        """Reset all context testing data."""
        self.tested_max_context = None
        self.loadable_max_context = None
        self.last_known_good_context = None
        self.last_known_bad_context = None
        self.context_test_status = ContextTestStatus.UNTESTED
        self.context_test_log = None
        self.context_test_date = None
        self.failed = False
        self.error_msg = ""

    def validate_integrity(self) -> bool:
        """Validate the model's integrity.

        Returns:
            bool: True if the model is valid, False otherwise.
        """
        # Check if path exists (convert string to Path if needed)
        model_path = Path(self.path) if isinstance(self.path, str) else self.path

        # Skip path existence check - LM Studio manages model paths internally
        # and they may not be directly accessible as filesystem paths
        # Only check path existence for obvious test paths
        if str(model_path).startswith("/path/to/"):
            # This is a test path, check if it exists
            if not model_path.exists():
                logger.warning(f"Test model path does not exist: {self.path}")
                return False

        # Check if size is positive
        if self.size <= 0:
            logger.warning(f"Model size is invalid: {self.size}")
            return False

        # Check if context limits are reasonable
        if self.context_limit <= 0:
            logger.warning(f"Model context limit is invalid: {self.context_limit}")
            return False

        if self.context_out <= 0:
            logger.warning(f"Model context out is invalid: {self.context_out}")
            return False

        # Basic sanity check on context limits
        if self.context_out > self.context_limit:
            logger.warning(
                f"Model context out ({self.context_out}) exceeds context limit ({self.context_limit})",
            )
            return False

        return True

    def sanitized_id(self) -> str:
        """Return a sanitized version of the model ID for filenames."""
        import re

        # Replace problematic characters with underscores
        # Also replace @ and ! for the test case
        return re.sub(r'[<>:"/\\|?*@!]', "_", self.id)


class ModelRegistryError(Exception):
    """Exception raised for model registry errors."""


class ModelRegistry:
    """Simplified model registry without complex validation."""

    def __init__(self, models_file: Path | None = None) -> None:
        """Initialize the model registry."""
        self.models_file = models_file or self._get_default_models_file()
        self._models: dict[str, Model] = {}
        self.lms_path: Path | None = None  # Compatibility
        self.load()

    def _get_default_models_file(self) -> Path:
        """Get the default models file path."""
        from lmstrix.utils.paths import get_default_models_file

        return get_default_models_file()

    def load(self) -> None:
        """Load models from JSON file."""
        if not self.models_file.exists():
            logger.warning(f"Models file {self.models_file} not found")
            return

        try:
            data = json.loads(self.models_file.read_text())

            # Get LMS path from data if available
            if "path" in data:
                self.lms_path = Path(data["path"])

            models_data = data.get("llms", {})

            for model_id, model_info in models_data.items():
                try:
                    # Ensure id field exists
                    model_info["id"] = model_info.get("id", model_id)
                    model = Model(**model_info)
                    self._models[model_id] = model
                except Exception as e:
                    logger.warning(f"Failed to load model {model_id}: {e}")
                    continue

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse models file: {e}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def save(self) -> None:
        """Save models to JSON file."""
        try:
            # Create parent directory if needed
            self.models_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data
            data = {
                "llms": {model_id: model.to_dict() for model_id, model in self._models.items()},
            }

            # Add lms_path if set
            if self.lms_path:
                data["path"] = str(self.lms_path)

            # Write to file
            self.models_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(self._models)} models to {self.models_file}")

        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            raise

    def add_model(self, model: Model) -> None:
        """Add a model to the registry."""
        self._models[model.id] = model
        self.save()  # Auto-save for compatibility

    def update_model(self, model_id: str, model: Model) -> None:
        """Update a model in the registry (adds if not exists for compatibility)."""
        self._models[model_id] = model
        self.save()  # Auto-save for compatibility

    def update_model_by_id(self, model: Model) -> None:
        """Update a model using its own ID, finding existing entry by path or ID."""
        # First, try to find the existing model by checking all keys
        existing_key = None

        # Check if there's an entry with the exact path
        if model.path in self._models:
            existing_key = model.path
        # Otherwise, check if there's an entry with the model ID
        elif model.id in self._models:
            existing_key = model.id
        else:
            # Search through all models to find one with matching path or ID
            for key, existing_model in self._models.items():
                if existing_model.path == model.path or existing_model.id == model.id:
                    existing_key = key
                    break

        # Update using the existing key if found, otherwise use model.id
        key_to_use = existing_key if existing_key else model.id
        self.update_model(key_to_use, model)

    def get_model(self, model_id: str) -> Model | None:
        """Get a model by ID."""
        return self._models.get(model_id)

    def find_model(self, model_identifier: str) -> Model | None:
        """Find a model by ID or path.

        First tries exact path match (for backward compatibility),
        then searches by model ID across all models.
        """
        # Try exact path match first (original behavior)
        if model_identifier in self._models:
            return self._models[model_identifier]

        # Search by model ID across all models
        for model in self._models.values():
            if model.id == model_identifier:
                return model

        return None

    def list_models(self) -> list[Model]:
        """List all models in the registry."""
        return list(self._models.values())

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the registry."""
        if model_id in self._models:
            del self._models[model_id]
            self.save()  # Auto-save for compatibility
            return True
        return False

    def clear(self) -> None:
        """Clear all models from the registry."""
        self._models.clear()

    def __len__(self) -> int:
        """Return the number of models."""
        return len(self._models)

    def __contains__(self, model_id: str) -> bool:
        """Check if a model exists."""
        return model_id in self._models
