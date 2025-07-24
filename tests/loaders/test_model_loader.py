"""Unit tests for the model loader functionality in LMStrix.

This test suite focuses on the `scan_and_update_registry` function, which is responsible
for keeping the local model registry (`lmstrix.json`) synchronized with the models
downloaded in LM Studio.

Key behaviors tested:
- Discovering and adding a new model to an empty registry.
- Updating the registry with a new model while preserving existing ones.
- Ignoring models that are listed in the remote source but no longer exist locally.
- Preserving existing test results for models that are re-scanned.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lmstrix.loaders.model_loader import scan_and_update_registry
from lmstrix.core.models import LmsModel, ModelRegistry, TestResult

# --- Mock Data ---

# Represents a model that is already in our local registry
EXISTING_MODEL_PATH = "/models/existing-model.gguf"
EXISTING_MODEL = LmsModel(
    name="existing-model",
    path=EXISTING_MODEL_PATH,
    test_result=TestResult(max_context_length=2048, status="passed")
)

# Represents a new model found in the LM Studio directory
NEW_MODEL_PATH = "/models/new-model.gguf"
NEW_MODEL_REMOTE_DICT = {
    "path": NEW_MODEL_PATH,
    "name": "new-model",
    "size_bytes": 123456789,
    "architecture": "llama"
}

# Represents a model that was once in the registry but is now deleted
DELETED_MODEL_PATH = "/models/deleted-model.gguf"
DELETED_MODEL = LmsModel(name="deleted-model", path=DELETED_MODEL_PATH)

# --- Fixtures ---

@pytest.fixture
def mock_empty_registry():
    """Fixture for an empty ModelRegistry."""
    return ModelRegistry()

@pytest.fixture
def mock_populated_registry():
    """Fixture for a ModelRegistry with existing and soon-to-be-deleted models."""
    registry = ModelRegistry()
    registry.models = {
        EXISTING_MODEL_PATH: EXISTING_MODEL,
        DELETED_MODEL_PATH: DELETED_MODEL
    }
    return registry

# --- Test Cases ---

@pytest.mark.asyncio
@patch("lmstrix.loaders.model_loader.get_lmstudio_path")
@patch("lmstrix.loaders.model_loader.LmsClient.list_downloaded_models")
@patch("lmstrix.loaders.model_loader.ModelRegistry.load")
@patch("lmstrix.loaders.model_loader.ModelRegistry.save")
async def test_scan_with_new_model(mock_save, mock_load, mock_list_models, mock_get_path, mock_empty_registry):
    """Test adding a new model to an empty registry."""
    # --- Test Setup ---
    mock_get_path.return_value = "/fake/lmstudio/path"
    mock_load.return_value = mock_empty_registry
    mock_list_models.return_value = [NEW_MODEL_REMOTE_DICT]

    # --- Run Test ---
    await scan_and_update_registry()

    # --- Assertions ---
    # Verify the new model was added correctly
    assert len(mock_empty_registry.models) == 1
    assert NEW_MODEL_PATH in mock_empty_registry.models
    assert mock_empty_registry.models[NEW_MODEL_PATH].name == "new-model"
    mock_save.assert_called_once()

@pytest.mark.asyncio
@patch("lmstrix.loaders.model_loader.get_lmstudio_path")
@patch("lmstrix.loaders.model_loader.LmsClient.list_downloaded_models")
@patch("lmstrix.loaders.model_loader.ModelRegistry.load")
@patch("lmstrix.loaders.model_loader.ModelRegistry.save")
async def test_scan_updates_and_preserves_data(mock_save, mock_load, mock_list_models, mock_get_path, mock_populated_registry):
    """Test that scanning adds new models, removes deleted ones, and preserves existing data."""
    # --- Test Setup ---
    # LM Studio reports the existing model and a new one, but not the deleted one
    mock_get_path.return_value = "/fake/lmstudio/path"
    mock_load.return_value = mock_populated_registry
    mock_list_models.return_value = [
        {"path": EXISTING_MODEL_PATH, "name": "updated-name"}, # Name change
        NEW_MODEL_REMOTE_DICT
    ]

    # --- Run Test ---
    await scan_and_update_registry()

    # --- Assertions ---
    # Final registry should have 2 models
    assert len(mock_populated_registry.models) == 2

    # The deleted model should be gone
    assert DELETED_MODEL_PATH not in mock_populated_registry.models

    # The new model should be present
    assert NEW_MODEL_PATH in mock_populated_registry.models

    # The existing model should have its name updated but its test result preserved
    existing_model_updated = mock_populated_registry.models[EXISTING_MODEL_PATH]
    assert existing_model_updated.name == "updated-name"
    assert existing_model_updated.test_result is not None
    assert existing_model_updated.test_result.max_context_length == 2048

    mock_save.assert_called_once()

@pytest.mark.asyncio
@patch("lmstrix.loaders.model_loader.get_lmstudio_path")
@patch("lmstrix.loaders.model_loader.LmsClient.list_downloaded_models")
@patch("lmstrix.loaders.model_loader.ModelRegistry.load")
@patch("lmstrix.loaders.model_loader.ModelRegistry.save")
async def test_scan_no_models_found(mock_save, mock_load, mock_list_models, mock_get_path, mock_empty_registry):
    """Test that the registry remains empty if no models are found."""
    # --- Test Setup ---
    mock_get_path.return_value = "/fake/lmstudio/path"
    mock_load.return_value = mock_empty_registry
    mock_list_models.return_value = []

    # --- Run Test ---
    await scan_and_update_registry()

    # --- Assertions ---
    assert len(mock_empty_registry.models) == 0
    # Save should still be called to write the empty state
    mock_save.assert_called_once()
