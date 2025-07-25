"""Context testing functionality for discovering true model limits."""

import asyncio
import json
import math
from datetime import datetime
from pathlib import Path

from loguru import logger

from lmstrix.api import LMStudioClient
from lmstrix.api.exceptions import ModelLoadError
from lmstrix.core.models import ContextTestStatus, Model
from lmstrix.loaders.model_loader import load_model_registry, save_model_registry
from lmstrix.utils import get_context_test_log_path


class ContextTestResult:
    """Result of a context test attempt."""

    def __init__(
        self,
        context_size: int,
        load_success: bool,
        inference_success: bool = False,
        prompt: str = "",
        response: str = "",
        error: str = "",
    ) -> None:
        """Initialize test result."""
        self.timestamp = datetime.now()
        self.context_size = context_size
        self.load_success = load_success
        self.inference_success = inference_success
        self.prompt = prompt
        self.response = response
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "context_size": self.context_size,
            "load_success": self.load_success,
            "inference_success": self.inference_success,
            "prompt": self.prompt,
            "response": self.response,
            "error": self.error,
        }

    def is_valid_response(self, expected: str = "") -> bool:
        """Check if we got any response at all (not validating content)."""
        # We consider any non-empty response as valid
        # Manual review will determine quality
        return bool(self.response.strip())


