# this_file: src/lmstrix/api/client.py
"""LM Studio API client for interacting with the local server."""

import os
from typing import Any

import litellm
from litellm import acompletion
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from lmstrix.api.exceptions import APIConnectionError, InferenceError

# Configure litellm for LM Studio
litellm.drop_params = True
litellm.set_verbose = False
litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True

# Set environment variables to suppress litellm output
os.environ["LITELLM_LOG"] = "ERROR"
os.environ["OPENAI_API_KEY"] = "dummy"  # Required by OpenAI client


class CompletionResponse(BaseModel):
    """Response from a completion request."""

    content: str = Field(..., description="The generated text")
    model: str = Field(..., description="Model used for generation")
    usage: dict[str, int] = Field(default_factory=dict, description="Token usage statistics")
    finish_reason: str | None = Field(None, description="Reason for completion termination")


class LMStudioClient:
    """Async client for interacting with LM Studio API."""

    def __init__(self, endpoint: str = "http://localhost:1234/v1", verbose: bool = False):
        """Initialize the LM Studio client."""
        self.endpoint = endpoint.rstrip("/")
        self.verbose = verbose

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def acompletion(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Make an async completion request to LM Studio."""
        try:
            # Try with openai/ prefix first (recommended by litellm docs)
            response = await acompletion(
                model=f"openai/{model_id}",
                messages=messages,
                api_base=self.endpoint,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
        except Exception as e:
            # Fallback to without prefix
            logger.debug(f"OpenAI prefix call failed, trying without prefix: {e}")
            try:
                response = await acompletion(
                    model=model_id,
                    messages=messages,
                    api_base=self.endpoint,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs,
                )
            except Exception as e2:
                if "connection" in str(e2).lower():
                    raise APIConnectionError(
                        self.endpoint,
                        str(e2),
                        {"original_error": str(e), "fallback_error": str(e2)},
                    )
                raise InferenceError(
                    model_id,
                    str(e2),
                    {"original_error": str(e), "fallback_error": str(e2)},
                )

        # Extract response data
        try:
            content = response.choices[0].message.content
            usage = response.usage.dict() if hasattr(response, "usage") else {}
            finish_reason = (
                response.choices[0].finish_reason
                if hasattr(response.choices[0], "finish_reason")
                else None
            )

            return CompletionResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
            )
        except (AttributeError, IndexError) as e:
            raise InferenceError(model_id, f"Invalid response format: {e}")
