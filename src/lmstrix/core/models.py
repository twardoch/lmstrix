# this_file: src/lmstrix/core/models.py
"""Model definitions and registry for LMStrix."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, field_validator

from ..utils.paths import get_default_models_file


class ContextTestStatus(str, Enum):
    """Status of context testing for a model."""

    UNTESTED = "untested"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class Model(BaseModel):
    """Represents a single LM Studio model with its metadata."""

    id: str = Field(..., description="Unique identifier for the model")
    path: Path = Field(..., description="Path to the model file")
    size: int = Field(..., description="Size of the model in bytes", alias="size_bytes")
    context_limit: int = Field(
        ..., description="Declared maximum context window size", alias="ctx_in",
    )
    context_out: int = Field(default=4096, description="Output context size", alias="ctx_out")
    supports_tools: bool = Field(
        default=False, description="Whether model supports tool use", alias="has_tools",
    )
    supports_vision: bool = Field(
        default=False, description="Whether model supports vision", alias="has_vision",
    )

    # Context testing fields
    tested_max_context: int | None = Field(
        default=None, description="Maximum context that produces correct output",
    )
    loadable_max_context: int | None = Field(
        default=None, description="Maximum context at which model loads successfully",
    )
    context_test_status: ContextTestStatus = Field(
        default=ContextTestStatus.UNTESTED, description="Status of context testing",
    )
    context_test_log: str | None = Field(default=None, description="Path to context test log file")
    context_test_date: datetime | None = Field(
        default=None, description="When context was last tested",
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

    def sanitized_id(self) -> str:
        """Return a sanitized version of the model ID suitable for filenames."""
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return "".join(c if c in safe_chars else "_" for c in self.id)

    def to_registry_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for registry storage."""
        return {
            "id": self.id,
            "path": str(self.path),
            "size_bytes": self.size,
            "ctx_in": self.context_limit,
            "ctx_out": self.context_out,
            "has_tools": self.supports_tools,
            "has_vision": self.supports_vision,
            "tested_max_context": self.tested_max_context,
            "loadable_max_context": self.loadable_max_context,
            "context_test_status": self.context_test_status.value,
            "context_test_log": self.context_test_log,
            "context_test_date": self.context_test_date.isoformat()
            if self.context_test_date
            else None,
            "failed": self.failed,
            "error_msg": self.error_msg,
        }


class ModelRegistry:
    """Manages the collection of available models."""

    def __init__(self, models_file: Path | None = None):
        """Initialize the model registry."""
        self.models_file = models_file or get_default_models_file()
        self._models: dict[str, Model] = {}
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

            for model_id, model_info in models_data.items():
                try:
                    # Ensure model_info has an ID
                    model_info["id"] = model_info.get("id", model_id)

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
                    self._models[model_id] = model
                except Exception as e:
                    logger.error(f"Failed to load model {model_id}: {e}")

            logger.info(f"Loaded {len(self._models)} models from {self.models_file}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def save(self) -> None:
        """Save models to the JSON file."""
        # Sort models by ID for consistent output
        sorted_models = dict(sorted(self._models.items()))

        data: dict[str, Any] = {
            "llms": {
                model_id: model.to_registry_dict() for model_id, model in sorted_models.items()
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

    def get_model(self, model_id: str) -> Model | None:
        """Get a model by ID."""
        return self._models.get(model_id)

    def list_models(self) -> list[Model]:
        """Get all models in the registry."""
        return list(self._models.values())

    def update_model(self, model_id: str, model: Model) -> None:
        """Update a model in the registry and save."""
        self._models[model_id] = model
        self.save()

    def remove_model(self, model_id: str) -> None:
        """Remove a model from the registry and save."""
        if model_id in self._models:
            del self._models[model_id]
            self.save()

    def __len__(self) -> int:
        """Return the number of models in the registry."""
        return len(self._models)
