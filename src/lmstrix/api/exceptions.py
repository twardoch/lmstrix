"""Custom exceptions for LMStrix API operations."""


class LMStrixError(Exception):
    """Base exception for all LMStrix errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ModelLoadError(LMStrixError):
    """Raised when a model fails to load."""

    def __init__(self, model_id: str, reason: str, details: dict | None = None) -> None:
        """Initialize the exception."""
        message = f"Failed to load model '{model_id}': {reason}"
        super().__init__(message, details)
        self.model_id = model_id
        self.reason = reason


class InferenceError(LMStrixError):
    """Raised when inference fails."""

    def __init__(self, model_id: str, reason: str, details: dict | None = None) -> None:
        """Initialize the exception."""
        message = f"Inference failed for model '{model_id}': {reason}"
        super().__init__(message, details)
        self.model_id = model_id
        self.reason = reason


class APIConnectionError(LMStrixError):
    """Raised when connection to LM Studio API fails."""

    def __init__(self, endpoint: str, reason: str, details: dict | None = None) -> None:
        """Initialize the exception."""
        message = f"Failed to connect to LM Studio API at '{endpoint}': {reason}"
        super().__init__(message, details)
        self.endpoint = endpoint
        self.reason = reason


class ContextLimitExceededError(InferenceError):
    """Raised when the input exceeds the model's context limit."""

    def __init__(
        self,
        model_id: str,
        input_tokens: int,
        context_limit: int,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception."""
        reason = f"Input tokens ({input_tokens}) exceed context limit ({context_limit})"
        super().__init__(model_id, reason, details)
        self.input_tokens = input_tokens
        self.context_limit = context_limit


class ModelNotFoundError(LMStrixError):
    """Raised when a requested model is not found."""

    def __init__(self, model_id: str, available_models: list[str] | None = None) -> None:
        """Initialize the exception."""
        message = f"Model '{model_id}' not found"
        details = {}
        if available_models:
            details["available_models"] = available_models
        super().__init__(message, details)
        self.model_id = model_id
        self.available_models = available_models or []


class ConfigurationError(LMStrixError):
    """Raised when there's a configuration issue."""

    def __init__(self, config_name: str, reason: str, details: dict | None = None) -> None:
        """Initialize the exception."""
        message = f"Configuration error for '{config_name}': {reason}"
        super().__init__(message, details)
        self.config_name = config_name
        self.reason = reason


class LMStudioInstallationNotFoundError(LMStrixError):
    """Raised when the LM Studio installation path cannot be found."""

    def __init__(self) -> None:
        """Initialize the exception."""
        message = (
            "Could not find LM Studio installation. "
            "Please ensure LM Studio is installed and has been run at least once."
        )
        super().__init__(message)


class ValidationError(LMStrixError):
    """Raised when data validation fails."""

    def __init__(self, field: str, value: any, reason: str) -> None:
        """Initialize the exception."""
        message = f"Validation failed for {field}={value}: {reason}"
        super().__init__(message)
        self.field = field
        self.value = value
        self.reason = reason


class InvalidContextLimitError(ValidationError):
    """Raised when context limit is invalid."""

    def __init__(self, value: int) -> None:
        """Initialize the exception."""
        reason = "must be a positive integer" if value <= 0 else f"{value} seems unreasonably large"
        super().__init__("context_limit", value, reason)


class InvalidModelSizeError(ValidationError):
    """Raised when model size is invalid."""

    def __init__(self, value: int) -> None:
        """Initialize the exception."""
        super().__init__("model_size", value, "must be a non-negative integer")


class RegistryValidationError(LMStrixError):
    """Raised when registry validation fails."""

    def __init__(self, reason: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Registry validation failed: {reason}")


class InvalidModelError(LMStrixError):
    """Raised when a model fails integrity check."""

    def __init__(self, model_id: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Model {model_id} failed integrity check")


class InvalidModelCountError(RegistryValidationError):
    """Raised when registry contains invalid models."""

    def __init__(self, count: int) -> None:
        """Initialize the exception."""
        super().__init__(f"Registry contains {count} invalid models")


class ModelRegistryError(LMStrixError):
    """Raised when there's an error with the model registry."""
