# this_file: src/lmstrix/core/models.py
"""Model definitions and registry for LMStrix."""

import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field, field_validator


class Model(BaseModel):
    """Represents a single LM Studio model with its metadata."""

    id: str = Field(..., description="Unique identifier for the model")
    path: Path = Field(..., description="Path to the model file")
    size: int = Field(..., description="Size of the model in bytes")
    context_limit: int = Field(..., description="Maximum context window size")
    supports_tools: bool = Field(
        default=False, description="Whether model supports tool use"
    )
    supports_vision: bool = Field(
        default=False, description="Whether model supports vision"
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        """Ensure path is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v

    def sanitized_id(self) -> str:
        """Return a sanitized version of the model ID suitable for filenames."""
        safe_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        )
        return "".join(c if c in safe_chars else "_" for c in self.id)


class ModelRegistry:
    """Manages the collection of available models."""

    def __init__(self, models_file: Optional[Path] = None):
        """Initialize the model registry."""
        self.models_file = (
            models_file or Path(__file__).parent.parent.parent / "lmsm.json"
        )
        self._models: dict[str, Model] = {}
        self.load()

    def load(self) -> None:
        """Load models from the JSON file."""
        if not self.models_file.exists():
            logger.warning(f"Models file {self.models_file} not found")
            return

        try:
            data = json.loads(self.models_file.read_text())
            models_data = data.get("llms", {})

            for model_id, model_info in models_data.items():
                mapped_data = {
                    "id": model_info.get("id", model_id),
                    "path": model_info.get("path", ""),
                    "size": model_info.get("size_bytes", 0),
                    "context_limit": model_info.get("ctx_in", 0),
                    "supports_tools": model_info.get("has_tools", False),
                    "supports_vision": model_info.get("has_vision", False),
                }
                self._models[model_id] = Model.from_dict(mapped_data)

            logger.info(f"Loaded {len(self._models)} models")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        return self._models.get(model_id)

    def list_models(self) -> list[Model]:
        """Get all models in the registry."""
        return list(self._models.values())

    def __len__(self) -> int:
        """Return the number of models in the registry."""
        return len(self._models)
