"""Tests for core models and registry."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry


class TestContextTestStatus:
    """Test ContextTestStatus enum."""

    def test_enum_values(self: "TestContextTestStatus") -> None:
        """Test that all expected enum values exist."""
        assert ContextTestStatus.UNTESTED.value == "untested"
        assert ContextTestStatus.TESTING.value == "testing"
        assert ContextTestStatus.COMPLETED.value == "completed"
        assert ContextTestStatus.FAILED.value == "failed"


class TestModel:
    """Test Model class."""

    def test_model_creation_minimal(self: "TestModel", sample_model_data: dict[str, Any]) -> None:
        """Test creating a model with minimal required fields."""
        model = Model(**sample_model_data)

        assert model.id == "test-model"
        assert str(model.path) == "/path/to/test-model.gguf"
        assert model.size == 1500000
        assert model.context_limit == 4096
        assert model.context_out == 4096
        assert model.supports_tools is False
        assert model.supports_vision is False
        assert model.context_test_status == ContextTestStatus.UNTESTED
        assert model.tested_max_context is None
        assert model.loadable_max_context is None

    def test_model_creation_with_aliases(self: "TestModel") -> None:
        """Test model creation using field aliases."""
        data = {
            "id": "alias-test",
            "path": "/path/to/model.gguf",
            "size_bytes": 2000000,  # Using alias
            "ctx_in": 8192,  # Using alias
            "ctx_out": 4096,  # Using alias
            "has_tools": True,  # Using alias
            "has_vision": True,  # Using alias
        }
        model = Model(**data)

        assert model.size == 2000000
        assert model.context_limit == 8192
        assert model.context_out == 4096
        assert model.supports_tools is True
        assert model.supports_vision is True

    def test_model_with_context_testing(
        self: "TestModel",
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test model with context testing information."""
        sample_model_data.update(
            {
                "tested_max_context": 3500,
                "loadable_max_context": 4000,
                "context_test_status": ContextTestStatus.COMPLETED,
                "context_test_date": datetime.now(),
                "context_test_log": "/path/to/log.json",
            },
        )

        model = Model(**sample_model_data)

        assert model.tested_max_context == 3500
        assert model.loadable_max_context == 4000
        assert model.context_test_status == ContextTestStatus.COMPLETED
        assert model.context_test_date is not None
        assert model.context_test_log == "/path/to/log.json"

    def test_model_path_validation(self: "TestModel") -> None:
        """Test that path field accepts both string and Path objects."""
        data = {
            "id": "path-test",
            "path": "/string/path/model.gguf",
            "size_bytes": 1000000,
            "ctx_in": 4096,
        }
        model = Model(**data)
        assert isinstance(model.path, Path)
        assert str(model.path) == "/string/path/model.gguf"

        # Test with Path object
        data["path"] = Path("/path/object/model.gguf")
        model2 = Model(**data)
        assert isinstance(model2.path, Path)
        assert str(model2.path) == "/path/object/model.gguf"

    def test_model_sanitized_id(self: "TestModel") -> None:
        """Test sanitized_id method."""
        data = {
            "id": "test-model/with:special@chars!",
            "path": "/path/to/model.gguf",
            "size_bytes": 1000000,
            "ctx_in": 4096,
        }
        model = Model(**data)

        sanitized = model.sanitized_id()
        assert sanitized == "test-model_with_special_chars_"
        assert all(
            c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in sanitized
        )

    def test_model_to_registry_dict(self: "TestModel", sample_model_data: dict[str, Any]) -> None:
        """Test converting model to registry dictionary format."""
        test_date = datetime.now()
        sample_model_data.update(
            {
                "tested_max_context": 3000,
                "context_test_status": ContextTestStatus.COMPLETED,
                "context_test_date": test_date,
                "failed": True,
                "error_msg": "Test error",
            },
        )

        model = Model(**sample_model_data)
        registry_dict = model.to_registry_dict()

        assert registry_dict["id"] == "test-model"
        assert registry_dict["path"] == "/path/to/test-model.gguf"
        assert registry_dict["size_bytes"] == 1500000
        assert registry_dict["ctx_in"] == 4096
        assert registry_dict["ctx_out"] == 4096
        assert registry_dict["has_tools"] is False
        assert registry_dict["has_vision"] is False
        assert registry_dict["tested_max_context"] == 3000
        assert registry_dict["context_test_status"] == "completed"
        assert registry_dict["context_test_date"] == test_date.isoformat()
        assert registry_dict["failed"] is True
        assert registry_dict["error_msg"] == "Test error"

    def test_model_validation_error(self: "TestModel") -> None:
        """Test that model validation raises appropriate errors."""
        with pytest.raises(TypeError):
            Model(id="test")  # Missing required fields


