"""Model definitions and registry for LMStrix."""

import json
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, ValidationError, field_validator

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

    @field_validator("context_limit")
    @classmethod
    def validate_context_limit(cls, v: Any) -> int:
        """Validate context limit is reasonable."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("Context limit must be a positive integer")
        if v > 10_000_000:  # 10M tokens seems unreasonable
            raise ValueError(f"Context limit {v} seems unreasonably large")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: Any) -> int:
        """Validate model size is reasonable."""
        if not isinstance(v, int) or v < 0:
            raise ValueError("Model size must be a non-negative integer")
        return v

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

    def validate_integrity(self) -> bool:
        """Validate model data integrity."""
        try:
            # Basic field validation
            if not self.id or not self.path:
                return False

            # Context limits should be reasonable
            if self.context_limit <= 0 or self.context_limit > 10_000_000:
                return False

            # Tested contexts should be <= declared context
            if self.tested_max_context and self.tested_max_context > self.context_limit * 2:
                return False

            # Size should be reasonable
            return not self.size < 0
        except Exception:
            return False


class ModelRegistryError(Exception):
    """Exception raised for model registry errors."""


class ModelRegistry:
    """Manages the collection of available models."""

    def __init__(self, models_file: Path | None = None) -> None:
        """Initialize the model registry."""
        self.models_file = models_file or get_default_models_file()
        self._models: dict[str, Model] = {}  # path -> Model mapping
        self.lms_path: Path | None = None
        self.load()

    def _create_backup(self) -> Path | None:
        """Create a backup of the current registry file."""
        if not self.models_file.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.models_file.with_suffix(f".backup_{timestamp}")

        try:
            shutil.copy2(self.models_file, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except OSError as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """Keep only the most recent N backup files."""
        backup_pattern = f"{self.models_file.stem}.backup_*"
        backup_files = list(self.models_file.parent.glob(backup_pattern))

        if len(backup_files) <= keep_count:
            return

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Remove old backups
        for old_backup in backup_files[keep_count:]:
            try:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
            except OSError as e:
                logger.warning(f"Failed to remove old backup {old_backup}: {e}")

    def _validate_registry_data(self, data: dict) -> dict:
        """Validate and sanitize registry data before use."""
        if not isinstance(data, dict):
            raise ModelRegistryError("Registry data must be a dictionary")

        # Ensure required structure
        if "llms" not in data:
            data["llms"] = {}

        if not isinstance(data["llms"], dict):
            raise ModelRegistryError("'llms' section must be a dictionary")

        # Validate each model entry
        valid_models = {}
        for model_key, model_info in data["llms"].items():
            try:
                if not isinstance(model_info, dict):
                    logger.warning(f"Skipping invalid model entry {model_key}: not a dictionary")
                    continue

                # Ensure model_info has an ID
                model_info["id"] = model_info.get("id", model_key)

                # Parse context test status
                if "context_test_status" in model_info:
                    try:
                        model_info["context_test_status"] = ContextTestStatus(
                            model_info["context_test_status"],
                        )
                    except ValueError:
                        logger.warning(
                            f"Invalid context_test_status for {model_key}, resetting to untested",
                        )
                        model_info["context_test_status"] = ContextTestStatus.UNTESTED

                # Parse datetime
                if model_info.get("context_test_date"):
                    try:
                        model_info["context_test_date"] = datetime.fromisoformat(
                            model_info["context_test_date"],
                        )
                    except ValueError:
                        logger.warning(f"Invalid date format for {model_key}, clearing date")
                        model_info["context_test_date"] = None

                # Validate with Pydantic
                model = Model(**model_info)

                # Additional integrity check
                if not model.validate_integrity():
                    logger.warning(f"Model {model_key} failed integrity check, skipping")
                    continue

                valid_models[model_key] = model_info

            except (TypeError, KeyError, ValidationError) as e:
                logger.warning(f"Skipping invalid model {model_key}: {e}")
                continue

        data["llms"] = valid_models
        return data

    def load(self) -> None:
        """Load models from the JSON file with validation and recovery."""
        if not self.models_file.exists():
            logger.warning(f"Models file {self.models_file} not found")
            return

        try:
            raw_data = json.loads(self.models_file.read_text())

            # Validate the data structure
            try:
                data = self._validate_registry_data(raw_data)
            except ModelRegistryError as e:
                logger.error(f"Registry data validation failed: {e}")
                self._attempt_recovery()
                return

            # Get LMS path from data if available
            if "path" in data:
                self.lms_path = Path(data["path"])

            models_data = data.get("llms", {})
            loaded_models = {}

            for model_key, model_info in models_data.items():
                try:
                    # Parse context test status
                    if "context_test_status" in model_info:
                        model_info["context_test_status"] = ContextTestStatus(
                            model_info["context_test_status"],
                        )

                    # Parse datetime
                    if model_info.get("context_test_date"):
                        if isinstance(model_info["context_test_date"], str):
                            model_info["context_test_date"] = datetime.fromisoformat(
                                model_info["context_test_date"],
                            )
                        # If it's already a datetime object, leave it as is

                    model = Model(**model_info)

                    # Validate model integrity
                    if not model.validate_integrity():
                        logger.warning(f"Model {model_key} failed integrity check, skipping")
                        continue

                    # Use path as the key instead of model_id
                    model_path = str(model.path)
                    loaded_models[model_path] = model

                except (TypeError, KeyError, ValidationError) as e:
                    logger.warning(f"Failed to load model {model_key}: {e}")
                    continue

            self._models = loaded_models
            logger.info(f"Read {len(self._models)} valid models from {self.models_file}")

            # If we skipped any models due to validation errors, save the cleaned registry
            if len(loaded_models) < len(models_data):
                logger.info("Saving cleaned registry after validation")
                self.save()

        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load models: {e}")
            self._attempt_recovery()

    def _attempt_recovery(self) -> None:
        """Attempt to recover from backup files."""
        logger.info("Attempting to recover from backup files...")

        backup_pattern = f"{self.models_file.stem}.backup_*"
        backup_files = list(self.models_file.parent.glob(backup_pattern))

        if not backup_files:
            logger.warning("No backup files found, starting with empty registry")
            return

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for backup_file in backup_files:
            try:
                logger.info(f"Trying to restore from {backup_file}")
                raw_data = json.loads(backup_file.read_text())
                self._validate_registry_data(raw_data)

                # If we get here, the backup is valid
                logger.info(f"Successfully restored from {backup_file}")

                # Create a new backup of the corrupted file
                if self.models_file.exists():
                    corrupted_backup = self.models_file.with_suffix(".corrupted")
                    shutil.copy2(self.models_file, corrupted_backup)
                    logger.info(f"Saved corrupted file as {corrupted_backup}")

                # Replace with good backup
                shutil.copy2(backup_file, self.models_file)

                # Reload from the recovered file
                self.load()
                return

            except Exception as e:
                logger.warning(f"Backup {backup_file} is also corrupted: {e}")
                continue

        logger.error("All backups are corrupted, starting with empty registry")

    def save(self) -> None:
        """Save models to the JSON file with validation and backup."""
        # Validate all models before saving
        invalid_models = []
        for model_path, model in self._models.items():
            if not model.validate_integrity():
                invalid_models.append(model_path)

        if invalid_models:
            logger.error(
                f"Cannot save registry: {len(invalid_models)} models failed integrity check",
            )
            for model_path in invalid_models:
                logger.error(f"  Invalid model: {model_path}")
            raise ModelRegistryError(f"Registry contains {len(invalid_models)} invalid models")

        # Create backup before saving
        backup_path = self._create_backup()

        try:
            # Sort models by path for consistent output
            sorted_models = dict(sorted(self._models.items()))

            data: dict[str, Any] = {
                "llms": {
                    model_path: model.to_registry_dict()
                    for model_path, model in sorted_models.items()
                },
            }

            # Add LMS path if available
            if self.lms_path:
                data["path"] = str(self.lms_path)

            # Validate the data we're about to save
            self._validate_registry_data(data)

            # Ensure directory exists
            self.models_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to a temporary file first, then rename for atomic write
            temp_file = self.models_file.with_suffix(self.models_file.suffix + ".tmp")
            try:
                json_str = json.dumps(data, indent=2, default=str)
                temp_file.write_text(json_str)

                # Validate the written file can be loaded back
                try:
                    json.loads(temp_file.read_text())
                except json.JSONDecodeError as e:
                    raise ModelRegistryError(f"Generated JSON is invalid: {e}")

                temp_file.rename(self.models_file)
                logger.info(f"Saved {len(self._models)} models to {self.models_file}")

                # Clean up old backups
                self._cleanup_old_backups()

            except OSError as e:
                logger.error(f"Failed to save model registry atomically: {e}")
                if temp_file.exists():
                    temp_file.unlink()  # Clean up temp file on error
                raise  # Re-raise the exception to indicate failure

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

            # If we have a backup and saving failed, we might want to restore it
            if backup_path and backup_path.exists():
                logger.info("Save failed, backup is available for manual recovery")

            raise

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
        """Update a model in the registry with validation."""
        # Validate the model before updating
        if not model.validate_integrity():
            raise ModelRegistryError(f"Model {model_path} failed integrity check")

        self._models[model_path] = model
        self.save()

    def update_model_by_id(self, model: Model) -> None:
        """Update a model by ID with validation."""
        # Validate the model before updating
        if not model.validate_integrity():
            raise ModelRegistryError(f"Model {model.id} failed integrity check")

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
    def models(self) -> dict[str, Model]:
        """Public property for internal model mapping (path -> Model)."""
        return self._models
