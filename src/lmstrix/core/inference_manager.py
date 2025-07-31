"""Unified inference manager for LMStrix.

This module consolidates inference logic from cli/main.py and core/inference.py
into a single, streamlined interface.
"""
# this_file: src/lmstrix/core/inference_manager.py

import builtins
import contextlib
import time
from typing import Any

from lmstrix.api.client import LMStudioClient
from lmstrix.api.exceptions import ModelNotFoundError
from lmstrix.core.models import Model, ModelRegistry
from lmstrix.utils.logging import logger


class InferenceManager:
    """Unified manager for model inference operations."""

    def __init__(
        self,
        client: LMStudioClient | None = None,
        registry: ModelRegistry | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize the inference manager.

        Args:
            client: LMStudio client instance (creates one if not provided)
            registry: Model registry instance (creates one if not provided)
            verbose: Enable verbose logging
        """
        self.client = client or LMStudioClient(verbose=verbose)
        self.registry = registry or ModelRegistry()
        self.verbose = verbose

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def infer(
        self,
        model_id: str,
        prompt: str,
        in_ctx: int | None = None,
        out_ctx: int = -1,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run inference on a model.

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
            Dictionary with inference results:
                - model_id: str
                - prompt: str
                - response: str
                - tokens_used: int
                - inference_time: float
                - error: str | None
                - succeeded: bool
        """
        # Find model in registry
        model = self.registry.find_model(model_id)
        if not model:
            available = [m.id for m in self.registry.list_models()]
            raise ModelNotFoundError(model_id, available)

        start_time = time.time()
        llm = None
        should_unload_after = False

        # Check if model is already loaded
        is_loaded, loaded_context = self.client.is_model_loaded(model_id)

        # Determine loading strategy
        if in_ctx is not None:
            # Explicit context specified - always reload
            logger.info(f"Explicit context specified: {in_ctx}")
            if is_loaded:
                logger.info(f"Model currently loaded with context {loaded_context:,}, will reload")
                try:
                    import lmstudio

                    lmstudio.unload()
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Failed to unload existing models: {e}")

            context_to_use = None if in_ctx == 0 else in_ctx
            should_unload_after = True  # Only unload if explicitly loaded with context
        # No explicit context - try to reuse or load optimal
        elif is_loaded:
            logger.info(f"Model already loaded with context {loaded_context:,}, reusing...")
            context_to_use = None  # Signal to skip loading
            should_unload_after = False  # Keep model loaded for subsequent calls
        else:
            context_to_use = model.tested_max_context or model.context_limit
            logger.info(f"Loading with optimal context {context_to_use:,}...")
            should_unload_after = False  # Keep model loaded for subsequent calls

        try:
            # Load model if needed
            if context_to_use is not None or not is_loaded:
                if context_to_use == 0:
                    # Load without specific context
                    import lmstudio

                    llm = lmstudio.llm(model.id)
                else:
                    llm = self.client.load_model_by_id(
                        model_id,
                        context_to_use or (model.tested_max_context or model.context_limit),
                    )
            else:
                # Get reference to already loaded model
                import lmstudio

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
                    # Fallback: load anyway
                    logger.warning("Could not find reference to loaded model, loading anyway...")
                    llm = self.client.load_model_by_id(
                        model_id,
                        model.tested_max_context or model.context_limit,
                    )

            # Run inference
            logger.info(f"Running inference on model {model_id}")
            response = self.client.completion(
                llm=llm,
                prompt=prompt,
                out_ctx=out_ctx,
                temperature=temperature,
                model_id=model_id,
                model_context_length=model.tested_max_context or model.context_limit,
                **kwargs,
            )

            inference_time = time.time() - start_time
            tokens_used = response.usage.get("total_tokens", 0)

            return {
                "model_id": model_id,
                "prompt": prompt,
                "response": response.content,
                "tokens_used": tokens_used,
                "inference_time": inference_time,
                "error": None,
                "succeeded": True,
            }

        except Exception as e:
            error_str = str(e)
            logger.error(f"Inference failed for model {model_id}: {error_str}")

            # Check for OOM error and attempt recovery
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

            if is_oom_error and model.tested_max_context:
                logger.warning("OOM error detected, retrying with reduced context...")
                reduced_context = int(model.tested_max_context * 0.8)

                try:
                    # Unload and retry
                    if llm:
                        with contextlib.suppress(builtins.BaseException):
                            llm.unload()

                    llm = self.client.load_model_by_id(model_id, reduced_context)
                    response = self.client.completion(
                        llm=llm,
                        prompt=prompt,
                        out_ctx=out_ctx,
                        temperature=temperature,
                        model_id=model_id,
                        **kwargs,
                    )

                    return {
                        "model_id": model_id,
                        "prompt": prompt,
                        "response": response.content,
                        "tokens_used": response.usage.get("total_tokens", 0),
                        "inference_time": time.time() - start_time,
                        "error": None,
                        "succeeded": True,
                    }
                except Exception as retry_e:
                    error_str = f"Even with reduced context: {retry_e}"

            return {
                "model_id": model_id,
                "prompt": prompt,
                "response": "",
                "tokens_used": 0,
                "inference_time": time.time() - start_time,
                "error": error_str,
                "succeeded": False,
            }

        finally:
            # Only unload if we explicitly loaded with in_ctx
            if llm and should_unload_after:
                try:
                    logger.info(f"Unloading model {model_id}...")
                    llm.unload()
                except Exception as e:
                    logger.warning(f"Failed to unload model: {e}")

    def test_inference_capability(self, model: Model, context_len: int) -> tuple[bool, str]:
        """Test if model can do basic inference at given context length.

        Args:
            model: Model to test
            context_len: Context length to test

        Returns:
            Tuple of (success, response_or_error)
        """
        llm = None
        try:
            llm = self.client.load_model_by_id(model.id, context_len)

            # Test 1: Number words to digits
            test_prompt_1 = "Write 'ninety-six' as a number using only digits"
            response_1 = self.client.completion(
                llm=llm,
                prompt=test_prompt_1,
                out_ctx=10,
                temperature=0.1,
            )

            test_1_pass = "96" in response_1.content

            # Test 2: Simple arithmetic
            test_prompt_2 = "2+3="
            response_2 = self.client.completion(
                llm=llm,
                prompt=test_prompt_2,
                out_ctx=10,
                temperature=0.1,
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
            if llm:
                try:
                    llm.unload()
                    logger.debug(f"Successfully unloaded model {model.id}")
                except Exception as e:
                    logger.warning(f"Failed to unload model {model.id}: {e}")
