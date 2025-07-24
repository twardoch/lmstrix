"""Tests for inference engine."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from lmstrix.api.exceptions import InferenceError
from lmstrix.core.inference import InferenceEngine, InferenceResult
from lmstrix.core.models import Model


class TestInferenceResult:
    """Test InferenceResult model."""

    def test_inference_result_success(self):
        """Test successful inference result."""
        result = InferenceResult(
            model_id="test-model",
            prompt="Hello",
            response="Hi there!",
            tokens_used=15,
            inference_time=0.5,
        )

        assert result.model_id == "test-model"
        assert result.prompt == "Hello"
        assert result.response == "Hi there!"
        assert result.tokens_used == 15
        assert result.inference_time == 0.5
        assert result.error is None
        assert result.succeeded is True

    def test_inference_result_failure(self):
        """Test failed inference result."""
        result = InferenceResult(
            model_id="test-model",
            prompt="Hello",
            response="",
            error="Model failed to load",
        )

        assert result.response == ""
        assert result.error == "Model failed to load"
        assert result.succeeded is False

    def test_inference_result_empty_response(self):
        """Test result with empty response is considered failed."""
        result = InferenceResult(
            model_id="test-model",
            prompt="Hello",
            response="",
            tokens_used=10,
        )

        assert result.succeeded is False  # Empty response = failure


class TestInferenceEngine:
    """Test InferenceEngine class."""

    def test_engine_initialization_defaults(self):
        """Test engine initialization with defaults."""
        with patch("lmstrix.core.inference.LMStudioClient") as mock_client_class:
            with patch("lmstrix.core.inference.ModelRegistry") as mock_registry_class:
                engine = InferenceEngine()

                mock_client_class.assert_called_once_with(verbose=False)
                mock_registry_class.assert_called_once()
                assert engine.verbose is False

    def test_engine_initialization_custom(self, mock_lmstudio_client):
        """Test engine initialization with custom client and registry."""
        mock_registry = Mock()

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
            verbose=True,
        )

        assert engine.client == mock_lmstudio_client
        assert engine.registry == mock_registry
        assert engine.verbose is True

    @pytest.mark.asyncio
    async def test_infer_model_not_found(self):
        """Test inference with non-existent model."""
        mock_registry = Mock()
        mock_registry.get_model.return_value = None

        engine = InferenceEngine(model_registry=mock_registry)

        result = await engine.infer("non-existent-model", "Hello")

        assert result.model_id == "non-existent-model"
        assert result.prompt == "Hello"
        assert result.response == ""
        assert "not found" in result.error.lower()
        assert result.succeeded is False

    @pytest.mark.asyncio
    async def test_infer_success(self, mock_lmstudio_client, mock_llm):
        """Test successful inference."""
        # Set up mock model in registry
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
            tested_max_context=3500,
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        # Set up mock LLM and response
        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="Hello! How can I help?", usage={"total_tokens": 20})
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        with patch("time.time", side_effect=[100.0, 100.5]):  # 0.5 second inference
            result = await engine.infer("test-model", "Hello", temperature=0.8)

        assert result.model_id == "test-model"
        assert result.prompt == "Hello"
        assert result.response == "Hello! How can I help?"
        assert result.tokens_used == 20
        assert result.inference_time == 0.5
        assert result.error is None
        assert result.succeeded is True

        # Verify calls
        mock_lmstudio_client.load_model.assert_called_once_with("test-model", 3500)
        mock_lmstudio_client.acompletion.assert_called_once_with(
            mock_llm,
            "Hello",
            temperature=0.8,
            max_tokens=-1,
        )

    @pytest.mark.asyncio
    async def test_infer_with_untested_model(self, mock_lmstudio_client, mock_llm):
        """Test inference with model that hasn't been context tested."""
        # Model without tested_max_context
        model = Model(
            id="untested-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=8192,  # Only declared context
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="Response", usage={"total_tokens": 10})
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        result = await engine.infer("untested-model", "Test")

        assert result.succeeded is True
        # Should use declared context limit
        mock_lmstudio_client.load_model.assert_called_once_with("untested-model", 8192)

    @pytest.mark.asyncio
    async def test_infer_with_max_tokens(self, mock_lmstudio_client, mock_llm):
        """Test inference with custom max_tokens."""
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="Short", usage={"total_tokens": 5})
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        result = await engine.infer("test-model", "Generate text", max_tokens=50)

        assert result.succeeded is True

        # Verify max_tokens was passed
        call_args = mock_lmstudio_client.acompletion.call_args
        assert call_args[1]["max_tokens"] == 50

    @pytest.mark.asyncio
    async def test_infer_load_failure(self, mock_lmstudio_client):
        """Test inference when model fails to load."""
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        # Mock load failure
        mock_lmstudio_client.load_model.side_effect = Exception("Failed to load model")

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        result = await engine.infer("test-model", "Hello")

        assert result.succeeded is False
        assert "Failed to load model" in result.error

    @pytest.mark.asyncio
    async def test_infer_completion_failure(self, mock_lmstudio_client, mock_llm):
        """Test inference when completion fails."""
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        mock_lmstudio_client.load_model.return_value = mock_llm
        # Mock completion failure
        mock_lmstudio_client.acompletion = AsyncMock(
            side_effect=InferenceError("test-model", "Context too long"),
        )

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        result = await engine.infer("test-model", "Very long prompt" * 1000)

        assert result.succeeded is False
        assert "Context too long" in result.error

    @pytest.mark.asyncio
    async def test_run_inference_simple(self, mock_lmstudio_client, mock_llm):
        """Test simple run_inference method."""
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=4096,
        )

        mock_registry = Mock()
        mock_registry.get_model.return_value = model

        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="42", usage={"total_tokens": 5})
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        engine = InferenceEngine(
            client=mock_lmstudio_client,
            model_registry=mock_registry,
        )

        # Assuming run_inference is a convenience method
        result = await engine.run_inference(
            model_id="test-model",
            prompt="What is the answer?",
            temperature=0.5,
            max_tokens=100,
        )

        assert isinstance(result, InferenceResult)
        assert result.response == "42"
        assert result.succeeded is True