class TestModelRegistry:
    """Test ModelRegistry class."""

    def test_registry_initialization(self: "TestModelRegistry", tmp_registry_file: Path) -> None:
        """Test registry initialization with custom file path."""
        registry = ModelRegistry(tmp_registry_file)

        assert registry.models_file == tmp_registry_file
        assert len(registry) == 0
        assert registry.lms_path is None

    def test_registry_save_and_load(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test saving and loading models."""
        # Create and save models
        registry = ModelRegistry(tmp_registry_file)
        registry.lms_path = Path("/path/to/lms")

        model1 = Model(**sample_model_data)
        model2_data = sample_model_data.copy()
        model2_data.update({"id": "test-model-2", "size_bytes": 2000000})
        model2 = Model(**model2_data)

        registry.update_model("test-model", model1)
        registry.update_model("test-model-2", model2)

        # Verify file was created
        assert tmp_registry_file.exists()

        # Load in new registry instance
        new_registry = ModelRegistry(tmp_registry_file)

        assert len(new_registry) == 2
        assert new_registry.lms_path == Path("/path/to/lms")

        loaded_model1 = new_registry.get_model("test-model")
        assert loaded_model1 is not None
        assert loaded_model1.id == "test-model"
        assert loaded_model1.size == 1500000

    def test_registry_get_model(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test getting a model by ID."""
        registry = ModelRegistry(tmp_registry_file)
        model = Model(**sample_model_data)
        registry.update_model("test-model", model)

        retrieved = registry.get_model("test-model")
        assert retrieved is not None
        assert retrieved.id == "test-model"

        # Test non-existent model
        assert registry.get_model("non-existent") is None

    def test_registry_list_models(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test listing all models."""
        registry = ModelRegistry(tmp_registry_file)

        # Add multiple models
        for i in range(3):
            data = sample_model_data.copy()
            data["id"] = f"model-{i}"
            model = Model(**data)
            registry.update_model(f"model-{i}", model)

        models = registry.list_models()
        assert len(models) == 3
        assert all(isinstance(m, Model) for m in models)
        assert {m.id for m in models} == {"model-0", "model-1", "model-2"}

    def test_registry_remove_model(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test removing a model."""
        registry = ModelRegistry(tmp_registry_file)
        model = Model(**sample_model_data)
        registry.update_model("test-model", model)

        assert len(registry) == 1

        registry.remove_model("test-model")
        assert len(registry) == 0
        assert registry.get_model("test-model") is None

        # Test removing non-existent model (should not raise)
        registry.remove_model("non-existent")

    def test_registry_with_context_test_data(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test saving/loading models with context test information."""
        registry = ModelRegistry(tmp_registry_file)

        # Add model with context test data
        test_date = datetime.now()
        sample_model_data.update(
            {
                "tested_max_context": 3500,
                "context_test_status": ContextTestStatus.COMPLETED,
                "context_test_date": test_date,
            },
        )
        model = Model(**sample_model_data)
        registry.update_model("test-model", model)

        # Load in new registry
        new_registry = ModelRegistry(tmp_registry_file)
        loaded_model = new_registry.get_model("test-model")

        assert loaded_model is not None
        assert loaded_model.tested_max_context == 3500
        assert loaded_model.context_test_status == ContextTestStatus.COMPLETED
        assert loaded_model.context_test_date is not None

    def test_registry_json_format(
        self: "TestModelRegistry",
        tmp_registry_file: Path,
        sample_model_data: dict[str, Any],
    ) -> None:
        """Test that the saved JSON has the expected format."""
        registry = ModelRegistry(tmp_registry_file)
        registry.lms_path = Path("/lms/path")

        model = Model(**sample_model_data)
        registry.update_model("test-model", model)

        # Read and parse the JSON file
        data = json.loads(tmp_registry_file.read_text())

        assert "path" in data
        assert data["path"] == "/lms/path"
        assert "llms" in data
        assert "test-model" in data["llms"]

        model_data = data["llms"]["test-model"]
        assert model_data["id"] == "test-model"
        assert model_data["size_bytes"] == 1500000
