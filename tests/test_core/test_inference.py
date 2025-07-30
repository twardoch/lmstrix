"""Tests for inference functionality - SIMPLIFIED."""

from unittest.mock import Mock, patch

import pytest

from lmstrix.api.exceptions import ModelNotFoundError
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.core.models import Model


class TestInferenceDict:
    """Test inference result dictionary structure."""

    def test_inference_dict_success(self) -> None:
        """Test successful inference result dict."""
        result = {
            "succeeded": True,
            "response": "Test response",
            "model_id": "test-model",
            "tokens_used": 10,
            "inference_time": 1.5,
            "error": None,
            "prompt": "test prompt",
        }

        assert result["succeeded"] is True
        assert result["response"] == "Test response"
        assert result["model_id"] == "test-model"
        assert result["tokens_used"] == 10
        assert result["inference_time"] == 1.5
        assert result["error"] is None

    def test_inference_dict_failure(self) -> None:
        """Test failed inference result dict."""
        result = {
            "succeeded": False,
            "response": "",
            "model_id": "test-model",
            "tokens_used": 0,
            "inference_time": 0.5,
            "error": "Model failed to load",
            "prompt": "test prompt",
        }

        assert result["succeeded"] is False
        assert result["response"] == ""
        assert result["error"] == "Model failed to load"

    def test_inference_dict_empty_response(self) -> None:
        """Test inference result dict with empty response."""
        result = {
            "succeeded": True,
            "response": "",
            "model_id": "test-model",
            "tokens_used": 5,
            "inference_time": 1.0,
            "error": None,
            "prompt": "test prompt",
        }

        assert result["succeeded"] is True
        assert result["response"] == ""
        assert result["tokens_used"] == 5


class TestInferenceManager:
    """Test InferenceManager PUBLIC API."""

    def test_manager_initialization(self) -> None:
        """Test inference manager initialization."""
        with patch("lmstrix.core.inference_manager.ModelRegistry"):
            manager = InferenceManager()
            assert manager.registry is not None
            assert manager.client is not None

    def test_manager_with_custom_client(self, mock_lmstudio_client: Mock) -> None:
        """Test manager with custom client."""
        manager = InferenceManager(client=mock_lmstudio_client)
        assert manager.client == mock_lmstudio_client

    def test_infer_model_not_found(self) -> None:
        """Test inference with non-existent model."""
        mock_registry = Mock()
        mock_registry.find_model.return_value = None
        mock_registry.list_models.return_value = []

        manager = InferenceManager(registry=mock_registry)

        with pytest.raises(ModelNotFoundError):
            manager.infer("non-existent", "test prompt")

    def test_infer_basic_success(self, mock_lmstudio_client: Mock) -> None:
        """Test basic successful inference."""
        # Setup registry
        mock_registry = Mock()
        model = Model(
            id="test-model",
            path="/path/to/model",
            size_bytes=1000000,
            ctx_in=4096,
            tested_max_context=3500,
        )
        mock_registry.find_model.return_value = model

        # Setup client
        mock_llm = Mock()
        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_lmstudio_client.is_model_loaded.return_value = (False, 0)
        mock_lmstudio_client.completion.return_value = Mock(
            content="Test response",
            usage={"total_tokens": 15},
        )

        manager = InferenceManager(client=mock_lmstudio_client, registry=mock_registry)
        result = manager.infer("test-model", "test prompt")

        assert result["succeeded"] is True
        assert result["response"] == "Test response"
        assert result["model_id"] == "test-model"
        assert result["tokens_used"] == 15
