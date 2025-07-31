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
