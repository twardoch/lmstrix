"""LM Studio API client for interacting with the local server."""

import time
from collections.abc import Callable, Iterator
from typing import Any

import lmstudio
from lmstudio import LMStudioServerError
from pydantic import BaseModel, Field

from lmstrix.api.exceptions import APIConnectionError, InferenceError, ModelLoadError
from lmstrix.utils.logging import logger


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
        except Exception as e:
            raise APIConnectionError("local", f"Failed to list models: {e}") from e

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

    def load_model(self, model_path: str, context_len: int, unload_all: bool = True) -> Any:
        """Load a model with a specific context length using model path."""
        try:
            if unload_all:
                self.unload_all_models()
            # Use Any type for config to avoid type checking issues
            # Use camelCase for config keys as expected by lmstudio SDK
            config: Any = {"contextLength": context_len, "flashAttention": True}
            return lmstudio.llm(model_path, config=config)
        except LMStudioServerError as e:
            # Handle specific LM Studio server errors during model loading
            error_message = str(e).lower()
            if "model not found" in error_message or "path not found" in error_message:
                raise ModelLoadError(
                    model_path,
                    f"Model not available in LM Studio (possibly deleted or unloaded): {e}",
                ) from e
            # Generic LM Studio server error during load
            raise ModelLoadError(model_path, f"LM Studio server error during load: {e}") from e
        except (TypeError, ValueError) as e:
            raise ModelLoadError(model_path, f"Failed to load model: {e}") from e

    def load_model_by_id(self, model_id: str, context_len: int) -> Any:
        """Load a model with a specific context length using model ID."""
        try:
            # First, try to find the model in LM Studio's list to get the correct model_key
            downloaded_models = lmstudio.list_downloaded_models()
            model_key = None

            for model in downloaded_models:
                info = model.info
                # Try multiple matching strategies
                lms_model_key = getattr(info, "model_key", getattr(info, "modelKey", ""))
                display_name = getattr(info, "display_name", getattr(info, "displayName", ""))

                # Match by model_key, display_name, or if model_id appears in path
                if model_id in (lms_model_key, display_name) or model_id in str(
                    getattr(info, "path", ""),
                ):
                    model_key = lms_model_key
                    logger.debug(f"Found model match: {model_id} -> {model_key}")
                    break

            if not model_key:
                # Fallback: try the model_id directly
                model_key = model_id
                logger.warning(f"No exact match found for {model_id}, trying directly")

            # Use camelCase for config keys as expected by lmstudio SDK
            config: Any = {"contextLength": int(context_len)}
            return lmstudio.llm(model_key, config=config)
        except Exception as e:
            # Get available models for better error message
            try:
                available_models = [
                    getattr(m.info, "model_key", "unknown")
                    for m in lmstudio.list_downloaded_models()
                ]
                error_msg = (
                    f"Failed to load model '{model_id}'. Available models: {available_models[:5]}"
                )
            except:
                error_msg = f"Failed to load model '{model_id}': {e}"
            raise ModelLoadError(model_id, error_msg) from e

    def get_loaded_models(self) -> list[dict[str, Any]]:
        """Get information about currently loaded models.

        Returns:
            List of dicts with model information including id and context_length
        """
        try:
            loaded = lmstudio.list_loaded_models()
            models_info = []
            for llm in loaded:
                try:
                    # Extract model info from the loaded LLM object
                    model_info = {
                        "id": getattr(llm, "id", "unknown"),
                        "model_key": getattr(llm, "model_key", getattr(llm, "modelKey", "unknown")),
                        "context_length": (
                            getattr(llm.config, "contextLength", None)
                            if hasattr(llm, "config")
                            else None
                        ),
                    }
                    models_info.append(model_info)
                except Exception as e:
                    logger.warning(f"Failed to extract info from loaded model: {e}")
            return models_info
        except Exception as e:
            logger.warning(f"Failed to list loaded models: {e}")
            return []

    def is_model_loaded(self, model_id: str) -> tuple[bool, int | None]:
        """Check if a specific model is currently loaded.

        Args:
            model_id: Model identifier to check

        Returns:
            Tuple of (is_loaded, context_length)
        """
        loaded_models = self.get_loaded_models()
        for model in loaded_models:
            # Check various possible matches
            if model_id in (model.get("id"), model.get("model_key")):
                return True, model.get("context_length")
        return False, None

    def unload_all_models(self) -> None:
        """Unload all currently loaded models to free up resources."""
        try:
            [llm.unload() for llm in lmstudio.list_loaded_models()]
            logger.info("All models unloaded successfully")
        except (TypeError, AttributeError) as e:
            logger.warning(f"Failed to unload all models: {e}")

    def completion(
        self,
        llm: Any,  # The loaded model object from lmstudio.llm
        prompt: str,
        out_ctx: int = -1,  # -1 for unlimited
        temperature: float = 0.8,  # Temperature for generation (LM Studio default)
        model_id: str | None = None,  # Pass model_id separately
        model_context_length: (
            int | None
        ) = None,  # Model's total context length for percentage calculation
        top_k: int = 40,  # topKSampling - controls token sampling diversity
        top_p: float = 0.95,  # topPSampling - nucleus sampling
        repeat_penalty: float = 1.1,  # repeatPenalty - penalty for repeated tokens
        min_p: float = 0.05,  # minPSampling - minimum token probability threshold
        **kwargs: Any,  # Accept additional parameters
    ) -> CompletionResponse:
        """Make a completion request to a loaded LM Studio model."""
        # LM Studio's complete() method accepts a config dict
        # Pass maxTokens (camelCase) to prevent models from generating indefinitely

        # Handle maxTokens - use -1 for unlimited like LM Studio GUI
        max_tokens = out_ctx if out_ctx > 0 else -1

        # Build config with all parameters matching LM Studio
        config = {
            "maxTokens": max_tokens if max_tokens != -1 else None,  # None for unlimited
            "temperature": temperature,
            "topKSampling": top_k,
            "topPSampling": top_p,
            "repeatPenalty": repeat_penalty,
            "minPSampling": min_p,
        }

        # Log comparison with LM Studio defaults
        logger.debug("═" * 60)
        logger.debug("🔍 DIAGNOSTIC: Inference Parameters Comparison")
        logger.debug(f"   Temperature: {temperature} (LM Studio GUI: 0.8)")
        logger.debug(f"   Top K: {top_k} (LM Studio GUI: 20)")
        logger.debug(f"   Top P: {top_p} (LM Studio GUI: 0.95)")
        logger.debug(f"   Min P: {min_p} (LM Studio GUI: 0.05)")
        logger.debug(f"   Repeat Penalty: {repeat_penalty} (LM Studio GUI: 1.1)")
        logger.debug(f"   Max Tokens: {max_tokens} (LM Studio GUI: -1/unlimited)")
        logger.debug(f"   Context Length: {model_context_length} (LM Studio GUI: 131072)")
        logger.debug("═" * 60)

        # Enhanced logging with beautiful formatting
        logger.info("═" * 60)
        logger.info(f"🤖 MODEL: {model_id or 'unknown'}")
        logger.info(
            f"🔧 CONFIG: maxTokens={config['maxTokens']}, temperature={config['temperature']}, "
            f"topK={config['topKSampling']}, topP={config['topPSampling']}, "
            f"minP={config['minPSampling']}, repeatPenalty={config['repeatPenalty']}",
        )

        # Log model context information if available
        if hasattr(llm, "config") and hasattr(llm.config, "contextLength"):
            try:
                # Handle mock objects in tests that don't support formatting
                context_length = llm.config.contextLength
                if isinstance(context_length, int):
                    logger.info(f"📏 CONTEXT: {context_length:,} tokens")
                else:
                    logger.info(f"📏 CONTEXT: {context_length} tokens")
            except (TypeError, ValueError):
                # In case of mock objects or other issues
                logger.info(f"📏 CONTEXT: {llm.config.contextLength} tokens")

        # Log full prompt in verbose mode using stderr to avoid loguru parsing issues
        prompt_lines = prompt.count("\n") + 1
        prompt_chars = len(prompt)
        logger.info(f"📝 Prompt ({prompt_lines} lines, {prompt_chars} chars):")
        # Only print prompt if logger is enabled for debug mode
        if logger._core.handlers:
            logger.debug(f"Prompt content: {prompt}")

        logger.info("═" * 60)

        start_time = time.time()

        try:
            # Direct synchronous call - no threading or async
            # Don't log config dict to avoid format string errors
            logger.debug("Calling llm.complete with provided config")
            response = llm.complete(prompt, config=config)
            # Don't log raw response to avoid tag parsing errors
            logger.debug("Received response from model")

            # Calculate total inference time
            total_inference_time = time.time() - start_time

            # Extract and log performance stats in verbose mode
            if hasattr(response, "stats") and response.stats:
                stats = response.stats
                logger.info("═" * 60)
                logger.info("📊 INFERENCE STATS")

                # Time to first token
                if hasattr(stats, "time_to_first_token_sec"):
                    logger.info(f"⚡ Time to first token: {stats.time_to_first_token_sec:.2f}s")

                # Total inference time
                logger.info(f"⏱️  Total inference time: {total_inference_time:.2f}s")

                # Token counts
                if hasattr(stats, "predicted_tokens_count"):
                    logger.info(f"🔢 Predicted tokens: {stats.predicted_tokens_count:,}")

                if hasattr(stats, "prompt_tokens_count"):
                    logger.info(f"📝 Prompt tokens: {stats.prompt_tokens_count:,}")

                if hasattr(stats, "total_tokens_count"):
                    logger.info(f"🎯 Total tokens: {stats.total_tokens_count:,}")

                # Tokens per second
                if hasattr(stats, "tokens_per_second"):
                    logger.info(f"🚀 Tokens/second: {stats.tokens_per_second:.2f}")

                # Stop reason
                if hasattr(stats, "stop_reason"):
                    logger.info(f"🛑 Stop reason: {stats.stop_reason}")

                logger.info("═" * 60)
        except LMStudioServerError as e:
            # Handle specific LM Studio server errors
            error_message = str(e).lower()
            if (
                "llama_memory is null" in error_message
                or "unable to reuse from cache" in error_message
            ):
                logger.warning(f"Model {model_id} has memory/cache issues: {e}")
                raise InferenceError(
                    model_id or "unknown",
                    f"Model memory/cache error - model may need to be reloaded: {e}",
                ) from e
            if "model not found" in error_message or "no model loaded" in error_message:
                logger.warning(f"Model {model_id} not found or unloaded: {e}")
                raise ModelLoadError(
                    model_id or "unknown",
                    f"Model not available in LM Studio: {e}",
                ) from e
            # Generic LM Studio server error
            logger.error(f"LM Studio server error for {model_id}: {e}")
            raise InferenceError(model_id or "unknown", f"LM Studio server error: {e}") from e
        except (TypeError, AttributeError, ValueError) as e:
            # Check for specific error patterns that indicate model issues
            error_str = str(e).lower()
            if "model unloaded" in error_str:
                raise InferenceError(
                    model_id or "unknown",
                    "Model was unloaded during inference - likely due to timeout or crash",
                ) from e
            raise InferenceError(model_id or "unknown", f"Inference failed: {e}") from e

        # Parse the response - could be PredictionResult, dict, or string
        if hasattr(response, "content"):
            content = response.content
        elif hasattr(response, "text"):
            content = response.text
        elif isinstance(response, dict):
            # Handle dict response format (common in tests)
            if response.get("choices"):
                content = response["choices"][0].get("text", "")
            else:
                content = str(response)
        else:
            content = str(response)

        # Check for empty responses which might indicate a problem
        if not content or not content.strip():
            logger.warning(f"Model {model_id} returned empty response")
            raise InferenceError(
                model_id or "unknown",
                "Model returned empty response - may be unresponsive",
            )

        # Extract usage stats if available
        usage = {}
        if isinstance(response, dict) and "usage" in response:
            usage = response.get("usage", {})

        # Extract model if available from response
        response_model = model_id or "unknown"
        if isinstance(response, dict) and "model" in response:
            response_model = response.get("model", response_model)

        return CompletionResponse(
            content=content,
            model=response_model,
            usage=usage,
            finish_reason="stop",
        )

    def stream_completion(
        self,
        llm: Any,  # The loaded model object from lmstudio.llm
        prompt: str,
        out_ctx: int = -1,  # -1 for unlimited
        temperature: float = 0.8,  # Temperature for generation (LM Studio default)
        model_id: str | None = None,  # Pass model_id separately
        model_context_length: (
            int | None
        ) = None,  # Model's total context length for percentage calculation
        top_k: int = 40,  # topKSampling - controls token sampling diversity
        top_p: float = 0.95,  # topPSampling - nucleus sampling
        repeat_penalty: float = 1.1,  # repeatPenalty - penalty for repeated tokens
        min_p: float = 0.05,  # minPSampling - minimum token probability threshold
        on_token: Callable[[str], None] | None = None,  # Callback for each token
        stream_timeout: int = 120,  # Timeout in seconds for no progress
        **kwargs: Any,  # Accept additional parameters
    ) -> Iterator[str]:
        """Stream a completion request to a loaded LM Studio model."""
        # Handle maxTokens - use -1 for unlimited like LM Studio GUI
        max_tokens = out_ctx if out_ctx > 0 else -1

        # Build config with all parameters matching LM Studio
        config = {
            "maxTokens": max_tokens if max_tokens != -1 else None,  # None for unlimited
            "temperature": temperature,
            "topKSampling": top_k,
            "topPSampling": top_p,
            "repeatPenalty": repeat_penalty,
            "minPSampling": min_p,
        }

        # Log comparison with LM Studio defaults
        logger.debug("═" * 60)
        logger.debug("🔍 DIAGNOSTIC: Streaming Inference Parameters")
        logger.debug(f"   Temperature: {temperature} (LM Studio GUI: 0.8)")
        logger.debug(f"   Top K: {top_k} (LM Studio GUI: 20)")
        logger.debug(f"   Top P: {top_p} (LM Studio GUI: 0.95)")
        logger.debug(f"   Min P: {min_p} (LM Studio GUI: 0.05)")
        logger.debug(f"   Repeat Penalty: {repeat_penalty} (LM Studio GUI: 1.1)")
        logger.debug(f"   Max Tokens: {max_tokens} (LM Studio GUI: -1/unlimited)")
        logger.debug(f"   Stream Timeout: {stream_timeout}s")
        logger.debug("═" * 60)

        # Enhanced logging with beautiful formatting
        logger.info("═" * 60)
        logger.info(f"🤖 MODEL: {model_id or 'unknown'} (streaming)")
        logger.info(
            f"🔧 CONFIG: maxTokens={config['maxTokens']}, temperature={config['temperature']}, "
            f"topK={config['topKSampling']}, topP={config['topPSampling']}, "
            f"minP={config['minPSampling']}, repeatPenalty={config['repeatPenalty']}",
        )

        # Log model context information if available
        if hasattr(llm, "config") and hasattr(llm.config, "contextLength"):
            try:
                context_length = llm.config.contextLength
                if isinstance(context_length, int):
                    logger.info(f"📏 CONTEXT: {context_length:,} tokens")
                else:
                    logger.info(f"📏 CONTEXT: {context_length} tokens")
            except (TypeError, ValueError):
                logger.info(f"📏 CONTEXT: {llm.config.contextLength} tokens")

        # Log full prompt in verbose mode using stderr to avoid loguru parsing issues
        prompt_lines = prompt.count("\n") + 1
        prompt_chars = len(prompt)
        logger.info(f"📝 Prompt ({prompt_lines} lines, {prompt_chars} chars):")
        # Only print prompt if logger is enabled for debug mode
        if logger._core.handlers:
            logger.debug(f"Prompt content: {prompt}")

        logger.info("═" * 60)

        start_time = time.time()
        last_token_time = start_time
        token_count = 0
        collected_tokens = []

        def handle_token(token: str) -> None:
            """Handle incoming token from stream."""
            nonlocal last_token_time, token_count
            last_token_time = time.time()
            token_count += 1
            collected_tokens.append(token)

            # Call user's callback if provided
            if on_token:
                on_token(token)

        def handle_first_token(elapsed_seconds: float) -> None:
            """Handle first token event."""
            logger.info(f"⚡ First token received after {elapsed_seconds:.2f}s")

        try:
            # Create streaming completion with callbacks
            logger.debug("Starting streaming completion")
            stream = llm.complete_stream(
                prompt,
                config=config,
                on_prediction_fragment=handle_token,
                on_first_token=handle_first_token,
            )

            # Iterate through the stream with timeout monitoring
            for fragment in stream:
                # Check for timeout
                if time.time() - last_token_time > stream_timeout:
                    logger.warning(f"Stream timeout - no tokens for {stream_timeout}s")
                    raise InferenceError(
                        model_id or "unknown",
                        f"Stream timeout - no tokens received for {stream_timeout} seconds",
                    )

                # Yield the fragment
                yield fragment

            # Calculate total stats
            total_time = time.time() - start_time
            tokens_per_second = token_count / total_time if total_time > 0 else 0

            logger.info("═" * 60)
            logger.info("📊 STREAMING INFERENCE STATS")
            logger.info(f"⏱️  Total inference time: {total_time:.2f}s")
            logger.info(f"🔢 Total tokens: {token_count:,}")
            logger.info(f"🚀 Tokens/second: {tokens_per_second:.2f}")
            logger.info("═" * 60)

        except LMStudioServerError as e:
            # Handle specific LM Studio server errors
            error_message = str(e).lower()
            if (
                "llama_memory is null" in error_message
                or "unable to reuse from cache" in error_message
            ):
                logger.warning(f"Model {model_id} has memory/cache issues: {e}")
                raise InferenceError(
                    model_id or "unknown",
                    f"Model memory/cache error - model may need to be reloaded: {e}",
                ) from e
            if "model not found" in error_message or "no model loaded" in error_message:
                logger.warning(f"Model {model_id} not found or unloaded: {e}")
                raise ModelLoadError(
                    model_id or "unknown",
                    f"Model not available in LM Studio: {e}",
                ) from e
            # Generic LM Studio server error
            logger.error(f"LM Studio server error for {model_id}: {e}")
            raise InferenceError(model_id or "unknown", f"LM Studio server error: {e}") from e
        except (TypeError, AttributeError, ValueError) as e:
            # Check for specific error patterns that indicate model issues
            error_str = str(e).lower()
            if "model unloaded" in error_str:
                raise InferenceError(
                    model_id or "unknown",
                    "Model was unloaded during inference - likely due to timeout or crash",
                ) from e
            raise InferenceError(model_id or "unknown", f"Streaming inference failed: {e}") from e
