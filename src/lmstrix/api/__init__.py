"""API client and exceptions for LMStrix."""

from lmstrix.api.client import CompletionResponse, LMStudioClient
from lmstrix.api.exceptions import (
    APIConnectionError,
    ConfigurationError,
    ContextLimitExceededError,
    InferenceError,
    LMStrixError,
    ModelLoadError,
    ModelNotFoundError,
)
from lmstrix.utils.logging import logger

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
