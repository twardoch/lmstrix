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
                }
                result.append(model_dict)
            return result
        except Exception as e:
            raise APIConnectionError("local", f"Failed to list models: {e}") from e

    def load_model(self, model_id: str, context_len: int) -> Any:
        """Load a model with a specific context length."""
        try:
            # Use Any type for config to avoid type checking issues
            config: Any = {"context_length": context_len}
            return lmstudio.llm(model_id, config=config)
        except Exception as e:
            raise ModelLoadError(model_id, f"Failed to load model: {e}") from e

    async def acompletion(
        self,
        llm: Any,  # The loaded model object from lmstudio.llm
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = -1,  # -1 for unlimited
    ) -> CompletionResponse:
        """Make an async completion request to a loaded LM Studio model."""
        try:
            response = await llm.complete(prompt, temperature=temperature, max_tokens=max_tokens)
            # Assuming the response object has a similar structure to the previous one
            # This might need adjustment based on the actual response from lmstudio.llm.complete
            return CompletionResponse(
                content=response["choices"][0]["text"],
                model=llm.model_id,  # Or however the model id is stored
                usage=response.get("usage", {}),
                finish_reason=response.get("finish_reason"),
            )
        except Exception as e:
            raise InferenceError(llm.model_id, f"Inference failed: {e}") from e
