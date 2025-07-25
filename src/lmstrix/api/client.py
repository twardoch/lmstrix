"""LM Studio API client for interacting with the local server."""

from typing import Any

import lmstudio
from loguru import logger
from pydantic import BaseModel, Field

from lmstrix.api.exceptions import APIConnectionError, InferenceError, ModelLoadError


class CompletionResponse(BaseModel):
    """Response from a completion request."""

    content: str = Field(..., description="The generated text")
    model: str = Field(..., description="Model used for generation")
    usage: dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    finish_reason: str | None = Field(None, description="Reason for completion termination")


class LMStudioClient:
    """Client for interacting with LM Studio."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the LM Studio client."""
        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def list_models(self) -> list[dict[str, Any]]:
        """List all downloaded models."""
        try:
            models = lmstudio.list_downloaded_models()
            # Convert DownloadedModel objects to dicts
            result = []
            for model in models:
                # Access the info property which contains all model metadata
                info = model.info

                # Handle different attribute names for LLMs vs Embeddings
                model_dict = {
                    "id": getattr(info, "model_key", getattr(info, "modelKey", None)),
                    "path": info.path,
                    "size_bytes": getattr(info, "size_bytes", getattr(info, "sizeBytes", 0)),
                    "context_length": getattr(
                        info,
                        "max_context_length",
                        getattr(info, "maxContextLength", 8192),
                    ),
                    "display_name": getattr(info, "display_name", getattr(info, "displayName", "")),
                    "architecture": info.architecture,
                    "has_tools": getattr(info, "trainedForToolUse", False),
                    "has_vision": getattr(info, "vision", False),
                    "model_type": getattr(info, "type", "llm"),  # 'llm' or 'embedding'
                }
                result.append(model_dict)
            return result
        except Exception as e:
            raise APIConnectionError("local", f"Failed to list models: {e}") from e

    def load_model(self, model_path: str, context_len: int, unload_all: bool = True) -> Any:
        """Load a model with a specific context length using model path."""
        try:
            if unload_all:
                self.unload_all_models()
            # Use Any type for config to avoid type checking issues
            config: Any = {"context_length": context_len}
            return lmstudio.llm(model_path, config=config)
        except Exception as e:
            raise ModelLoadError(model_path, f"Failed to load model: {e}") from e

    def load_model_by_id(self, model_id: str, context_len: int) -> Any:
        """Load a model with a specific context length using model ID (backward compatibility)."""
        try:
            # Use Any type for config to avoid type checking issues
            config: Any = {"context_length": context_len}
            return lmstudio.llm(model_id, config=config)
        except Exception as e:
            raise ModelLoadError(model_id, f"Failed to load model: {e}") from e

    def unload_all_models(self) -> None:
        """Unload all currently loaded models to free up resources."""
        try:
            [llm.unload() for llm in lmstudio.list_loaded_models()]
            logger.info("All models unloaded successfully")
        except Exception as e:
            logger.warning(f"Failed to unload all models: {e}")

    def completion(
        self,
        llm: Any,  # The loaded model object from lmstudio.llm
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = -1,  # -1 for unlimited
        model_id: str | None = None,  # Pass model_id separately since llm object may not have it
        timeout: float = 30.0,  # Timeout in seconds
        **kwargs: Any,
    ) -> CompletionResponse:
        """Make a completion request to a loaded LM Studio model."""
        try:
            # LM Studio's complete() method accepts a config dict
            # Pass maxTokens to prevent models from generating indefinitely
            config = {"maxTokens": max_tokens if max_tokens > 0 else 100}
            logger.debug(f"Calling llm.complete with config: {config}, prompt: {prompt[:50]}...")

            # Direct synchronous call - no threading or async
            response = llm.complete(prompt, config=config)

            # Parse the response - could be PredictionResult or string
            if hasattr(response, "content"):
                content = response.content
            elif hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # Check for empty responses which might indicate a problem
            if not content or not content.strip():
                logger.warning(f"Model {model_id} returned empty response")
                raise InferenceError(
                    model_id or "unknown",
                    "Model returned empty response - may be unresponsive",
                )

            return CompletionResponse(
                content=content,
                model=model_id or "unknown",
                usage={},  # lmstudio doesn't provide usage stats in the same way
                finish_reason="stop",
            )
        except Exception as e:
            # Check for specific error patterns that indicate model issues
            error_str = str(e).lower()
            if "model unloaded" in error_str:
                raise InferenceError(
                    model_id or "unknown",
                    "Model was unloaded during inference - likely due to timeout or crash",
                )
            raise InferenceError(model_id or "unknown", f"Inference failed: {e}") from e
