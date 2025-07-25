# tests/loaders/test_model_loader.py
from unittest.mock import patch

import pytest

from lmstrix.core.models import Model, Models
from lmstrix.loaders.model_loader import ModelLoader


@pytest.fixture
def mock_lmstudio_client():
    """Fixture for a mocked lmstudio client."""
    with patch("lmstrix.loaders.model_loader.lmstudio") as mock_lmstudio:
        yield mock_lmstudio


@pytest.fixture
def mock_models_file(tmp_path):
    """Fixture to create a temporary models.json file."""
    return tmp_path / "models.json"


def test_scan_and_update_adds_new_models(mock_lmstudio_client, mock_models_file) -> None:
    """
    Tests that new models from the scan are added to the registry.
    """
    # Arrange
    mock_lmstudio_client.list_downloaded_models.return_value = [
        {"path": "/models/phi.gguf", "name": "phi.gguf"},
    ]
    loader = ModelLoader(models_file=mock_models_file)
    loader.models = Models(models={})

    # Act
    loader.scan_and_update_registry()

    # Assert
    assert "phi" in loader.models.models
    assert loader.models.models["phi"].path == "/models/phi.gguf"


def test_scan_and_update_removes_deleted_models(mock_lmstudio_client, mock_models_file) -> None:
    """
    Tests that models no longer present in the scan are removed from the registry.
    """
    # Arrange
    mock_lmstudio_client.list_downloaded_models.return_value = [
        {"path": "/models/phi.gguf", "name": "phi.gguf"},
    ]
    existing_model = Model(id="llama", path="/models/llama.gguf", name="llama.gguf")
    loader = ModelLoader(models_file=mock_models_file)
    loader.models = Models(models={"llama": existing_model})

    # Act
    loader.scan_and_update_registry()

    # Assert
    assert "llama" not in loader.models.models
    assert "phi" in loader.models.models


def test_scan_and_update_preserves_test_data(mock_lmstudio_client, mock_models_file) -> None:
    """
    Ensures that existing test data is not overwritten for models that are re-scanned.
    """
    # Arrange
    mock_lmstudio_client.list_downloaded_models.return_value = [
        {"path": "/models/phi.gguf", "name": "phi.gguf"},
    ]
    existing_model = Model(
        id="phi",
        path="/models/phi.gguf",
        name="phi.gguf",
        max_context_tested=4096,
        test_results=[(2048, True), (4096, True)],
    )
    loader = ModelLoader(models_file=mock_models_file)
    loader.models = Models(models={"phi": existing_model})

    # Act
    loader.scan_and_update_registry()

    # Assert
    assert "phi" in loader.models.models
    updated_model = loader.models.models["phi"]
    assert updated_model.max_context_tested == 4096
    assert updated_model.test_results is not None
    assert len(updated_model.test_results) == 2


def test_load_from_non_existent_file(mock_models_file) -> None:
    """
    Tests that loading from a non-existent file results in an empty Models object.
    """
    # Arrange
    loader = ModelLoader(models_file=mock_models_file)  # File doesn't exist yet

    # Act
    models = loader.load()

    # Assert
    assert isinstance(models, Models)
    assert not models.models


def test_save_and_load_cycle(mock_models_file) -> None:
    """
    Tests that saving models to a file and loading them back preserves the data.
    """
    # Arrange
    loader1 = ModelLoader(models_file=mock_models_file)
    model = Model(id="test", path="/fake/test.gguf", name="test.gguf", max_context_tested=2048)
    loader1.models = Models(models={"test": model})

    # Act
    loader1.save()

    loader2 = ModelLoader(models_file=mock_models_file)
    loaded_models = loader2.load()

    # Assert
    assert "test" in loaded_models.models
    assert loaded_models.models["test"].max_context_tested == 2048
    assert loaded_models.models["test"].path == "/fake/test.gguf"
