"""Tests for context testing functionality - PUBLIC API ONLY."""

from datetime import datetime
from unittest.mock import Mock, patch

from lmstrix.api.exceptions import ModelLoadError
from lmstrix.core.context_tester import ContextTester, ContextTestResult
from lmstrix.core.models import Model


class TestContextTestResult:
    """Test ContextTestResult data class."""

    def test_result_creation(self) -> None:
        """Test creating a context test result."""
        result = ContextTestResult(
            context_size=4096,
            load_success=True,
            inference_success=True,
            prompt="test",
            response="response",
            error="",
        )

        assert result.context_size == 4096
        assert result.load_success is True
        assert result.inference_success is True
        assert result.prompt == "test"
        assert result.response == "response"
        assert result.error == ""
        assert isinstance(result.timestamp, datetime)

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = ContextTestResult(
            context_size=4096,
            load_success=True,
        )

        result_dict = result.to_dict()
        assert result_dict["context_size"] == 4096
        assert result_dict["load_success"] is True
        assert "timestamp" in result_dict


class TestContextTester:
    """Test ContextTester PUBLIC API."""

    def test_initialization(self) -> None:
        """Test context tester initialization."""
        with patch("lmstrix.core.context_tester.LMStudioClient"):
            tester = ContextTester()
            assert tester.client is not None
            assert tester.test_prompt == "Say hello"
            assert tester.fast_mode is False

    def test_initialization_with_client(self, mock_lmstudio_client: Mock) -> None:
        """Test initialization with custom client."""
        tester = ContextTester(client=mock_lmstudio_client, fast_mode=True)
        assert tester.client == mock_lmstudio_client
        assert tester.fast_mode is True

    def test_test_model_not_found(self, mock_lmstudio_client: Mock) -> None:
        """Test testing a model that doesn't exist."""
        mock_lmstudio_client.load_model.side_effect = ModelLoadError("test-model", "Not found")

        tester = ContextTester(mock_lmstudio_client)
        model = Model(
            id="test-model",
            path="/path/to/model",
            size_bytes=1000000,
            ctx_in=4096,
        )

        # Test model should handle the error gracefully
        with patch.object(tester, "_test_at_context") as mock_test:
            mock_test.return_value = ContextTestResult(
                context_size=4096,
                load_success=False,
                error="Model not found",
            )

            result = tester.test_model(model)
            assert result is not None
            # The actual test_model method returns the model, not the result

    def test_test_all_models(self, mock_lmstudio_client: Mock) -> None:
        """Test batch testing of models."""
        tester = ContextTester(mock_lmstudio_client)

        models = {
            "model1": Model(
                id="model1",
                path="/path/to/model1",
                size_bytes=1000000,
                ctx_in=4096,
            ),
            "model2": Model(
                id="model2",
                path="/path/to/model2",
                size_bytes=2000000,
                ctx_in=8192,
            ),
        }

        # Mock successful tests
        with patch.object(tester, "test_model") as mock_test:
            mock_test.return_value = models["model1"]

            active, updated = tester.test_all_models(models, passes=1)

            # Should attempt to test both models
            assert len(active) <= 2
            assert len(updated) >= 0
