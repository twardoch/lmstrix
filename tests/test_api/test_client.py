"""Tests for LMStudioClient."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from lmstrix.api.client import CompletionResponse, LMStudioClient
from lmstrix.api.exceptions import APIConnectionError, InferenceError, ModelLoadError


class TestCompletionResponse:
    """Test CompletionResponse model."""

    def test_completion_response_creation(self) -> None:
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

    def test_completion_response_minimal(self) -> None:
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

    def test_client_initialization(self) -> None:
        """Test client initialization with different verbose settings."""
        with patch("lmstrix.api.client.logger") as mock_logger:
            LMStudioClient(verbose=True)
            mock_logger.enable.assert_called_once_with("lmstrix")

            LMStudioClient(verbose=False)
            mock_logger.disable.assert_called_with("lmstrix")

    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_success(self, mock_lmstudio) -> None:
        """Test successful list_models call."""
        mock_models = [
            {"id": "model1", "size_bytes": 1000},
            {"id": "model2", "size_bytes": 2000},
        ]
        mock_lmstudio.list_downloaded_models.return_value = mock_models

        client = LMStudioClient()
        result = client.list_models()

        assert result == mock_models
        mock_lmstudio.list_downloaded_models.assert_called_once()

    @patch("lmstrix.api.client.lmstudio")
    def test_list_models_failure(self, mock_lmstudio) -> None:
        """Test list_models with connection error."""
        mock_lmstudio.list_downloaded_models.side_effect = Exception("Connection failed")

        client = LMStudioClient()
        with pytest.raises(APIConnectionError) as exc_info:
            client.list_models()

        assert "Failed to list models" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    @patch("lmstrix.api.client.lmstudio")
    def test_load_model_success(self, mock_lmstudio) -> None:
        """Test successful model loading."""
        mock_llm = Mock()
        mock_lmstudio.llm.return_value = mock_llm

        client = LMStudioClient()
        result = client.load_model("test-model", 4096)

        assert result == mock_llm
        mock_lmstudio.llm.assert_called_once_with(
            "test-model",
            config={"context_length": 4096},
        )

    @patch("lmstrix.api.client.lmstudio")
    def test_load_model_failure(self, mock_lmstudio) -> None:
        """Test model loading failure."""
        mock_lmstudio.llm.side_effect = Exception("Model not found")

        client = LMStudioClient()
        with pytest.raises(ModelLoadError) as exc_info:
            client.load_model("test-model", 4096)

        assert "test-model" in str(exc_info.value)
        assert "Failed to load model" in str(exc_info.value)
        assert "Model not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acompletion_success(self, mock_llm, mock_completion_response) -> None:
        """Test successful async completion."""
        mock_llm.complete = AsyncMock(return_value=mock_completion_response)

        client = LMStudioClient()
        result = await client.acompletion(
            mock_llm,
            "2+2=",
            temperature=0.5,
            max_tokens=100,
        )

        assert isinstance(result, CompletionResponse)
        assert result.content == "4"
        assert result.model == "test-model"
        assert result.usage["total_tokens"] == 11

        mock_llm.complete.assert_called_once_with(
            "2+2=",
            temperature=0.5,
            max_tokens=100,
        )

    @pytest.mark.asyncio
    async def test_acompletion_failure(self, mock_llm) -> None:
        """Test async completion failure."""
        mock_llm.complete = AsyncMock(side_effect=Exception("Inference failed"))
        mock_llm.model_id = "test-model"

        client = LMStudioClient()
        with pytest.raises(InferenceError) as exc_info:
            await client.acompletion(mock_llm, "test prompt")

        assert "test-model" in str(exc_info.value)
        assert "Inference failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acompletion_with_defaults(self, mock_llm, mock_completion_response) -> None:
        """Test async completion with default parameters."""
        mock_llm.complete = AsyncMock(return_value=mock_completion_response)

        client = LMStudioClient()
        await client.acompletion(mock_llm, "Hello")

        mock_llm.complete.assert_called_once_with(
            "Hello",
            temperature=0.7,  # default
            max_tokens=-1,  # default (unlimited)
        )
