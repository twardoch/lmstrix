"""Context testing functionality for discovering true model limits."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Self

from loguru import logger

from lmstrix.api import LMStudioClient
from lmstrix.api.exceptions import InferenceError, ModelLoadError
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.loaders.model_loader import load_model_registry
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

    def is_valid_response(self) -> bool:
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
    PROBLEMATIC_MODELS: ClassVar[dict] = {}

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
        self,
        model_id: str,
        context_size: int,
        event_type: str,
        details: str = "",
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
        except OSError as e:
            logger.warning(f"Failed to write to main log: {e}")

    def _test_at_context(
        self: Self,
        model_path: str,
        context_size: int,
        log_path: Path,
        model: Model | None = None,
        registry: ModelRegistry | None = None,
    ) -> ContextTestResult:
        """Test model at a specific context size with retry logic for timeouts."""
        logger.debug(f"Testing {model_path} at context size {context_size}")

        # Always print progress for context testing
        print(f"  → Testing context size: {context_size:,} tokens...")

        # Pessimistic approach: save the previous last_known_bad_context
        previous_last_bad = None
        if model:
            previous_last_bad = model.last_known_bad_context
            # Set current context as last_known_bad_context pessimistically
            model.last_known_bad_context = context_size
            # Save this pessimistic state if registry provided
            if registry:
                registry.update_model_by_id(model)
                logger.debug(f"Pessimistically set last_known_bad_context to {context_size}")

        # Check if we're approaching previous last_known_bad_context
        if previous_last_bad:
            percentage_of_bad = (context_size / previous_last_bad) * 100
            if percentage_of_bad >= 80:
                logger.warning(
                    f"Context size {context_size:,} is {percentage_of_bad:.0f}% of "
                    f"previous known bad context ({previous_last_bad:,}).",
                )
                if percentage_of_bad >= 90:
                    print(
                        f"  ⚠️  WARNING: Testing at {percentage_of_bad:.0f}% of previous known bad context!",
                    )

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

                # Success - restore previous last_known_bad_context
                if model:
                    model.last_known_bad_context = previous_last_bad
                    # Save the restored state if registry provided
                    if registry:
                        registry.update_model_by_id(model)
                        logger.debug(f"Restored last_known_bad_context to {previous_last_bad}")

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

            except (ModelLoadError, InferenceError) as e:
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
                    except (TypeError, AttributeError) as e:
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

    def _perform_initial_test(
        self: Self,
        model: Model,
        min_context: int,
        log_path: Path,
        registry: ModelRegistry,
    ) -> ContextTestResult | None:
        """Perform the initial test at a minimal context to ensure the model is operational."""
        logger.info(f"Initial test for {model.id} with context size {min_context}")
        print(f"\nPhase 1: Verifying model loads at {min_context:,} tokens...")

        if self.verbose:
            logger.info(
                f"[Phase 1] Verifying model can load with minimal context ({min_context} tokens)...",
            )

        initial_result = self._test_at_context(model.id, min_context, log_path, model, registry)

        if not initial_result.load_success:
            logger.error(f"Model {model.id} failed to load even with minimum context {min_context}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = f"Failed to load with context {min_context}: {initial_result.error}"
            model.last_known_bad_context = min_context
            registry.update_model_by_id(model)
            return None

        if not initial_result.inference_success:
            logger.error(f"Model {model.id} loaded but inference failed at context {min_context}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = f"Inference failed at context {min_context}: {initial_result.error}"
            model.loadable_max_context = min_context
            model.last_known_bad_context = min_context
            registry.update_model_by_id(model)
            return None

        model.last_known_good_context = min_context
        logger.info(
            f"✓ Model {model.id} works at context {min_context} - got response of length {len(initial_result.response)}",
        )

        if self.verbose:
            logger.info("[Phase 1] ✓ Success! Model is operational")

        return initial_result

    def _perform_threshold_test(
        self: Self,
        model: Model,
        max_context: int,
        log_path: Path,
        registry: ModelRegistry,
    ) -> ContextTestResult | None:
        """Perform the test at the specified threshold."""
        test_context = max_context
        declared_limit = model.context_limit

        print(f"\nPhase 2: Testing at threshold ({test_context:,} tokens)...")
        if self.verbose:
            logger.info(f"[Phase 2] Testing at threshold: {test_context:,} tokens")
            logger.info(f"[Phase 2] Declared limit: {declared_limit:,} tokens")
            logger.info(f"[Phase 2] Using min(threshold, declared_limit) = {test_context:,}")

        threshold_result = self._test_at_context(model.id, test_context, log_path, model, registry)

        if threshold_result.load_success and threshold_result.inference_success:
            model.last_known_good_context = test_context
            model.tested_max_context = test_context
            return threshold_result

        model.last_known_bad_context = test_context
        if threshold_result.load_success:
            model.loadable_max_context = test_context

        return None

    def _perform_incremental_test(
        self: Self,
        model: Model,
        start_context: int,
        log_path: Path,
        registry: ModelRegistry,
    ) -> None:
        """Perform incremental testing from a known good context."""
        print("\nPhase 3: Testing higher contexts...")
        if self.verbose:
            logger.info("[Phase 3] Threshold test passed, testing higher contexts...")
            logger.info(f"[Phase 3] Will use progressive strategy up to {model.context_limit:,}")

        current_context = start_context

        while current_context < model.context_limit:
            if current_context < start_context:
                next_context = current_context * 2
            else:
                next_context = int(current_context * 1.1)

            next_context = min(next_context, model.context_limit)

            if model.last_known_bad_context:
                safe_next_context = int(model.last_known_bad_context * 0.75)
                if next_context >= model.last_known_bad_context:
                    next_context = safe_next_context
                    logger.info(
                        f"Limiting next_context to {safe_next_context:,} (75% of last bad {model.last_known_bad_context:,})",
                    )
            print(f"  → Testing context size: {next_context:,} tokens...")

            if self.verbose:
                logger.info(f"[Phase 3] Testing at {next_context:,} tokens...")

            result = self._test_at_context(model.id, next_context, log_path, model, registry)

            if result.load_success and result.inference_success:
                model.last_known_good_context = next_context
                model.tested_max_context = next_context
                current_context = next_context
                registry.update_model_by_id(model)

                if next_context >= model.context_limit:
                    model.context_test_status = ContextTestStatus.COMPLETED
                    model.context_test_log = str(log_path)
                    logger.info(
                        f"✓ Model {model.id} works at full declared limit {next_context:,}!",
                    )
                    print("  ✓ Success! Model works at declared limit.")
                    return
            else:
                model.last_known_bad_context = next_context
                if result.load_success:
                    model.loadable_max_context = next_context
                return

    def _perform_binary_search(
        self: Self,
        model: Model,
        low: int,
        high: int,
        log_path: Path,
        registry: ModelRegistry,
    ) -> None:
        """Perform binary search to find the optimal context size."""
        print(f"\nPhase 4: Binary search between {low:,} and {high:,}...")
        if self.verbose:
            logger.info(f"[Phase 4] Failed at {high + 1:,}, starting binary search")

        left = low
        right = high
        best_working_context = left
        iteration = 0
        consecutive_timeouts = 0
        max_consecutive_timeouts = 2

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

            result = self._test_at_context(model.id, mid, log_path, model, registry)

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
                consecutive_timeouts = 0

            if result.load_success and result.inference_success:
                best_working_context = mid
                model.last_known_good_context = mid
                left = mid + 1
                logger.info(
                    f"✓ Context size {mid} succeeded (model loaded and responded), searching higher",
                )

                if self.verbose:
                    logger.info(
                        f"[Iteration {iteration}] ✓ SUCCESS at {mid:,} tokens - searching for higher limit",
                    )
            else:
                model.last_known_bad_context = mid
                right = mid - 1
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

                if result.load_success:
                    model.loadable_max_context = max(model.loadable_max_context or 0, mid)

            model.tested_max_context = best_working_context
            registry.update_model_by_id(model)
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
            ContextTestStatus.COMPLETED if best_working_context > 0 else ContextTestStatus.FAILED
        )

        logger.info(
            f"Context test completed for {model.id}. Optimal working context: {best_working_context}",
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

    def _filter_models_for_testing(self: Self, models: list[Model]) -> list[Model]:
        """Filter out embedding models and already completed models."""
        llm_models = []
        skipped_completed = 0
        skipped_embedding = 0
        for m in models:
            if self._is_embedding_model(m):
                skipped_embedding += 1
                continue
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

        if skipped_embedding > 0:
            logger.info(f"Excluded {skipped_embedding} embedding models from context testing")

        if len(models) - len(llm_models) - skipped_completed > 0:
            excluded_count = len(models) - len(llm_models) - skipped_completed
            logger.info(f"Excluded {excluded_count} embedding models from context testing")

        if skipped_completed > 0:
            logger.info(f"Skipped {skipped_completed} already completed models")

        if not llm_models:
            logger.warning(
                "No models need testing (all are either embedding models or already completed)",
            )

        return llm_models

    def _perform_pass_one_testing(
        self: Self,
        sorted_models: list[Model],
        min_context: int,
        registry: ModelRegistry,
    ) -> tuple[dict[str, Model], list[Model]]:
        """Perform the first pass of testing at a minimal context."""
        active_models = {m.id: m for m in sorted_models}
        updated_models = []

        print(f"\n{'=' * 60}")
        print(f"Pass 1: Testing all models at {min_context:,} tokens")
        print(f"{'=' * 60}\n")

        for i, model in enumerate(sorted_models, 1):
            if model.id not in active_models:
                continue

            print(f"[{i}/{len(sorted_models)}] Testing {model.id}...")

            if model.last_known_good_context and model.last_known_good_context >= min_context:
                print(
                    f"  ⏭️  Skipping - already tested successfully at {model.last_known_good_context:,} tokens",
                )
                updated_models.append(model)
                continue

            if i > 1:
                print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
                time.sleep(3.0)

            log_path = get_context_test_log_path(model.id)

            model.context_test_status = ContextTestStatus.TESTING
            model.context_test_date = datetime.now()
            registry.update_model_by_id(model)

            result = self._test_at_context(model.id, min_context, log_path, model, registry)

            if not result.load_success or not result.inference_success:
                model.context_test_status = ContextTestStatus.FAILED
                model.error_msg = f"Failed at minimum context {min_context}: {result.error}"
                if result.load_success:
                    model.loadable_max_context = min_context
                    model.last_known_bad_context = min_context
                else:
                    model.last_known_bad_context = min_context
                del active_models[model.id]
                print(f"  ✗ Failed at {min_context:,} tokens: {result.error}")
            else:
                model.last_known_good_context = min_context
                model.tested_max_context = min_context
                print(f"  ✓ Success at {min_context:,} tokens")

            registry.update_model_by_id(model)
            updated_models.append(model)

        return active_models, updated_models

    def _perform_subsequent_passes(
        self: Self,
        active_models: dict[str, Model],
        threshold: int,
        registry: ModelRegistry,
    ) -> None:
        """Perform subsequent passes of testing at progressively higher contexts."""
        pass_num = 2

        while active_models:
            next_contexts = {}
            for model_id, model in active_models.items():
                if model.last_known_good_context >= model.context_limit:
                    continue

                if model.last_known_good_context < threshold:
                    next_context = model.last_known_good_context * 2
                else:
                    next_context = int(model.last_known_good_context * 1.1)

                next_context = min(next_context, model.context_limit)

                if model.last_known_bad_context:
                    safe_next_context = int(model.last_known_bad_context * 0.75)
                    if next_context >= model.last_known_bad_context:
                        next_context = safe_next_context
                        logger.info(
                            f"Model {model_id}: Limiting next_context to {safe_next_context:,} "
                            f"(75% of last bad {model.last_known_bad_context:,})",
                        )

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

                print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
                time.sleep(3.0)

                log_path = get_context_test_log_path(model.id)
                result = self._test_at_context(model.id, test_context, log_path, model, registry)

                if result.load_success and result.inference_success:
                    model.last_known_good_context = test_context
                    model.tested_max_context = test_context
                    print(f"  ✓ Success at {test_context:,} tokens")

                    if test_context >= model.context_limit:
                        model.context_test_status = ContextTestStatus.COMPLETED
                        model.context_test_log = str(log_path)
                        models_to_remove.append(model_id)
                        print("  ✓ Reached declared limit!")
                else:
                    model.last_known_bad_context = test_context
                    if result.load_success:
                        model.loadable_max_context = test_context

                    model.context_test_status = ContextTestStatus.COMPLETED
                    model.context_test_log = str(log_path)
                    models_to_remove.append(model_id)
                    print(f"  ✗ Failed at {test_context:,} tokens - found limit")

                registry.update_model_by_id(model)

            for model_id in models_to_remove:
                del active_models[model_id]

            pass_num += 1

    def test_model(
        self: Self,
        model: Model,
        min_context: int = 2048,
        max_context: int | None = None,
        registry: ModelRegistry | None = None,
    ) -> Model:
        """Run full context test on a model using the new safe testing strategy."""
        logger.info(f"Starting context test for {model.id}")

        if self.verbose:
            logger.info(f"[Test Start] Model: {model.id}")
            logger.info(f"[Test Start] Declared context limit: {model.context_limit:,} tokens")
            logger.info("[Test Start] Using binary search to find true operational limit")

        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()

        if registry is None:
            registry = load_model_registry()

        registry.update_model_by_id(model)

        max_context = max_context or model.context_limit

        if model.last_known_bad_context:
            safe_max_context = int(model.last_known_bad_context * 0.75)
            if max_context >= model.last_known_bad_context:
                logger.warning(
                    f"Requested max_context ({max_context:,}) is at or above last known bad context "
                    f"({model.last_known_bad_context:,}). Limiting to {safe_max_context:,} (75% of last bad).",
                )
                max_context = safe_max_context

        log_path = get_context_test_log_path(model.id)

        if self.verbose:
            logger.info(f"[Test Start] Test log will be saved to: {log_path}")

        initial_result = self._perform_initial_test(model, min_context, log_path, registry)
        if not initial_result:
            return model

        threshold_result = self._perform_threshold_test(model, max_context, log_path, registry)
        if threshold_result:
            if threshold_result.context_size >= model.context_limit:
                model.context_test_status = ContextTestStatus.COMPLETED
                model.context_test_log = str(log_path)
                logger.info(
                    f"✓ Model {model.id} works at declared limit {threshold_result.context_size:,}!",
                )
                print("  ✓ Success! Model works at declared limit.")
                registry.update_model_by_id(model)
                return model

            self._perform_incremental_test(model, threshold_result.context_size, log_path, registry)
        else:
            self._perform_binary_search(
                model,
                min_context,
                max_context - 1,
                log_path,
                registry,
            )

        registry.update_model_by_id(model)

        return model

    def _is_embedding_model(self: Self, model: Model) -> bool:
        """Check if a model is an embedding model."""
        if model.id.startswith("text-embedding-"):
            return True
        if "embedding" in model.id.lower():
            return True
        if "embed" in model.id.lower():
            return True
        return bool(hasattr(model, "model_type") and model.model_type == "embedding")

    def test_all_models(
        self: Self,
        models: list[Model],
        threshold: int = 102400,
        registry: ModelRegistry | None = None,
    ) -> list[Model]:
        """Test multiple models efficiently using a pass-based approach."""
        llm_models = self._filter_models_for_testing(models)
        if not llm_models:
            return []

        if registry is None:
            registry = load_model_registry()

        sorted_models = sorted(llm_models, key=lambda m: m.context_limit)
        logger.info(f"Testing {len(sorted_models)} models in optimized pass-based approach")

        active_models, updated_models = self._perform_pass_one_testing(
            sorted_models,
            2048,
            registry,
        )

        if active_models:
            self._perform_subsequent_passes(active_models, threshold, registry)

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
