"""Tests for LMStudioClient."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from lmstrix.api.client import CompletionResponse, LMStudioClient, _sdk_model_info_by_key
from lmstrix.api.exceptions import APIConnectionError, InferenceError, ModelLoadError


class TestCompletionResponse:
    """Test CompletionResponse model."""

    def test_completion_response_creation(self: "TestCompletionResponse") -> None:
        """Test creating a CompletionResponse."""
        response = CompletionResponse(
            content="Test response",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
        )

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"

    def test_completion_response_minimal(self: "TestCompletionResponse") -> None:
        """Test creating a CompletionResponse with minimal fields."""
        response = CompletionResponse(
            content="Test",
            model="model",
        )

        assert response.content == "Test"
        assert response.model == "model"
        assert response.usage == {}
        assert response.finish_reason is None


class TestLMStudioClient:
    """Test LMStudioClient class."""

    def test_client_initialization(self: "TestLMStudioClient") -> None:
        """Test client initialization with different verbose settings."""
        with patch("lmstrix.api.client.logger") as mock_logger:
            LMStudioClient(verbose=True)
            mock_logger.enable.assert_called_once_with("lmstrix")

            LMStudioClient(verbose=False)
            mock_logger.disable.assert_called_with("lmstrix")

    @patch("lmstrix.api.client.httpx.get")
    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_success(
        self: "TestLMStudioClient",
        mock_lmstudio: Mock,
        mock_http_get: Mock,
    ) -> None:
        """Test successful list_models call."""
        mock_http_get.side_effect = Exception("REST API unavailable")
        mock_model_info1 = Mock(
            model_key="model1",
            path="/path/to/model1",
            size_bytes=1000,
            max_context_length=4096,
            display_name="Model One",
            architecture="llama",
            trainedForToolUse=False,
            vision=False,
            type="llm",
        )
        mock_model_info2 = Mock(
            model_key="model2",
            path="/path/to/model2",
            size_bytes=2000,
            max_context_length=8192,
            display_name="Model Two",
            architecture="mistral",
            trainedForToolUse=True,
            vision=True,
            type="llm",
        )
        mock_model1 = Mock(info=mock_model_info1)
        mock_model2 = Mock(info=mock_model_info2)
        mock_lmstudio.list_downloaded_models.return_value = [mock_model1, mock_model2]

        client = LMStudioClient()
        result = client.list_models()

        expected_result = [
            {
                "id": "model1",
                "path": "/path/to/model1",
                "size_bytes": 1000,
                "context_length": 4096,
                "display_name": "Model One",
                "architecture": "llama",
                "has_tools": False,
                "has_vision": False,
                "capabilities": {
                    "vision": False,
                    "trained_for_tool_use": False,
                },
                "model_type": "llm",
            },
            {
                "id": "model2",
                "path": "/path/to/model2",
                "size_bytes": 2000,
                "context_length": 8192,
                "display_name": "Model Two",
                "architecture": "mistral",
                "has_tools": True,
                "has_vision": True,
                "capabilities": {
                    "vision": True,
                    "trained_for_tool_use": True,
                },
                "model_type": "llm",
            },
        ]
        assert result == expected_result
        mock_lmstudio.list_downloaded_models.assert_called_once()

    @patch("lmstrix.api.client.httpx.get")
    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_merges_rest_capabilities(
        self: "TestLMStudioClient",
        mock_lmstudio: Mock,
        mock_http_get: Mock,
    ) -> None:
        """Test REST model capabilities override SDK fallback metadata."""
        mock_model_info = SimpleNamespace(
            model_key="google/gemma-4-26b-a4b",
            path="/path/to/gemma",
            size_bytes=17990911801,
            max_context_length=262144,
            display_name="Gemma 4 26B A4B",
            architecture="gemma4",
            trained_for_tool_use=False,
            vision=False,
            type="llm",
        )
        mock_lmstudio.list_downloaded_models.return_value = [Mock(info=mock_model_info)]

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "models": [
                {
                    "key": "google/gemma-4-26b-a4b",
                    "type": "llm",
                    "capabilities": {
                        "vision": True,
                        "trained_for_tool_use": True,
                        "reasoning": {
                            "allowed_options": ["off", "on"],
                            "default": "on",
                        },
                    },
                },
            ],
        }
        mock_http_get.return_value = mock_response

        result = LMStudioClient().list_models()

        assert result[0]["has_vision"] is True
        assert result[0]["has_tools"] is True
        assert result[0]["capabilities"] == {
            "vision": True,
            "trained_for_tool_use": True,
            "reasoning": {
                "allowed_options": ["off", "on"],
                "default": "on",
            },
        }

    @patch("lmstrix.api.client.httpx.get")
    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_uses_sdk_capability_fallback(
        self: "TestLMStudioClient",
        mock_lmstudio: Mock,
        mock_http_get: Mock,
    ) -> None:
        """Test SDK snake_case capability fields are used when REST is unavailable."""
        mock_http_get.side_effect = Exception("server unavailable")
        mock_model_info = SimpleNamespace(
            model_key="tool-model",
            path="/path/to/tool-model",
            size_bytes=2000,
            max_context_length=8192,
            display_name="Tool Model",
            architecture="llama",
            trained_for_tool_use=True,
            vision=True,
            type="llm",
        )
        mock_lmstudio.list_downloaded_models.return_value = [Mock(info=mock_model_info)]

        result = LMStudioClient().list_models()

        assert result[0]["has_tools"] is True
        assert result[0]["has_vision"] is True
        assert result[0]["capabilities"] == {
            "vision": True,
            "trained_for_tool_use": True,
        }

    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_failure(self: "TestLMStudioClient", mock_lmstudio: Mock) -> None:
        """Test list_models with connection error."""
        mock_lmstudio.list_downloaded_models.side_effect = Exception("Connection failed")

        client = LMStudioClient()
        with pytest.raises(APIConnectionError) as exc_info:
            client.list_models()

        assert "Failed to list models" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    def test_sdk_model_info_by_key_uses_model_key(self: "TestLMStudioClient") -> None:
        """Test SDK model info is normalized to a dict keyed by modelKey."""
        info = Mock()
        info.to_dict.return_value = {
            "modelKey": "model-one",
            "displayName": "Model One",
            "trainedForToolUse": True,
            "vision": False,
        }

        result = _sdk_model_info_by_key([Mock(info=info)])

        assert result == {
            "model-one": {
                "modelKey": "model-one",
                "displayName": "Model One",
                "trainedForToolUse": True,
                "vision": False,
            },
        }

    @patch("lmstrix.api.client.lmstudio")
    def test_load_model_success(self: "TestLMStudioClient", mock_lmstudio: Mock) -> None:
        """Test successful model loading."""
        mock_llm = Mock()
        mock_lmstudio.llm.return_value = mock_llm

        client = LMStudioClient()
        result = client.load_model("test-model", 4096)

        assert result == mock_llm
        mock_lmstudio.llm.assert_called_once_with(
            "test-model",
            config={"contextLength": 4096, "flashAttention": True},
        )

    @patch("lmstrix.api.client.lmstudio")
    def test_load_model_failure(self: "TestLMStudioClient", mock_lmstudio: Mock) -> None:
        """Test model loading failure."""
        mock_lmstudio.llm.side_effect = Exception("Model not found")

        client = LMStudioClient()
        with pytest.raises(ModelLoadError) as exc_info:
            client.load_model("test-model", 4096)

        assert "test-model" in str(exc_info.value)
        assert "Failed to load model" in str(exc_info.value)
        assert "Model not found" in str(exc_info.value)

    def test_completion_success(
        self: "TestLMStudioClient",
        mock_llm: Mock,
        mock_completion_response: CompletionResponse,
    ) -> None:
        """Test successful completion."""
        mock_llm.complete = Mock(return_value=mock_completion_response)

        client = LMStudioClient()
        result = client.completion(
            llm=mock_llm,
            prompt="2+2=",
            out_ctx=100,
        )

        assert isinstance(result, CompletionResponse)
        assert result.content == "4"
        assert result.model == "test-model"
        assert result.usage["total_tokens"] == 11

        mock_llm.complete.assert_called_once_with(
            "2+2=",
            config={"maxTokens": 100, "temperature": 0.7},
        )

    def test_completion_failure(
        self: "TestLMStudioClient",
        mock_llm: Mock,
    ) -> None:
        """Test completion failure."""
        mock_llm.complete = Mock(side_effect=Exception("Inference failed"))
        mock_llm.model_id = "test-model"

        client = LMStudioClient()
        with pytest.raises(InferenceError) as exc_info:
            client.completion(mock_llm, "test prompt")

        assert "test-model" in str(exc_info.value)
        assert "Inference failed" in str(exc_info.value)

    def test_completion_with_defaults(
        self: "TestLMStudioClient",
        mock_llm: Mock,
        mock_completion_response: CompletionResponse,
    ) -> None:
        """Test completion with default parameters."""
        mock_llm.complete = Mock(return_value=mock_completion_response)

        client = LMStudioClient()
        client.completion(
            llm=mock_llm,
            prompt="Hello",
        )

        mock_llm.complete.assert_called_once_with(
            "Hello",
            config={"maxTokens": 100},
        )
