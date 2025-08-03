"""Context testing functionality for discovering true model limits."""

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from lmstrix.api import LMStudioClient
from lmstrix.core.inference import InferenceEngine

if TYPE_CHECKING:
    from lmstrix.core.models import Model, ModelRegistry

from lmstrix.core.models import ContextTestStatus


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

    def __init__(
        self,
        client: LMStudioClient | None = None,
        verbose: bool = False,
        fast_mode: bool = False,
    ) -> None:
        """Initialize context tester.

        Args:
            client: LMStudioClient instance for model operations.
            verbose: Enable verbose logging output.
            fast_mode: Skip semantic verification - only test if inference completes.
        """
        self.client = client or LMStudioClient()
        self.inference_engine = InferenceEngine(client=self.client, verbose=verbose)
        # Enhanced dual testing prompts
        self.test_prompt_1 = "Write 'ninety-six' as a number using only digits"
        self.test_prompt_2 = "2+3="
        # Keep legacy for backward compatibility
        self.test_prompt = "Say hello"
        self.verbose = verbose
        self.fast_mode = fast_mode
        self.inference_timeout = 90.0  # Increased to 90 seconds for better reliability
        self.max_retries = 2  # Retry timeouts up to 2 times

    def _test_at_context(
        self,
        model_id: str,
        context_size: int,
        log_path: str | None = None,
        model: "Model" = None,
        registry: "ModelRegistry" = None,
    ) -> ContextTestResult:
        """Test a model at a specific context size using InferenceEngine.

        Args:
            model_id: Model identifier.
            context_size: Context size to test.
            log_path: Optional path for logging (unused).
            model: Optional model object (unused).
            registry: Optional registry (unused).

        Returns:
            ContextTestResult with test outcome.
        """
        # Use the proven InferenceEngine test method
        try:
            success, response = self.inference_engine._test_inference_capability(
                model_id,
                context_size,
            )

            return ContextTestResult(
                context_size=context_size,
                load_success=True,  # If we got here, model loaded
                inference_success=success,
                prompt="Dual inference test (96 digits + 2+3=5)",
                response=response,
                error=None if success else response,
            )
        except Exception as e:
            return ContextTestResult(
                context_size=context_size,
                load_success=False,
                inference_success=False,
                prompt="Dual inference test (96 digits + 2+3=5)",
                response="",
                error=str(e),
            )

    def _is_embedding_model(self, model) -> bool:
        """Check if a model is an embedding model.

        Args:
            model: Model object to check

        Returns:
            True if the model is an embedding model, False otherwise
        """
        # Check if model has the id attribute and contains embedding keywords
        if hasattr(model, "id") and model.id:
            model_id = model.id.lower()
            return "embedding" in model_id or "embed" in model_id
        return False

    def _filter_models_for_testing(self, models: list) -> list:
        """Filter out embedding models from the list of models to test.

        Args:
            models: List of models to filter

        Returns:
            List of models with embedding models removed
        """
        filtered_models = []
        for model in models:
            if not self._is_embedding_model(model):
                filtered_models.append(model)
        return filtered_models

    def test_all_models(
        self,
        models_to_test: list["Model"],
        threshold: int = 4096,
        registry: "ModelRegistry" = None,
    ) -> list["Model"]:
        """Test all models to find their maximum working context.

        Args:
            models_to_test: List of models to test
            threshold: Context size threshold to test
            registry: Model registry for updating results

        Returns:
            List of updated models with test results
        """
        updated_models = []

        for model in models_to_test:
            # Test the model at the threshold context size
            result = self._test_at_context(
                model.id,
                threshold,
                log_path=None,
                model=model,
                registry=registry,
            )

            # Update model with test results
            if result.load_success and result.inference_success:
                model.tested_max_context = threshold
                model.context_test_status = ContextTestStatus.COMPLETED
            else:
                model.context_test_status = ContextTestStatus.FAILED

            model.context_test_date = datetime.now()

            # Update registry if provided
            if registry:
                registry.update_model_by_id(model)

            updated_models.append(model)

        return updated_models

    def test_model(
        self,
        model_id: str,
        min_context: int = 512,
        max_context: int = 131072,
    ) -> dict:
        """Test a model to find its maximum working context.

        Args:
            model_id: Model identifier.
            min_context: Minimum context to test.
            max_context: Maximum context to test.

        Returns:
            Dictionary with test results including max working context.
        """
        results = []

        # Binary search for maximum working context
        low = min_context
        high = max_context
        last_good = None

        while low <= high:
            mid = (low + high) // 2

            result = self._test_at_context(model_id, mid)
            results.append(result)

            if result.load_success and result.inference_success:
                last_good = mid
                low = mid + 1
            else:
                high = mid - 1

        return {
            "model_id": model_id,
            "max_working_context": last_good,
            "test_results": [r.to_dict() for r in results],
            "final_status": "completed" if last_good else "failed",
        }