class ContextTester:
    """Tests models to find their true operational context limits.

    Uses a smart binary search algorithm to efficiently discover the maximum context
    size that a model can reliably handle. The test starts with a moderate context (128)
    to verify the model loads and can generate responses, then searches for the
    maximum working context. Progress is saved after each test to allow resuming if interrupted.

    A context is considered "good" if the model loads AND generates any response.
    A context is considered "bad" if the model fails to load OR crashes during inference.
    All responses are logged for manual review - no content validation is performed.

    Attributes:
        client: LMStudioClient instance for model operations.
        test_prompt: The prompt used for testing (default: "Say hello").
    """

    def __init__(self, client: LMStudioClient | None = None, verbose: bool = False) -> None:
        """Initialize context tester.

        Args:
            client: LMStudioClient instance for model operations.
            verbose: Enable verbose logging output.
        """
        self.client = client or LMStudioClient()
        self.test_prompt = "Say hello"
        self.verbose = verbose

    def _log_result(self, log_path: Path, result: ContextTestResult) -> None:
        """Append test result to log file."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    async def _test_at_context(
        self,
        model_id: str,
        context_size: int,
        log_path: Path,
    ) -> ContextTestResult:
        """Test model at a specific context size."""
        logger.debug(f"Testing {model_id} at context size {context_size}")

        if self.verbose:
            logger.info(
                f"[Context Test] Loading model '{model_id}' with context size: {context_size:,} tokens",
            )

        llm = None
        try:
            # Add a small delay to avoid rapid operations
            await asyncio.sleep(0.5)

            llm = self.client.load_model(model_id, context_len=context_size)
            logger.debug(f"Model {model_id} loaded successfully at {context_size}.")

            if self.verbose:
                logger.info("[Context Test] ✓ Model loaded successfully, attempting inference...")

            response = await self.client.acompletion(
                llm=llm,
                prompt=self.test_prompt,
                max_tokens=10,
                model_id=model_id,
            )

            if self.verbose:
                logger.info(
                    f"[Context Test] ✓ Inference successful! Response length: {len(response.content)} chars",
                )
                logger.debug(
                    f"[Context Test] Response: {response.content[:50]}..."
                    if len(response.content) > 50
                    else f"[Context Test] Response: {response.content}",
                )

            result = ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=True,
                prompt=self.test_prompt,
                response=response.content,
            )

        except ModelLoadError as e:
            logger.warning(f"Failed to load {model_id} at context {context_size}: {e}")

            if self.verbose:
                logger.info(f"[Context Test] ✗ Model failed to load at context {context_size:,}")
                logger.debug(f"[Context Test] Load error: {e!s}")

            result = ContextTestResult(
                context_size=context_size,
                load_success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Inference failed for {model_id} at context {context_size}: {e}")

            if self.verbose:
                logger.info(f"[Context Test] ✗ Inference failed at context {context_size:,}")
                logger.debug(f"[Context Test] Inference error: {e!s}")

            result = ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=False,
                prompt=self.test_prompt,
                error=str(e),
            )
        finally:
            if llm:
                if self.verbose:
                    logger.debug("[Context Test] Unloading model...")
                llm.unload()
                logger.debug(f"Model {model_id} unloaded.")
                # Add delay after unload to ensure clean state
                await asyncio.sleep(0.5)

        self._log_result(log_path, result)
        return result

    async def test_model(
        self,
        model: Model,
        min_context: int = 128,
        max_context: int | None = None,
        registry=None,
    ) -> Model:
        """Run full context test on a model using smart binary search with progress saving."""
        logger.info(f"Starting context test for {model.id}")

        if self.verbose:
            logger.info(f"[Test Start] Model: {model.id}")
            logger.info(f"[Test Start] Declared context limit: {model.context_limit:,} tokens")
            logger.info("[Test Start] Using binary search to find true operational limit")

        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()

        # Load registry if not provided
        if registry is None:
            registry = load_model_registry()

        max_context = max_context or model.context_limit
        log_path = get_context_test_log_path(model.id)

        if self.verbose:
            logger.info(f"[Test Start] Test log will be saved to: {log_path}")

        # First, test with small context to ensure model loads
        logger.info(f"Initial test for {model.id} with context size {min_context}")

        if self.verbose:
            logger.info(
                f"[Phase 1] Verifying model can load with minimal context ({min_context} tokens)...",
            )

        initial_result = await self._test_at_context(model.id, min_context, log_path)

        if not initial_result.load_success:
            logger.error(f"Model {model.id} failed to load even with minimum context {min_context}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = f"Failed to load with context {min_context}: {initial_result.error}"
            model.last_known_bad_context = min_context
            # Save progress
            registry.update_model(model.id, model)
            save_model_registry(registry)
            return model

        if not initial_result.inference_success:
            logger.error(f"Model {model.id} loaded but inference failed at context {min_context}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = f"Inference failed at context {min_context}: {initial_result.error}"
            model.loadable_max_context = min_context
            model.last_known_bad_context = min_context
            # Save progress
            registry.update_model(model.id, model)
            save_model_registry(registry)
            return model

        # Model works at minimum context - we got a response
        model.last_known_good_context = min_context
        logger.info(
            f"✓ Model {model.id} works at context {min_context} - got response of length {len(initial_result.response)}",
        )

        if self.verbose:
            logger.info("[Phase 1] ✓ Success! Model is operational")
            logger.info("[Phase 2] Starting binary search for maximum context...")

        # Resume from previous test if available
        if model.last_known_good_context and model.last_known_bad_context:
            left = model.last_known_good_context
            right = model.last_known_bad_context - 1
            logger.info(f"Resuming test from previous state: good={left}, bad={right + 1}")

            if self.verbose:
                logger.info("[Resume] Found previous test data - resuming from checkpoint")
        else:
            left = min_context
            right = max_context

        logger.info(f"Testing range for {model.id}: {left} - {right}")

        if self.verbose:
            logger.info(f"[Binary Search] Search space: {left:,} to {right:,} tokens")
            logger.info(
                f"[Binary Search] Estimated iterations: ~{int(math.log2(right - left)) + 1}",
            )

        best_working_context = left  # We know this works
        iteration = 0

        try:
            while left <= right:
                mid = (left + right) // 2
                if mid in (0, best_working_context):
                    break

                iteration += 1
                logger.info(
                    f"Binary search iteration {iteration} for {model.id}: "
                    f"testing context size {mid} (range: {left}-{right})",
                )

                if self.verbose:
                    remaining = right - left
                    progress = ((model.context_limit - remaining) / model.context_limit) * 100
                    logger.info(f"[Iteration {iteration}] Testing midpoint: {mid:,} tokens")
                    logger.info(
                        f"[Iteration {iteration}] Current range: {left:,} - {right:,} ({remaining:,} tokens)",
                    )
                    logger.info(f"[Iteration {iteration}] Search progress: ~{progress:.1f}%")

                result = await self._test_at_context(model.id, mid, log_path)

                if result.load_success and result.inference_success:
                    # Model loaded and generated something - this is "good"
                    best_working_context = mid
                    model.last_known_good_context = mid
                    left = mid + 1  # Try for a larger context
                    logger.info(
                        f"✓ Context size {mid} succeeded (model loaded and responded), searching higher",
                    )

                    if self.verbose:
                        logger.info(
                            f"[Iteration {iteration}] ✓ SUCCESS at {mid:,} tokens - searching for higher limit",
                        )
                else:
                    # Model failed to load or inference failed - this is "bad"
                    model.last_known_bad_context = mid
                    right = mid - 1  # This context failed, try smaller
                    if not result.load_success:
                        logger.info(
                            f"✗ Context size {mid} failed (model didn't load), searching lower",
                        )
                        if self.verbose:
                            logger.info(
                                f"[Iteration {iteration}] ✗ FAILED to load at {mid:,} tokens - searching lower",
                            )
                    else:
                        logger.info(
                            f"✗ Context size {mid} failed (inference error), searching lower",
                        )
                        if self.verbose:
                            logger.info(
                                f"[Iteration {iteration}] ✗ FAILED inference at {mid:,} tokens - searching lower",
                            )

                    # Track loadable_max_context
                    if result.load_success:
                        model.loadable_max_context = max(model.loadable_max_context or 0, mid)

                # Save progress after each test
                model.tested_max_context = best_working_context
                registry.update_model(model.id, model)
                save_model_registry(registry)
                logger.debug(
                    f"Progress saved: good={model.last_known_good_context}, bad={model.last_known_bad_context}",
                )

                if self.verbose:
                    logger.debug(
                        f"[Progress] Current best working context: {best_working_context:,} tokens",
                    )

            model.tested_max_context = best_working_context
            model.context_test_log = str(log_path)
            model.context_test_status = (
                ContextTestStatus.COMPLETED
                if best_working_context > 0
                else ContextTestStatus.FAILED
            )

            logger.info(
                f"Context test completed for {model.id}. "
                f"Optimal working context: {best_working_context}",
            )

            if self.verbose:
                logger.info("[Test Complete] Final Results:")
                logger.info(
                    f"[Test Complete] ✓ Maximum working context: {best_working_context:,} tokens",
                )
                logger.info(f"[Test Complete] ✓ Declared limit: {model.context_limit:,} tokens")
                efficiency = (best_working_context / model.context_limit) * 100
                logger.info(f"[Test Complete] ✓ Efficiency: {efficiency:.1f}% of declared limit")
                logger.info(f"[Test Complete] ✓ Total iterations: {iteration}")
                logger.info(f"[Test Complete] ✓ Test log saved to: {log_path}")

        except Exception as e:
            logger.error(f"An unexpected error occurred during context test for {model.id}: {e}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = str(e)

        # Final save
        registry.update_model(model.id, model)
        save_model_registry(registry)

        return model
