"""Inference engine for running models."""

import time
from collections.abc import Callable, Iterator
from typing import Any

import lmstudio
from pydantic import BaseModel, Field

from lmstrix.api.client import LMStudioClient
from lmstrix.api.exceptions import ModelNotFoundError
from lmstrix.core.models import ModelRegistry
from lmstrix.utils.logging import logger


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
    ) -> None:
        """Initialize the inference engine."""
        self.client = client or LMStudioClient(verbose=verbose)
        self.registry = model_registry or ModelRegistry()
        self.verbose = verbose

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def _test_inference_capability(self, model_id: str, context_len: int) -> tuple[bool, str]:
        """Test if model can do basic inference at given context length.

        Args:
            model_id: Model identifier
            context_len: Context length to test

        Returns:
            Tuple of (success, response_or_error)
        """
        llm = None
        try:
            llm = self.client.load_model_by_id(model_id, context_len=context_len)

            # Test 1: Number words to digits
            test_prompt_1 = "Write 'ninety-six' as a number using only digits"
            response_1 = self.client.completion(
                llm=llm,
                prompt=test_prompt_1,
                out_ctx=10,
                temperature=0.1,
                model_id=model_id,
            )

            test_1_pass = "96" in response_1.content

            # Test 2: Simple arithmetic
            test_prompt_2 = "2+3="
            response_2 = self.client.completion(
                llm=llm,
                prompt=test_prompt_2,
                out_ctx=10,
                temperature=0.1,
                model_id=model_id,
            )

            test_2_pass = "5" in response_2.content

            # Success if ANY test passes
            success = test_1_pass or test_2_pass

            test1_status = "✓" if test_1_pass else "✗"
            test2_status = "✓" if test_2_pass else "✗"
            combined_response = (
                f"Test1: '{response_1.content.strip()}' ({test1_status}), "
                f"Test2: '{response_2.content.strip()}' ({test2_status})"
            )

            return success, combined_response

        except Exception as e:
            return False, str(e)
        finally:
            # Always unload model regardless of success/failure
            if llm:
                try:
                    llm.unload()
                    logger.debug(f"Successfully unloaded model {model_id}")
                except Exception as unload_e:
                    logger.warning(f"Failed to unload model {model_id}: {unload_e}")

    def _find_working_context(self, model_id: str, initial_context: int) -> int:
        """Find the maximum working context length for a model.

        Args:
            model_id: Model identifier
            initial_context: Starting context length

        Returns:
            Working context length (0 if none found)
        """
        current_context = initial_context
        min_context = 2047

        logger.info(
            f"Testing inference capability for {model_id} starting at {current_context:,} tokens",
        )

        while current_context >= min_context:
            logger.info(f"Testing context length: {current_context:,} tokens")

            success, result = self._test_inference_capability(model_id, current_context)

            if success:
                logger.info(f"✓ Model {model_id} works at {current_context:,} tokens")
                logger.info(f"Test response: '{result}'")
                return current_context
            is_oom_error = any(
                phrase in result.lower()
                for phrase in [
                    "insufficient memory",
                    "out of memory",
                    "oom",
                    "metal error",
                    "cuda out of memory",
                ]
            )

            if is_oom_error:
                logger.warning(f"✗ OOM error at {current_context:,} tokens, reducing by 10%")
                current_context = int(current_context * 0.9)
            else:
                logger.warning(f"✗ Inference failed at {current_context:,} tokens: {result}")
                # For non-OOM errors, try smaller context anyway
                current_context = int(current_context * 0.8)

        logger.error(f"Model {model_id} failed at all tested context lengths down to {min_context}")
        return 0

    def infer(
        self,
        model_id: str,
        prompt: str,
        in_ctx: int | None = None,
        out_ctx: int = -1,  # Use -1 for unlimited as per new client
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> InferenceResult:
        """Run inference on a model with automatic context optimization.

        Args:
            model_id: Model identifier
            prompt: Text prompt for the model
            in_ctx: Context size at which to load the model.
                   If 0, load without specified context.
                   If None, reuse existing loaded model if available.
            out_ctx: Maximum tokens to generate (-1 for unlimited)
            temperature: Sampling temperature
            **kwargs: Additional arguments passed to completion

        Returns:
            InferenceResult with response or error
        """
        model = self.registry.find_model(model_id)
        if not model:
            available = [m.id for m in self.registry.list_models()]
            raise ModelNotFoundError(model_id, available)

        start_time = time.time()
        llm = None
        should_unload_after = False
        model_was_reused = False

        # Check if model is already loaded
        is_loaded, loaded_context = self.client.is_model_loaded(model_id)

        # Determine context size based on in_ctx parameter
        if in_ctx is not None:
            # Explicit context specified - always unload existing and reload
            logger.info(f"Explicit context specified: {in_ctx}")
            if is_loaded:
                logger.info(
                    f"Model currently loaded with context {loaded_context:,}, will reload with new context",
                )

            try:
                # Unload all models first when explicit context is specified
                logger.info("Unloading all models before loading with specific context...")
                lmstudio.unload()
                time.sleep(0.5)  # Brief pause after unload
            except Exception as e:
                logger.warning(f"Failed to unload existing models: {e}")

            if in_ctx == 0:
                # Load without specified context (use model's default)
                logger.info(
                    f"Loading model {model_id} without specified context (using default)...",
                )
                context_to_use = None
            else:
                # Validate context size
                if in_ctx > model.context_limit:
                    logger.warning(
                        f"Requested context {in_ctx:,} exceeds model's declared limit {model.context_limit:,}",
                    )
                    logger.warning("This may cause loading to fail or performance issues")

                if model.tested_max_context and in_ctx > model.tested_max_context:
                    logger.warning(
                        f"Requested context {in_ctx:,} exceeds tested maximum {model.tested_max_context:,}",
                    )
                    logger.info("Consider using the tested maximum for best results")

                # Load with specific context
                logger.info(f"Loading model {model_id} with context length {in_ctx:,}...")
                context_to_use = in_ctx
            should_unload_after = True  # Always unload after when explicit context specified
        else:
            # No explicit context - try to reuse existing or load with optimal context
            logger.info("No explicit context specified, checking if model already loaded...")

            if is_loaded:
                # Model already loaded - reuse it
                logger.info(
                    f"Model {model_id} already loaded with context {loaded_context:,}, reusing...",
                )
                model_was_reused = True
                # We'll skip loading and use the existing model
                context_to_use = None  # Signal to skip loading
            else:
                # Model not loaded - load with optimal context
                context_to_use = model.tested_max_context or model.context_limit
                logger.info(f"Model not loaded, loading with optimal context {context_to_use:,}...")

        try:
            if model_was_reused:
                # Model already loaded, get a reference to it
                # Note: We need to get the loaded model reference
                loaded_models = lmstudio.list_loaded_models()
                logger.debug(f"Found {len(loaded_models)} loaded models, searching for {model.id}")

                for loaded_llm in loaded_models:
                    # Try multiple matching strategies for better model identification
                    llm_id = getattr(loaded_llm, "id", "")
                    llm_model_key = getattr(loaded_llm, "model_key", "")

                    logger.debug(
                        f"Checking loaded model: id='{llm_id}', model_key='{llm_model_key}'",
                    )

                    # Match by exact ID or model_key, or if model.id appears in either
                    if (
                        model.id in (llm_id, llm_model_key)
                        or model.id in llm_id
                        or model.id in llm_model_key
                    ):
                        llm = loaded_llm
                        logger.info(f"✓ Found matching loaded model: {llm_id or llm_model_key}")
                        break

                if llm is None:
                    # Fallback: couldn't find the loaded model, load it anyway
                    logger.warning("Could not find reference to loaded model, loading anyway...")
                    context_to_use = model.tested_max_context or model.context_limit
                    llm = self.client.load_model_by_id(model.id, context_len=context_to_use)
                    model_was_reused = False  # Mark as not reused since we had to load it
            elif context_to_use is None and in_ctx == 0:
                # Load without context specification (for in_ctx=0 case)
                llm = lmstudio.llm(model.id)
            else:
                # Normal loading with context
                llm = self.client.load_model_by_id(model.id, context_len=context_to_use)

            logger.info(f"Running inference on model {model_id}")
            response = self.client.completion(
                llm=llm,
                prompt=prompt,
                out_ctx=out_ctx,
                temperature=temperature,
                model_id=model_id,
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
                error=None,
            )

        except Exception as e:
            error_str = str(e)
            is_oom_error = any(
                phrase in error_str.lower()
                for phrase in [
                    "insufficient memory",
                    "out of memory",
                    "oom",
                    "metal error",
                    "cuda out of memory",
                ]
            )

            if is_oom_error:
                logger.warning(
                    f"OOM error during inference for {model_id}, finding working context...",
                )

                # Find working context length
                working_context = self._find_working_context(
                    model.id,
                    context_to_use or model.context_limit,
                )

                if working_context > 0:
                    # Update the model's tested context in the registry
                    model.tested_max_context = working_context
                    self.registry.update_model_by_id(model)
                    logger.info(f"Updated {model_id} tested_max_context to {working_context:,}")

                    # Try inference again with working context
                    try:
                        # Unload any existing model first
                        if llm:
                            try:
                                llm.unload()
                                logger.debug("Unloaded previous model instance")
                            except:
                                pass

                        llm = self.client.load_model_by_id(model.id, context_len=working_context)
                        response = self.client.completion(
                            llm=llm,
                            prompt=prompt,
                            out_ctx=out_ctx,
                            temperature=temperature,
                            model_id=model_id,
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
                            error=None,
                        )

                    except Exception as retry_e:
                        logger.error(f"Even with reduced context, inference failed: {retry_e}")
                        error_str = str(retry_e)
                else:
                    # No working context found, mark model as having 0 tested context
                    model.tested_max_context = 0
                    self.registry.update_model_by_id(model)
                    logger.error(f"Model {model_id} has no working context length, marked as 0")

            logger.error(f"Inference failed for model {model_id}: {error_str}")
            return InferenceResult(
                model_id=model_id,
                prompt=prompt,
                response="",
                tokens_used=0,
                inference_time=time.time() - start_time,
                error=error_str,
            )

        finally:
            # Only unload if we explicitly loaded with in_ctx
            if llm and should_unload_after:
                try:
                    logger.info(f"Unloading model {model_id} (was loaded with explicit context)...")
                    llm.unload()
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Failed to unload model: {e}")

    def stream_infer(
        self,
        model_id: str,
        prompt: str,
        in_ctx: int | None = None,
        out_ctx: int = -1,  # Use -1 for unlimited as per new client
        temperature: float = 0.7,
        on_token: Callable[[str], None] | None = None,  # Callback for each token
        stream_timeout: int = 120,  # Timeout in seconds
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream inference on a model with automatic context optimization.

        Args:
            model_id: Model identifier
            prompt: Text prompt for the model
            in_ctx: Context size at which to load the model.
                   If 0, load without specified context.
                   If None, reuse existing loaded model if available.
            out_ctx: Maximum tokens to generate (-1 for unlimited)
            temperature: Sampling temperature
            on_token: Optional callback for each token
            stream_timeout: Timeout in seconds for no progress
            **kwargs: Additional arguments passed to stream completion

        Yields:
            String tokens as they are generated
        """
        model = self.registry.find_model(model_id)
        if not model:
            available = [m.id for m in self.registry.list_models()]
            raise ModelNotFoundError(model_id, available)

        time.time()
        llm = None
        should_unload_after = False
        model_was_reused = False

        # Check if model is already loaded
        is_loaded, loaded_context = self.client.is_model_loaded(model_id)

        # Determine context size based on in_ctx parameter
        if in_ctx is not None:
            # Explicit context specified - always unload existing and reload
            logger.info(f"Explicit context specified: {in_ctx}")
            if is_loaded:
                logger.info(
                    f"Model currently loaded with context {loaded_context:,}, will reload with new context",
                )

            try:
                # Unload all models first when explicit context is specified
                logger.info("Unloading all models before loading with specific context...")
                lmstudio.unload()
                time.sleep(0.5)  # Brief pause after unload
            except Exception as e:
                logger.warning(f"Failed to unload existing models: {e}")

            if in_ctx == 0:
                # Load without specified context (use model's default)
                logger.info(
                    f"Loading model {model_id} without specified context (using default)...",
                )
                context_to_use = None
            else:
                # Validate context size
                if in_ctx > model.context_limit:
                    logger.warning(
                        f"Requested context {in_ctx:,} exceeds model's declared limit {model.context_limit:,}",
                    )
                    logger.warning("This may cause loading to fail or performance issues")

                if model.tested_max_context and in_ctx > model.tested_max_context:
                    logger.warning(
                        f"Requested context {in_ctx:,} exceeds tested maximum {model.tested_max_context:,}",
                    )
                    logger.info("Consider using the tested maximum for best results")

                # Load with specific context
                logger.info(f"Loading model {model_id} with context length {in_ctx:,}...")
                context_to_use = in_ctx
            should_unload_after = True  # Always unload after when explicit context specified
        else:
            # No explicit context - try to reuse existing or load with optimal context
            logger.info("No explicit context specified, checking if model already loaded...")

            if is_loaded:
                # Model already loaded - reuse it
                logger.info(
                    f"Model {model_id} already loaded with context {loaded_context:,}, reusing...",
                )
                model_was_reused = True
                # We'll skip loading and use the existing model
                context_to_use = None  # Signal to skip loading
            else:
                # Model not loaded - load with optimal context
                context_to_use = model.tested_max_context or model.context_limit
                logger.info(f"Model not loaded, loading with optimal context {context_to_use:,}...")

        try:
            if model_was_reused:
                # Model already loaded, get a reference to it
                loaded_models = lmstudio.list_loaded_models()
                logger.debug(f"Found {len(loaded_models)} loaded models, searching for {model.id}")

                for loaded_llm in loaded_models:
                    # Try multiple matching strategies for better model identification
                    llm_id = getattr(loaded_llm, "id", "")
                    llm_model_key = getattr(loaded_llm, "model_key", "")

                    logger.debug(
                        f"Checking loaded model: id='{llm_id}', model_key='{llm_model_key}'",
                    )

                    # Match by exact ID or model_key, or if model.id appears in either
                    if (
                        model.id in (llm_id, llm_model_key)
                        or model.id in llm_id
                        or model.id in llm_model_key
                    ):
                        llm = loaded_llm
                        logger.info(f"✓ Found matching loaded model: {llm_id or llm_model_key}")
                        break

                if llm is None:
                    # Fallback: couldn't find the loaded model, load it anyway
                    logger.warning("Could not find reference to loaded model, loading anyway...")
                    context_to_use = model.tested_max_context or model.context_limit
                    llm = self.client.load_model_by_id(model.id, context_len=context_to_use)
                    model_was_reused = False  # Mark as not reused since we had to load it
            elif context_to_use is None and in_ctx == 0:
                # Load without context specification (for in_ctx=0 case)
                llm = lmstudio.llm(model.id)
            else:
                # Normal loading with context
                llm = self.client.load_model_by_id(model.id, context_len=context_to_use)

            logger.info(f"Running streaming inference on model {model_id}")

            # Stream tokens using the client's stream_completion method
            yield from self.client.stream_completion(
                llm=llm,
                prompt=prompt,
                out_ctx=out_ctx,
                temperature=temperature,
                model_id=model_id,
                on_token=on_token,
                stream_timeout=stream_timeout,
                **kwargs,
            )

        except Exception as e:
            logger.error(f"Streaming inference failed for model {model_id}: {e}")
            raise

        finally:
            # Only unload if we explicitly loaded with in_ctx
            if llm and should_unload_after:
                try:
                    logger.info(f"Unloading model {model_id} (was loaded with explicit context)...")
                    llm.unload()
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Failed to unload model: {e}")
