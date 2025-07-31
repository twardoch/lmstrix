"""API client and exceptions for LMStrix."""

from lmstrix.api.client import CompletionResponse, LMStudioClient
from lmstrix.utils.logging import logger

from lmstrix.api.exceptions import (
from lmstrix.utils.logging import logger

    APIConnectionError,
    ConfigurationError,
    ContextLimitExceededError,
    InferenceError,
    LMStrixError,
    ModelLoadError,
    ModelNotFoundError,
)

__all__ = [
    "APIConnectionError",
    "CompletionResponse",
    "ConfigurationError",
    "ContextLimitExceededError",
    "InferenceError",
    "LMStrixError",
    "LMStudioClient",
    "ModelLoadError",
    "ModelNotFoundError",
]
