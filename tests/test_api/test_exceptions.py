"""Tests for API exceptions."""

from lmstrix.api.exceptions import (
    APIConnectionError,
    InferenceError,
    LMStrixError,
    ModelLoadError,
)


class TestAPIExceptions:
    """Test API exception classes."""

    def test_api_error_base(self) -> None:
        """Test base LMStrixError class."""
        error = LMStrixError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_api_connection_error(self) -> None:
        """Test APIConnectionError creation and attributes."""
        error = APIConnectionError("localhost:1234", "Connection refused")
        assert isinstance(error, LMStrixError)
        assert "localhost:1234" in str(error)
        assert "Connection refused" in str(error)

    def test_model_load_error(self) -> None:
        """Test ModelLoadError creation and attributes."""
        model_id = "test-model-123"
        reason = "Insufficient memory"
        error = ModelLoadError(model_id, reason)

        assert isinstance(error, LMStrixError)
        assert model_id in str(error)
        assert reason in str(error)

    def test_inference_error(self) -> None:
        """Test InferenceError creation and attributes."""
        model_id = "test-model-456"
        reason = "Context too long"
        error = InferenceError(model_id, reason)

        assert isinstance(error, LMStrixError)
        assert model_id in str(error)
        assert reason in str(error)

    def test_exception_inheritance(self) -> None:
        """Test that all exceptions inherit from lmstrixError."""

        exceptions = [
            APIConnectionError("host", "reason"),
            ModelLoadError("model", "reason"),
            InferenceError("model", "reason"),
        ]

        for exc in exceptions:
            assert isinstance(exc, LMStrixError)
            assert isinstance(exc, Exception)
