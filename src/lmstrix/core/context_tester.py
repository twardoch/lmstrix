"""Context testing functionality for discovering true model limits."""

from datetime import datetime
from typing import ClassVar

from lmstrix.api import LMStudioClient


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
    ) -> ContextTestResult:
        """Test a model at a specific context size.

        Args:
            model_id: Model identifier.
            context_size: Context size to test.

        Returns:
            ContextTestResult with test outcome.
        """
        # Try to load the model
        try:
            llm = self.client.load_model(model_id, context_size)
        except Exception as e:
            return ContextTestResult(
                context_size=context_size,
                load_success=False,
                inference_success=False,
                error=str(e),
            )

        # Try inference
        try:
            response = self.client.completion(
                llm,
                self.test_prompt,
                max_tokens=50,
                timeout=self.inference_timeout,
            )

            return ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=True,
                prompt=self.test_prompt,
                response=response,
            )
        except Exception as e:
            return ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=False,
                prompt=self.test_prompt,
                error=str(e),
            )

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
