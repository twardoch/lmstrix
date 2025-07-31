"""Concrete config manager for LM Studio model configurations."""

# this_file: src/lmstrix/core/concrete_config.py

import json
from pathlib import Path
from typing import Any

from lmstrix.core.models import Model
from lmstrix.utils.logging import logger


class ConcreteConfigManager:
    """Manages LM Studio concrete model configurations."""

    def __init__(self, lms_path: Path) -> None:
        """Initialize the concrete config manager.

        Args:
            lms_path: Path to the LM Studio directory
        """
        self.lms_path = lms_path
        self.config_dir = lms_path / ".internal" / "user-concrete-model-default-config"

    def _get_config_path(self, model: Model) -> Path:
        """Get the path for a model's concrete config file.

        Args:
            model: The model object

        Returns:
            Path to the concrete config JSON file
        """
        # Model path is like "google/gemma-3n-e4b" for MLX
        # or "vendor/model-folder/model.gguf" for GGUF
        model_path = model.path

        # Convert path to string if it's a Path object
        if isinstance(model_path, Path):
            model_path = str(model_path)

        # Add .json extension
        return self.config_dir / f"{model_path}.json"

    def _create_skeleton_config(self) -> dict[str, Any]:
        """Create the skeleton structure for a concrete config.

        Returns:
            The skeleton config dict
        """
        return {"preset": "", "operation": {"fields": []}, "load": {"fields": []}}

    def _update_field(self, fields: list[dict[str, Any]], key: str, value: Any) -> None:
        """Update or add a field in the fields list.

        Args:
            fields: The fields list to update
            key: The field key to update
            value: The new value
        """
        # Check if field exists
        for field in fields:
            if field.get("key") == key:
                field["value"] = value
                return

        # Field doesn't exist, add it
        fields.append({"key": key, "value": value})

    def save_model_config(self, model: Model, enable_flash: bool = False) -> bool:
        """Save a model's tested context limit to its concrete config.

        Args:
            model: The model to save config for
            enable_flash: Whether to enable flash attention for GGUF models

        Returns:
            True if successful, False otherwise
        """
        if not model.tested_max_context:
            logger.debug(f"Model {model.id} has no tested_max_context, skipping")
            return False

        config_path = self._get_config_path(model)

        # Read existing config or create skeleton
        if config_path.exists():
            try:
                with config_path.open("r") as f:
                    config = json.load(f)
                logger.debug(f"Loaded existing config from {config_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to read existing config {config_path}: {e}")
                config = self._create_skeleton_config()
        else:
            config = self._create_skeleton_config()

        # Ensure structure exists
        if "load" not in config:
            config["load"] = {"fields": []}
        if "fields" not in config["load"]:
            config["load"]["fields"] = []

        # Update context length
        self._update_field(
            config["load"]["fields"],
            "llm.load.contextLength",
            model.tested_max_context,
        )

        # Handle flash attention for GGUF models
        if enable_flash and str(model.path).endswith(".gguf"):
            self._update_field(config["load"]["fields"], "llm.load.llama.flashAttention", True)
            logger.info(f"Enabled flash attention for GGUF model {model.id}")

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the config
        try:
            with config_path.open("w") as f:
                json.dump(config, f, indent=2)
            logger.info(
                f"Saved concrete config for {model.id} with context {model.tested_max_context}",
            )
            return True
        except OSError as e:
            logger.error(f"Failed to save concrete config {config_path}: {e}")
            return False

    def save_all_configs(self, models: list[Model], enable_flash: bool = False) -> tuple[int, int]:
        """Save concrete configs for all models with tested contexts.

        Args:
            models: List of models to process
            enable_flash: Whether to enable flash attention for GGUF models

        Returns:
            Tuple of (successful_saves, failed_saves)
        """
        successful = 0
        failed = 0

        for model in models:
            if model.tested_max_context:
                if self.save_model_config(model, enable_flash):
                    successful += 1
                else:
                    failed += 1

        return successful, failed
