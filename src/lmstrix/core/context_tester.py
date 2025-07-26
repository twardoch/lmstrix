"""Context testing functionality for discovering true model limits."""

import json
import math
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from lmstrix.api import LMStudioClient
from lmstrix.api.exceptions import ModelLoadError
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.loaders.model_loader import load_model_registry, save_model_registry
from lmstrix.utils import get_context_test_log_path, get_lmstrix_log_path


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
    size that a model can reliably handle. The test starts with a moderate context (2048)
    to verify the model loads and can generate responses, then searches for the
    maximum working context. Progress is saved after each test to allow resuming if interrupted.

    A context is considered "good" if the model loads AND generates any response.
    A context is considered "bad" if the model fails to load OR crashes during inference.
    All responses are logged for manual review - no content validation is performed.

    Attributes:
        client: LMStudioClient instance for model operations.
        test_prompt: The prompt used for testing (default: "Say hello").
    """

    # Models with known issues - these may need special handling
    PROBLEMATIC_MODELS = {}

    def __init__(self, client: LMStudioClient | None = None, verbose: bool = False) -> None:
        """Initialize context tester.

        Args:
            client: LMStudioClient instance for model operations.
            verbose: Enable verbose logging output.
        """
        self.client = client or LMStudioClient()
        self.test_prompt = "Say hello"
        self.verbose = verbose
        self.inference_timeout = 90.0  # Increased to 90 seconds for better reliability
        self.max_retries = 2  # Retry timeouts up to 2 times

    def _log_result(self, log_path: Path, result: ContextTestResult) -> None:
        """Append test result to log file."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    def _log_to_main_log(
        self, model_id: str, context_size: int, event_type: str, details: str = "",
    ) -> None:
        """Log attempt or solution to the main lmstrix.log.txt file.

        Args:
            model_id: The model being tested
            context_size: The context size being tested
            event_type: Either "ATTEMPT" or "SOLUTION"
            details: Additional details (e.g., success/failure, response length)
        """
        log_path = get_lmstrix_log_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}: model={model_id}, context={context_size:,}"
        if details:
            log_entry += f", {details}"
        log_entry += "\n"

        try:
            with log_path.open("a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.warning(f"Failed to write to main log: {e}")

    def _test_at_context(
        self,
        model_path: str,
        context_size: int,
        log_path: Path,
    ) -> ContextTestResult:
        """Test model at a specific context size with retry logic for timeouts."""
        logger.debug(f"Testing {model_path} at context size {context_size}")

        # Always print progress for context testing
        print(f"  → Testing context size: {context_size:,} tokens...")

        # Log the attempt before loading the model
        self._log_to_main_log(model_path, context_size, "ATTEMPT")

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for {model_path} at context {context_size}")
                print(f"  ↻ Retry {attempt}/{self.max_retries}...")
                # Add extra delay before retry
                time.sleep(2.0)

            if self.verbose:
                logger.info(
                    f"[Context Test] Loading model '{model_path}' with context size: {context_size:,} tokens",
                )

            llm = None
            model_loaded = False
            try:
                # Add a small delay to avoid rapid operations
                time.sleep(0.5)

                llm = self.client.load_model(model_path, context_len=context_size)
                model_loaded = True
                logger.debug(f"Model {model_path} loaded successfully at {context_size}.")

                if self.verbose:
                    logger.info(
                        "[Context Test] ✓ Model loaded successfully, attempting inference...",
                    )

                response = self.client.completion(
                    llm=llm,
                    prompt=self.test_prompt,
                    max_tokens=10,
                    model_id=model_path,
                    timeout=self.inference_timeout,
                )

                if self.verbose:
                    logger.info(
                        f"[Context Test] ✓ Inference successful! Response length: {len(response.content)} chars",
                    )
                    logger.debug(
                        (
                            f"[Context Test] Response: {response.content[:50]}..."
                            if len(response.content) > 50
                            else f"[Context Test] Response: {response.content}"
                        ),
                    )

                result = ContextTestResult(
                    context_size=context_size,
                    load_success=True,
                    inference_success=True,
                    prompt=self.test_prompt,
                    response=response.content,
                )

                # Log the successful solution
                self._log_to_main_log(
                    model_path,
                    context_size,
                    "SOLUTION",
                    f"success=True, response_length={len(response.content)}",
                )

                # Success - log and return
                self._log_result(log_path, result)
                return result

            except ModelLoadError as e:
                logger.warning(f"Failed to load {model_path} at context {context_size}: {e}")

                if self.verbose:
                    logger.info(
                        f"[Context Test] ✗ Model failed to load at context {context_size:,}",
                    )
                    logger.debug(f"[Context Test] Load error: {e!s}")

                    # Check if it's a "model not found" error
                    if "noModelMatchingQuery" in str(e):
                        logger.info(
                            f"[Context Test] ⚠️  Model '{model_path}' is not loaded in LM Studio",
                        )
                        logger.info(
                            "[Context Test] ⚠️  Please load the model in LM Studio first before testing",
                        )

                result = ContextTestResult(
                    context_size=context_size,
                    load_success=False,
                    error=str(e),
                )

                # Log the failed solution
                self._log_to_main_log(
                    model_path,
                    context_size,
                    "SOLUTION",
                    f"success=False, load_failed=True, error={str(e)[:50]}",
                )

                self._log_result(log_path, result)
                return result  # Don't retry load errors

            except Exception as e:
                is_timeout = "timed out" in str(e).lower()

                if is_timeout and attempt < self.max_retries:
                    # This is a timeout and we have retries left
                    logger.warning(
                        f"Timeout on attempt {attempt + 1} for {model_path} at context {context_size}, will retry",
                    )
                    if self.verbose:
                        logger.info(
                            f"[Context Test] ⏱️  Timeout on attempt {attempt + 1}, retrying...",
                        )
                    continue  # Try again

                # Final failure or non-timeout error
                logger.error(f"Inference failed for {model_path} at context {context_size}: {e}")

                if self.verbose:
                    logger.info(f"[Context Test] ✗ Inference failed at context {context_size:,}")
                    logger.debug(f"[Context Test] Inference error: {e!s}")

                    # Special handling for timeout errors
                    if is_timeout:
                        logger.warning(
                            f"[Context Test] ⏱️  Model timed out after {self.inference_timeout}s on all attempts. "
                            "Model may be unresponsive or context size too large.",
                        )

                result = ContextTestResult(
                    context_size=context_size,
                    load_success=True,
                    inference_success=False,
                    prompt=self.test_prompt,
                    error=str(e),
                )

                # Log the failed inference
                self._log_to_main_log(
                    model_path,
                    context_size,
                    "SOLUTION",
                    f"success=False, inference_failed=True, error={str(e)[:50]}",
                )

                self._log_result(log_path, result)
                return result

            finally:
                if llm and model_loaded:
                    try:
                        if self.verbose:
                            logger.debug("[Context Test] Unloading model...")
                        llm.unload()
                        logger.debug(f"Model {model_path} unloaded.")
                        # Add delay after unload to ensure clean state
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Failed to unload model: {e}")

        # This should not be reached, but just in case
        result = ContextTestResult(
            context_size=context_size,
            load_success=False,
            error="All retry attempts failed",
        )

        # Log the failed attempt
        self._log_to_main_log(
            model_path,
            context_size,
            "SOLUTION",
            "success=False, all_retries_failed=True",
        )

        self._log_result(log_path, result)
        return result

    def test_model(
        self,
        model: Model,
        min_context: int = 2048,
        max_context: int | None = None,
        registry: ModelRegistry | None = None,
    ) -> Model:
        """Run full context test on a model using the new safe testing strategy.

        Algorithm:
        1. Test at min_context (1024) to verify model loads
        2. Test at min(max_context, declared_limit) - the threshold test
        3. If threshold test succeeds and max_context > declared_limit:
           - Increment by 10240 until failure or reaching declared_limit
        4. If threshold test fails:
           - Binary search between min_context and failed size
        """
        # Track consecutive failures to detect unresponsive models
        consecutive_timeouts = 0
        max_consecutive_timeouts = 2  # Give up after 2 consecutive timeouts

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

        # Save the initial testing status
        registry.update_model(model.id, model)
        save_model_registry(registry)

        max_context = max_context or model.context_limit
        log_path = get_context_test_log_path(model.id)

        if self.verbose:
            logger.info(f"[Test Start] Test log will be saved to: {log_path}")

        # Phase 1: Test with small context to ensure model loads
        logger.info(f"Initial test for {model.id} with context size {min_context}")
        print(f"\nPhase 1: Verifying model loads at {min_context:,} tokens...")

        if self.verbose:
            logger.info(
                f"[Phase 1] Verifying model can load with minimal context ({min_context} tokens)...",
            )

        initial_result = self._test_at_context(model.id, min_context, log_path)

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

        # Phase 2: Test at threshold (min of max_context and declared limit)
        test_context = max_context
        declared_limit = model.context_limit

        print(f"\nPhase 2: Testing at threshold ({test_context:,} tokens)...")
        if self.verbose:
            logger.info(f"[Phase 2] Testing at threshold: {test_context:,} tokens")
            logger.info(f"[Phase 2] Declared limit: {declared_limit:,} tokens")
            logger.info(f"[Phase 2] Using min(threshold, declared_limit) = {test_context:,}")

        threshold_result = self._test_at_context(model.id, test_context, log_path)

        if threshold_result.load_success and threshold_result.inference_success:
            # Threshold test passed
            model.last_known_good_context = test_context
            model.tested_max_context = test_context

            if test_context >= declared_limit:
                # We tested at or above declared limit and it worked - we're done!
                model.context_test_status = ContextTestStatus.COMPLETED
                model.context_test_log = str(log_path)
                logger.info(f"✓ Model {model.id} works at declared limit {test_context:,}!")
                print("  ✓ Success! Model works at declared limit.")

                registry.update_model(model.id, model)
                save_model_registry(registry)
                return model
            # Threshold < declared limit, try incremental increases
            print("\nPhase 3: Testing higher contexts...")
            if self.verbose:
                logger.info("[Phase 3] Threshold test passed, testing higher contexts...")
                logger.info(f"[Phase 3] Will use progressive strategy up to {declared_limit:,}")

            current_context = test_context

            while current_context < declared_limit:
                # Use the same strategy as batch testing:
                # Double until threshold, then add 10%
                if current_context < max_context:  # max_context is the threshold
                    next_context = current_context * 2
                else:
                    next_context = int(current_context * 1.1)

                next_context = min(next_context, declared_limit)
                print(f"  → Testing context size: {next_context:,} tokens...")

                if self.verbose:
                    logger.info(f"[Phase 3] Testing at {next_context:,} tokens...")

                result = self._test_at_context(model.id, next_context, log_path)

                if result.load_success and result.inference_success:
                    # Still working, update and continue
                    model.last_known_good_context = next_context
                    model.tested_max_context = next_context
                    current_context = next_context

                    # Save progress
                    registry.update_model(model.id, model)
                    save_model_registry(registry)

                    if next_context >= declared_limit:
                        # Reached declared limit successfully
                        model.context_test_status = ContextTestStatus.COMPLETED
                        model.context_test_log = str(log_path)
                        logger.info(
                            f"✓ Model {model.id} works at full declared limit {next_context:,}!",
                        )
                        print("  ✓ Success! Model works at declared limit.")
                        return model
                else:
                    # Failed at this size, we found the limit
                    model.last_known_bad_context = next_context
                    if result.load_success:
                        model.loadable_max_context = next_context

                    # Do binary search between last good and this bad
                    print(
                        f"\nPhase 4: Binary search between {current_context:,} and {next_context:,}...",
                    )
                    if self.verbose:
                        logger.info(f"[Phase 4] Failed at {next_context:,}, starting binary search")

                    left = current_context
                    right = next_context - 1
                    break
            else:
                # Completed all increments successfully
                model.context_test_status = ContextTestStatus.COMPLETED
                model.context_test_log = str(log_path)
                logger.info(
                    f"✓ Model {model.id} completed incremental testing up to {current_context:,}!",
                )
                print(f"  ✓ Test complete! Optimal context: {current_context:,} tokens")
                return model
        else:
            # Threshold test failed, need binary search
            model.last_known_bad_context = test_context
            if threshold_result.load_success:
                model.loadable_max_context = test_context

            print("\nPhase 3: Binary search to find actual limit...")
            if self.verbose:
                logger.info(f"[Phase 2] ✗ Failed at threshold {test_context:,}")
                logger.info("[Phase 3] Starting binary search...")

            left = min_context
            right = test_context - 1

        logger.info(f"Testing range for {model.id}: {left} - {right}")

        if self.verbose:
            logger.info(f"[Binary Search] Search space: {left:,} to {right:,} tokens")
            logger.info(
                f"[Binary Search] Estimated iterations: ~{int(math.log2(right - left)) + 1}",
            )

        best_working_context = left  # We know this works
        iteration = 0
        consecutive_timeouts = 0  # Reset counter

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

                result = self._test_at_context(model.id, mid, log_path)

                # Check for timeout
                is_timeout = "timed out" in str(result.error).lower()
                if is_timeout:
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= max_consecutive_timeouts:
                        logger.error(
                            f"Model {model.id} appears unresponsive after "
                            f"{consecutive_timeouts} consecutive timeouts. Aborting test.",
                        )
                        if self.verbose:
                            logger.error(
                                f"[Test Abort] Model has timed out {consecutive_timeouts} times in a row. "
                                "The model appears to be unresponsive or stuck.",
                            )
                        model.context_test_status = ContextTestStatus.FAILED
                        model.error_msg = (
                            f"Model unresponsive - {consecutive_timeouts} consecutive timeouts"
                        )
                        break
                else:
                    consecutive_timeouts = 0  # Reset on non-timeout result

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

            # No need for special final check since we test max first now
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
            print(f"  ✓ Test complete! Optimal context: {best_working_context:,} tokens")

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

    def test_all_models(
        self,
        models: list[Model],
        threshold: int = 102400,
        registry: ModelRegistry | None = None,
    ) -> list[Model]:
        """Test multiple models efficiently using a pass-based approach.

        This method optimizes testing by:
        1. Sorting models by declared context size (ascending)
        2. Testing in passes to minimize model loading/unloading
        3. Excluding failed models from subsequent passes
        4. Persisting progress between passes

        Args:
            models: List of models to test
            threshold: Maximum context size for initial testing
            registry: Model registry for saving progress

        Returns:
            List of updated models with test results
        """
        if not models:
            return []

        # Filter out embedding models - they can't be used for LLM context testing
        def is_embedding_model(model) -> bool:
            # Check ID patterns
            if model.id.startswith("text-embedding-"):
                return True
            if "embedding" in model.id.lower():
                return True
            if "embed" in model.id.lower():
                return True
            # Check if model has model_type field indicating it's an embedding model
            return bool(hasattr(model, "model_type") and model.model_type == "embedding")

        # Filter out embedding models and already completed models
        llm_models = []
        skipped_completed = 0
        for m in models:
            if is_embedding_model(m):
                continue
            # Skip if already completed and at declared limit
            if (
                m.context_test_status == ContextTestStatus.COMPLETED
                and m.tested_max_context
                and m.tested_max_context >= m.context_limit
            ):
                skipped_completed += 1
                logger.info(
                    f"Skipping {m.id} - already tested to declared limit ({m.tested_max_context:,} tokens)",
                )
                continue
            llm_models.append(m)

        if len(models) - len(llm_models) - skipped_completed > 0:
            excluded_count = len(models) - len(llm_models) - skipped_completed
            logger.info(f"Excluded {excluded_count} embedding models from context testing")

        if skipped_completed > 0:
            logger.info(f"Skipped {skipped_completed} already completed models")

        if not llm_models:
            logger.warning(
                "No models need testing (all are either embedding models or already completed)",
            )
            return []

        # Load registry if not provided
        if registry is None:
            registry = load_model_registry()

        # Sort models by declared context size (ascending)
        sorted_models = sorted(llm_models, key=lambda m: m.context_limit)
        logger.info(f"Testing {len(sorted_models)} models in optimized pass-based approach")

        # Track which models are still active for testing
        active_models = {m.id: m for m in sorted_models}
        updated_models = []

        # Pass 1: Test all models at min context (2048)
        min_context = 2048
        print(f"\n{'=' * 60}")
        print(f"Pass 1: Testing all models at {min_context:,} tokens")
        print(f"{'=' * 60}\n")

        for i, model in enumerate(sorted_models, 1):
            if model.id not in active_models:
                continue

            print(f"[{i}/{len(sorted_models)}] Testing {model.id}...")

            # Check if model has already been tested at a higher context
            if model.last_known_good_context and model.last_known_good_context >= min_context:
                print(
                    f"  ⏭️  Skipping - already tested successfully at {model.last_known_good_context:,} tokens",
                )
                # Keep the model active for higher context testing
                updated_models.append(model)
                continue

            # Add delay to prevent rapid model switching in batch mode
            if i > 1:  # Skip delay for first model
                print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
                time.sleep(3.0)

            log_path = get_context_test_log_path(model.id)

            # Update model status
            model.context_test_status = ContextTestStatus.TESTING
            model.context_test_date = datetime.now()
            registry.update_model(model.id, model)
            save_model_registry(registry)

            # Test at min context
            result = self._test_at_context(model.id, min_context, log_path)

            if not result.load_success or not result.inference_success:
                # Model failed at minimum context
                model.context_test_status = ContextTestStatus.FAILED
                model.error_msg = f"Failed at minimum context {min_context}: {result.error}"
                if result.load_success:
                    model.loadable_max_context = min_context
                    model.last_known_bad_context = min_context
                else:
                    model.last_known_bad_context = min_context

                # Remove from active models
                del active_models[model.id]
                print(f"  ✗ Failed at {min_context:,} tokens: {result.error}")
            else:
                # Model passed minimum context
                model.last_known_good_context = min_context
                model.tested_max_context = min_context
                print(f"  ✓ Success at {min_context:,} tokens")

            # Save progress
            registry.update_model(model.id, model)
            save_model_registry(registry)
            updated_models.append(model)

        # Continue with additional passes for models that passed
        if not active_models:
            print("\nAll models failed at minimum context. Testing complete.")
            return updated_models

        # Pass 2+: Test remaining models at progressively higher contexts
        pass_num = 2
        current_context = min_context

        while active_models and current_context < max(
            m.context_limit for m in active_models.values()
        ):
            # Determine next context size using new strategy:
            # - Double until we exceed threshold
            # - Then add 10% each time
            next_contexts = {}
            for model_id, model in active_models.items():
                if model.last_known_good_context >= model.context_limit:
                    # Already at declared limit
                    continue

                # Determine next context size based on threshold
                if model.last_known_good_context < threshold:
                    # Below threshold: double the context
                    next_context = model.last_known_good_context * 2
                else:
                    # Above threshold: add 10%
                    next_context = int(model.last_known_good_context * 1.1)

                # Ensure we don't exceed the declared limit
                next_context = min(next_context, model.context_limit)

                # Only add if there's room to grow
                if next_context > model.last_known_good_context:
                    next_contexts[model_id] = next_context

            if not next_contexts:
                break

            print(f"\n{'=' * 60}")
            print(f"Pass {pass_num}: Testing {len(next_contexts)} models")
            print(f"{'=' * 60}\n")

            models_to_remove = []

            for model_id, test_context in next_contexts.items():
                model = active_models[model_id]
                print(f"Testing {model.id} at {test_context:,} tokens...")

                # Add delay to prevent rapid model switching in batch mode
                print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
                time.sleep(3.0)

                log_path = get_context_test_log_path(model.id)
                result = self._test_at_context(model.id, test_context, log_path)

                if result.load_success and result.inference_success:
                    # Success - update model
                    model.last_known_good_context = test_context
                    model.tested_max_context = test_context
                    print(f"  ✓ Success at {test_context:,} tokens")

                    # Check if we've reached declared limit
                    if test_context >= model.context_limit:
                        model.context_test_status = ContextTestStatus.COMPLETED
                        model.context_test_log = str(log_path)
                        models_to_remove.append(model_id)
                        print("  ✓ Reached declared limit!")
                else:
                    # Failure - model has hit its limit
                    model.last_known_bad_context = test_context
                    if result.load_success:
                        model.loadable_max_context = test_context

                    # Mark as completed (we found the limit)
                    model.context_test_status = ContextTestStatus.COMPLETED
                    model.context_test_log = str(log_path)
                    models_to_remove.append(model_id)
                    print(f"  ✗ Failed at {test_context:,} tokens - found limit")

                # Save progress
                registry.update_model(model.id, model)
                save_model_registry(registry)

            # Remove completed models
            for model_id in models_to_remove:
                del active_models[model_id]

            pass_num += 1

        # Final summary
        print(f"\n{'=' * 60}")
        print("Testing complete! Summary:")
        print(f"{'=' * 60}")

        completed = sum(
            1 for m in updated_models if m.context_test_status == ContextTestStatus.COMPLETED
        )
        failed = sum(1 for m in updated_models if m.context_test_status == ContextTestStatus.FAILED)

        print(f"Total models tested: {len(updated_models)}")
        print(f"Successfully completed: {completed}")
        print(f"Failed: {failed}")

        return updated_models
