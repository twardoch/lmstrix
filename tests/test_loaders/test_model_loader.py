"""Tests for model loader functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

from lmstrix.core.models import Model, ModelRegistry
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)


class TestModelLoader:
    """Test model loading functions."""

    def test_load_model_registry_default_path(self: "TestModelLoader", tmp_path: Path) -> None:
        """Test loading registry with default path."""
        # Create a test registry file
        registry_file = tmp_path / "models_registry.json"
        test_data = {
            "path": "/path/to/lms",
            "llms": {
                "test-model": {
                    "id": "test-model",
                    "path": "/path/to/model.gguf",
                    "size_bytes": 1000000,
                    "ctx_in": 4096,
                    "ctx_out": 4096,
                    "has_tools": False,
                    "has_vision": False,
                },
            },
        }
        registry_file.write_text(json.dumps(test_data, indent=2))

        with patch("lmstrix.loaders.model_loader.get_default_models_file") as mock_get_path:
            mock_get_path.return_value = registry_file

            registry = load_model_registry(verbose=True)

            assert isinstance(registry, ModelRegistry)
            assert len(registry) == 1
            assert registry.get_model("test-model") is not None

    def test_load_model_registry_custom_path(self: "TestModelLoader", tmp_path: Path) -> None:
        """Test loading registry with custom path."""
        # Create a test registry file
        custom_file = tmp_path / "custom_models.json"
        test_data = {
            "llms": {
                "model1": {
                    "id": "model1",
                    "path": "/path/to/model1.gguf",
                    "size_bytes": 500000,
                    "ctx_in": 2048,
                },
            },
        }
        custom_file.write_text(json.dumps(test_data, indent=2))

        registry = load_model_registry(json_path=custom_file)

        assert len(registry) == 1
        assert registry.get_model("model1") is not None

    def test_load_model_registry_nonexistent_file(self: "TestModelLoader", tmp_path: Path) -> None:
        """Test loading registry when file doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.json"

        registry = load_model_registry(json_path=nonexistent)

        assert isinstance(registry, ModelRegistry)
        assert len(registry) == 0
        assert registry.models_file == nonexistent

    def test_save_model_registry_default_path(self: "TestModelLoader", tmp_path: Path) -> None:
        """Test saving registry with default path."""
        registry_file = tmp_path / "models_registry.json"

        # Create a registry with models
        registry = ModelRegistry(models_file=registry_file)
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )
        registry.update_model("test-model", model)

        # Save the registry
        saved_path = save_model_registry(registry)

        assert saved_path == registry_file
        assert registry_file.exists()

        # Verify contents
        data = json.loads(registry_file.read_text())
        assert "llms" in data
        assert "test-model" in data["llms"]

    def test_save_model_registry_custom_path(self: "TestModelLoader", tmp_path: Path) -> None:
        """Test saving registry to custom path."""
        original_file = tmp_path / "original.json"
        custom_file = tmp_path / "custom.json"

        # Create a registry
        registry = ModelRegistry(models_file=original_file)
        model = Model(
            id="model1",
            path="/path/to/model1.gguf",
            size_bytes=500000,
            ctx_in=2048,
        )
        registry.update_model("model1", model)

        # Save to custom path
        saved_path = save_model_registry(registry, json_path=custom_file)

        assert saved_path == custom_file
        assert custom_file.exists()
        assert not original_file.exists()  # Original path not used

        # Verify contents
        data = json.loads(custom_file.read_text())
        assert "model1" in data["llms"]

    @patch("lmstrix.loaders.model_loader.LMStudioClient")
    @patch("lmstrix.loaders.model_loader.ModelScanner")
    def test_scan_and_update_models(
        self: "TestModelLoader",
        mock_scanner_class: Mock,
        mock_client_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test scanning and updating models."""
        # Set up mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner

        # Mock scan results
        new_model = Model(
            id="new-model",
            path="/path/to/new-model.gguf",
            size_bytes=2000000,
            ctx_in=8192,
        )
        removed_model = Model(
            id="removed-model",
            path="/path/to/removed.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )

        mock_scanner.sync_with_registry.return_value = ([new_model], [removed_model])

        # Create a registry
        registry_file = tmp_path / "models.json"
        registry = ModelRegistry(models_file=registry_file)

        # Run scan
        scan_and_update_registry(
            rescan_failed=False,
            rescan_all=False,
            verbose=True,
        )

        assert len(new_models) == 1
        assert new_models[0].id == "new-model"
        assert len(removed_models) == 1
        assert removed_models[0].id == "removed-model"

        # Verify scanner was called correctly
        mock_scanner.sync_with_registry.assert_called_once_with(registry)

    @patch("lmstrix.loaders.model_loader.LMStudioClient")
    @patch("lmstrix.loaders.model_loader.ModelScanner")
    def test_scan_and_update_models_default_client(
        self: "TestModelLoader",
        mock_scanner_class: Mock,
        mock_client_class: Mock,
    ) -> None:
        """Test scan_and_update_models creates default client if none provided."""
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.sync_with_registry.return_value = ([], [])

        registry = Mock()

        scan_and_update_models(registry=registry)

        # Verify client was created
        mock_client_class.assert_called_once_with(verbose=False)
