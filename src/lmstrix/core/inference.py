# this_file: src/lmstrix/core/inference.py
"""Inference engine for running models."""

import time
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from lmstrix.api.client import LMStudioClient
from lmstrix.api.exceptions import ModelNotFoundError
from lmstrix.core.models import ModelRegistry


class InferenceResult(BaseModel):
    """Result from an inference run."""

    model_id: str = Field(..., description="ID of the model used")
    prompt: str = Field(..., description="The input prompt")
    response: str = Field(..., description="The generated response")
    tokens_used: int = Field(0, description="Total tokens used")
    inference_time: float = Field(0.0, description="Time taken for inference in seconds")
    error: str | None = Field(None, description="Error message if inference failed")

    @property
    def succeeded(self) -> bool:
        """Check if the inference was successful."""
        return self.error is None and bool(self.response)


class InferenceEngine:
    """Engine for running inference on models."""

    def __init__(
        self,
        client: LMStudioClient | None = None,
        model_registry: ModelRegistry | None = None,
        verbose: bool = False,
    ):
        """Initialize the inference engine."""
        self.client = client or LMStudioClient(verbose=verbose)
        self.registry = model_registry or ModelRegistry()
        self.verbose = verbose

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    async def infer(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = -1,  # Use -1 for unlimited as per new client
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> InferenceResult:
        """Run inference on a model."""
        model = self.registry.get_model(model_id)
        if not model:
            available = list(self.registry._models.keys())
            raise ModelNotFoundError(model_id, available)

        start_time = time.time()
        llm = None
        try:
            # Use tested context limit if available, otherwise fallback to declared limit
            context_len = model.tested_max_context or model.context_limit
            logger.info(f"Loading model {model_id} with context length {context_len}...")
            llm = self.client.load_model(model_id, context_len=context_len)

            logger.info(f"Running inference on model {model_id}")
            response = await self.client.acompletion(
                llm=llm,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            inference_time = time.time() - start_time
            tokens_used = response.usage.get("total_tokens", 0)

            return InferenceResult(
                model_id=model_id,
                prompt=prompt,
                response=response.content,
                tokens_used=tokens_used,
                inference_time=inference_time,
            )

        except Exception as e:
            logger.error(f"Inference failed for model {model_id}: {e}")
            return InferenceResult(
                model_id=model_id,
                prompt=prompt,
                response="",
                inference_time=time.time() - start_time,
                error=str(e),
            )
        finally:
            if llm:
                logger.info(f"Unloading model {model_id}...")
                llm.unload()
