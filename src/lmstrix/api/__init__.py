# this_file: src/lmstrix/api/__init__.py
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

__all__ = [
    "LMStudioClient",
    "CompletionResponse",
    "LMStrixError",
    "ModelLoadError",
    "InferenceError",
    "APIConnectionError",
    "ContextLimitExceededError",
    "ModelNotFoundError",
    "ConfigurationError",
]
