"""Model definitions and registry for LMStrix."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, field_validator

from lmstrix.utils.paths import get_default_models_file


class ContextTestStatus(str, Enum):
    """Status of context testing for a model."""

    UNTESTED = "untested"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class Model(BaseModel):
    """Represents a model in the registry."""

    id: str  # Unique identifier, the model's relative path
    short_id: str | None = Field(
        default=None,
        description="Short identifier, path without file extension",
    )
    path: str  # Full absolute path to the model file or directory
    size: int = Field(..., description="Size of the model in bytes", alias="size_bytes")
    context_limit: int = Field(
        ...,
        description="Declared maximum context window size",
        alias="ctx_in",
    )
    context_out: int = Field(default=4096, description="Output context size", alias="ctx_out")
    supports_tools: bool = Field(
        default=False,
        description="Whether model supports tool use",
        alias="has_tools",
    )
    supports_vision: bool = Field(
        default=False,
        description="Whether model supports vision",
        alias="has_vision",
    )

    # Context testing fields
    tested_max_context: int | None = Field(
        default=None,
        description="Maximum context that produces correct output",
    )
    loadable_max_context: int | None = Field(
        default=None,
        description="Maximum context at which model loads successfully",
    )
    last_known_good_context: int | None = Field(
        default=None,
        description="Last confirmed working context size (for resuming tests)",
    )
    last_known_bad_context: int | None = Field(
        default=None,
        description="Last confirmed failing context size (for resuming tests)",
    )
    context_test_status: ContextTestStatus = Field(
        default=ContextTestStatus.UNTESTED,
        description="Status of context testing",
    )
    context_test_log: str | None = Field(default=None, description="Path to context test log file")
    context_test_date: datetime | None = Field(
        default=None,
        description="When context was last tested",
    )

    # Error tracking
    failed: bool = Field(default=False, description="Whether model failed to load")
    error_msg: str = Field(default="", description="Error message if failed")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True  # Allow both field names and aliases

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        """Ensure path is a Path object."""
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        return Path(str(v))

    def sanitized_path(self) -> str:
        """Return a sanitized version of the model path suitable for filenames."""
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return "".join(c if c in safe_chars else "_" for c in str(self.path))

    def sanitized_id(self) -> str:
        """Return a sanitized version of the model ID suitable for filenames."""
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return "".join(c if c in safe_chars else "_" for c in self.id)

    def get_short_id(self) -> str:
        """Get the short_id, computing it from path if not set."""
        if self.short_id:
            return self.short_id
        # Generate short_id from path: filename without extension
        path_obj = Path(self.path)
        return path_obj.stem if path_obj.name else self.id

    def to_registry_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for registry storage."""
        return {
            "id": self.id,
            "short_id": self.get_short_id(),  # Always save computed short_id
            "path": str(self.path),
            "size_bytes": self.size,
            "ctx_in": self.context_limit,
            "ctx_out": self.context_out,
            "has_tools": self.supports_tools,
            "has_vision": self.supports_vision,
            "tested_max_context": self.tested_max_context,
            "loadable_max_context": self.loadable_max_context,
            "last_known_good_context": self.last_known_good_context,
            "last_known_bad_context": self.last_known_bad_context,
            "context_test_status": self.context_test_status.value,
            "context_test_log": self.context_test_log,
            "context_test_date": (
                self.context_test_date.isoformat() if self.context_test_date else None
            ),
            "failed": self.failed,
            "error_msg": self.error_msg,
        }


class ModelRegistry:
    """Manages the collection of available models."""

    def __init__(self, models_file: Path | None = None) -> None:
        """Initialize the model registry."""
        self.models_file = models_file or get_default_models_file()
        self._models: dict[str, Model] = {}  # path -> Model mapping
        self.lms_path: Path | None = None
        self.load()

    def load(self) -> None:
        """Load models from the JSON file."""
        if not self.models_file.exists():
            logger.warning(f"Models file {self.models_file} not found")
            return

        try:
            data = json.loads(self.models_file.read_text())

            # Get LMS path from data if available
            if "path" in data:
                self.lms_path = Path(data["path"])

            models_data = data.get("llms", {})

            for model_key, model_info in models_data.items():
                try:
                    # Ensure model_info has an ID - use model_key as fallback
                    model_info["id"] = model_info.get("id", model_key)

                    # Parse context test status
                    if "context_test_status" in model_info:
                        model_info["context_test_status"] = ContextTestStatus(
                            model_info["context_test_status"],
                        )

                    # Parse datetime
                    if model_info.get("context_test_date"):
                        model_info["context_test_date"] = datetime.fromisoformat(
                            model_info["context_test_date"],
                        )

                    model = Model(**model_info)
                    # Use path as the key instead of model_id
                    model_path = str(model.path)
                    self._models[model_path] = model
                except Exception as e:
                    logger.error(f"Failed to load model {model_key}: {e}")

            logger.info(f"Read {len(self._models)} models from {self.models_file}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def save(self) -> None:
        """Save models to the JSON file."""
        # Sort models by path for consistent output
        sorted_models = dict(sorted(self._models.items()))

        data: dict[str, Any] = {
            "llms": {
                model_path: model.to_registry_dict() for model_path, model in sorted_models.items()
            },
        }

        # Add LMS path if available
        if self.lms_path:
            data["path"] = str(self.lms_path)

        # Ensure directory exists
        self.models_file.parent.mkdir(parents=True, exist_ok=True)

        # Write with nice formatting
        json_str = json.dumps(data, indent=2, default=str)
        self.models_file.write_text(json_str)

        logger.info(f"Saved {len(self._models)} models to {self.models_file}")

    def get_model(self, model_path: str) -> Model | None:
        """Get a model by its path."""
        return self._models.get(model_path)

    def find_model(self, identifier: str) -> Model | None:
        """Find a model by its full ID or short ID."""
        # First, try to find by full ID
        for model in self._models.values():
            if model.id == identifier:
                return model
        # If not found, search by short_id
        for model in self._models.values():
            if model.get_short_id() == identifier:
                return model
        return None

    def get_model_by_id(self, model_id: str) -> Model | None:
        """Get a model by ID (backward compatibility)."""
        for model in self._models.values():
            if model.id == model_id:
                return model
        return None

    def list_models(self) -> list[Model]:
        """Get all models in the registry."""
        return list(self._models.values())

    def update_model(self, model_path: str, model: Model) -> None:
        """Update a model in the registry and save."""
        self._models[model_path] = model
        self.save()

    def update_model_by_id(self, model_id: str, model: Model) -> None:
        """Update a model by ID (backward compatibility)."""
        # Find existing model by ID and update it
        model_path = str(model.path)
        self._models[model_path] = model
        self.save()

    def remove_model(self, model_path: str) -> None:
        """Remove a model from the registry and save."""
        if model_path in self._models:
            del self._models[model_path]
            self.save()

    def remove_model_by_id(self, model_id: str) -> None:
        """Remove a model by ID (backward compatibility)."""
        model = self.get_model_by_id(model_id)
        if model:
            model_path = str(model.path)
            if model_path in self._models:
                del self._models[model_path]
                self.save()

    def __len__(self) -> int:
        """Return the number of models in the registry."""
        return len(self._models)

    @property
    def models(self):
        """Public property for internal model mapping (path -> Model)."""
        return self._models
