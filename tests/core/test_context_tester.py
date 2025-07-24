"""Unit tests for the ContextTester component of LMStrix.

This test suite verifies the core logic of the `ContextTester`, particularly the
binary search algorithm used to find the maximum working context of a model.
It uses a mocked `lmstudio` client to simulate various scenarios without requiring
a live LM Studio instance.

Key scenarios tested:
- A model that passes and fails at predictable context sizes.
- A model that never successfully loads.
- A model that loads but consistently fails inference.
- A model that works perfectly at all tested context sizes.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lmstrix.core.context_tester import ContextTester
from lmstrix.core.models import LmsModel, ModelRegistry

# A mock model path for testing purposes
MOCK_MODEL_PATH = "/fake/path/to/model.gguf"

@pytest.fixture
def mock_model_registry():
    """Fixture to create a mock ModelRegistry with a single model."""
    model = LmsModel(name="test-model", path=MOCK_MODEL_PATH)
    registry = ModelRegistry()
    registry.models = {MOCK_MODEL_PATH: model}
    return registry

@pytest.fixture
def mock_lmstudio_client():
    """Fixture to create a mock LM Studio client with async methods."""
    client = MagicMock()
    client.load_model = AsyncMock()
    client.unload_model = AsyncMock()
    client.predict = AsyncMock()
    return client

@pytest.mark.asyncio
@patch("lmstrix.core.context_tester.LmsClient")
@patch("lmstrix.core.context_tester.ModelRegistry.load")
@patch("lmstrix.core.context_tester.ModelRegistry.save")
async def test_binary_search_logic_success(mock_save, mock_load, mock_client_constructor, mock_model_registry, mock_lmstudio_client):
    """Test the binary search logic for a model that works up to a certain context size."""
    # --- Test Setup ---
    # Simulate a model that works with 4096 context but fails with 8192
    def predict_side_effect(prompt, **kwargs):
        context_length = len(prompt)
        if context_length <= 4096:
            return {"choices": [{"message": {"content": "success"}}]}
        # Simulate an inference failure for larger contexts
        raise ValueError("Inference failed due to context size")

    mock_lmstudio_client.predict.side_effect = predict_side_effect
    mock_client_constructor.return_value = mock_lmstudio_client
    mock_load.return_value = mock_model_registry

    tester = ContextTester(min_context=1024, max_context=16384)

    # --- Run Test ---
    await tester.test_model(MOCK_MODEL_PATH)

    # --- Assertions ---
    # Verify that the model was loaded and unloaded exactly once
    mock_lmstudio_client.load_model.assert_called_once_with(MOCK_MODEL_PATH)
    mock_lmstudio_client.unload_model.assert_called_once()

    # Check that the registry was saved with the correct result
    result = mock_model_registry.models[MOCK_MODEL_PATH].test_result
    assert result is not None
    assert result.max_context_length == 4096
    assert result.status == "passed"
    mock_save.assert_called_once()

@pytest.mark.asyncio
@patch("lmstrix.core.context_tester.LmsClient")
@patch("lmstrix.core.context_tester.ModelRegistry.load")
@patch("lmstrix.core.context_tester.ModelRegistry.save")
async def test_model_never_loads(mock_save, mock_load, mock_client_constructor, mock_model_registry, mock_lmstudio_client):
    """Test the scenario where the model fails to load in LM Studio."""
    # --- Test Setup ---
    mock_lmstudio_client.load_model.side_effect = Exception("Failed to load model")
    mock_client_constructor.return_value = mock_lmstudio_client
    mock_load.return_value = mock_model_registry

    tester = ContextTester()

    # --- Run Test ---
    await tester.test_model(MOCK_MODEL_PATH)

    # --- Assertions ---
    # The result should indicate a failure to load
    result = mock_model_registry.models[MOCK_MODEL_PATH].test_result
    assert result is not None
    assert result.max_context_length == 0
    assert "Failed to load model" in result.error_message
    assert result.status == "failed_to_load"
    mock_save.assert_called_once()

@pytest.mark.asyncio
@patch("lmstrix.core.context_tester.LmsClient")
@patch("lmstrix.core.context_tester.ModelRegistry.load")
@patch("lmstrix.core.context_tester.ModelRegistry.save")
async def test_inference_always_fails(mock_save, mock_load, mock_client_constructor, mock_model_registry, mock_lmstudio_client):
    """Test the scenario where the model loads but inference always fails."""
    # --- Test Setup ---
    mock_lmstudio_client.predict.side_effect = ValueError("GPU out of memory")
    mock_client_constructor.return_value = mock_lmstudio_client
    mock_load.return_value = mock_model_registry

    tester = ContextTester(min_context=1024, max_context=4096)

    # --- Run Test ---
    await tester.test_model(MOCK_MODEL_PATH)

    # --- Assertions ---
    # The result should show that the lowest context size failed
    result = mock_model_registry.models[MOCK_MODEL_PATH].test_result
    assert result is not None
    assert result.max_context_length == 0
    assert "GPU out of memory" in result.error_message
    assert result.status == "failed_inference"
    mock_save.assert_called_once()

@pytest.mark.asyncio
@patch("lmstrix.core.context_tester.LmsClient")
@patch("lmstrix.core.context_tester.ModelRegistry.load")
@patch("lmstrix.core.context_tester.ModelRegistry.save")
async def test_model_works_at_max_context(mock_save, mock_load, mock_client_constructor, mock_model_registry, mock_lmstudio_client):
    """Test a model that works perfectly up to the maximum testable context."""
    # --- Test Setup ---
    mock_lmstudio_client.predict.return_value = {"choices": [{"message": {"content": "success"}}]}
    mock_client_constructor.return_value = mock_lmstudio_client
    mock_load.return_value = mock_model_registry

    tester = ContextTester(min_context=1024, max_context=8192)

    # --- Run Test ---
    await tester.test_model(MOCK_MODEL_PATH)

    # --- Assertions ---
    # The result should show the max context as the highest passing value
    result = mock_model_registry.models[MOCK_MODEL_PATH].test_result
    assert result is not None
    assert result.max_context_length == 8192
    assert result.status == "passed"
    mock_save.assert_called_once()
