# this_file: src/lmstrix/core/context_tester.py
"""Context testing functionality for discovering true model limits."""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from lmstrix.api import LMStudioClient
from lmstrix.core.models import ContextTestStatus, Model
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
    ):
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

    def is_valid_response(self, expected: str) -> bool:
        """Check if response matches expected output."""
        return self.response.strip() == expected.strip()


class ContextTester:
    """Tests models to find their true operational context limits."""

    def __init__(self, client: LMStudioClient | None = None):
        """Initialize context tester.

        Args:
            client: LM Studio client instance. If None, creates default.
        """
        self.client = client or LMStudioClient()
        self.test_prompt = "2+2="
        self.expected_response = "4"

    def _log_result(self, log_path: Path, result: ContextTestResult) -> None:
        """Append test result to log file."""
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    async def _test_at_context(
        self,
        model: Model,
        context_size: int,
        log_path: Path,
    ) -> ContextTestResult:
        """Test model at specific context size.

        Args:
            model: Model to test.
            context_size: Context size to test.
            log_path: Path to log results.

        Returns:
            Test result.
        """
        logger.debug(f"Testing {model.id} at context size {context_size}")

        # First try to load the model with specified context
        try:
            # In real implementation, this would use lmstudio package
            # For now, we simulate by checking if context is reasonable
            if context_size > model.context_limit:
                raise ValueError(f"Context {context_size} exceeds limit {model.context_limit}")

            # Simulate load success based on some heuristic
            # In reality, this would actually try to load the model
            load_success = True

        except Exception as e:
            result = ContextTestResult(
                context_size=context_size,
                load_success=False,
                error=str(e),
            )
            self._log_result(log_path, result)
            return result

        # If load succeeded, try inference
        try:
            # Test with simple prompt
            messages = [{"role": "user", "content": self.test_prompt}]

            # Override context in the request
            response = await self.client.acompletion(
                model_id=model.id,
                messages=messages,
                max_tokens=10,
                temperature=0.0,
                # This would need to pass context_length parameter
                # For now we simulate
            )

            response_text = response.choices[0].message.content.strip()

            result = ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=True,
                prompt=self.test_prompt,
                response=response_text,
            )

        except Exception as e:
            result = ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=False,
                prompt=self.test_prompt,
                error=str(e),
            )

        self._log_result(log_path, result)
        return result

    async def find_max_loadable_context(
        self,
        model: Model,
        min_context: int = 32,
        max_context: int | None = None,
    ) -> tuple[int, Path]:
        """Find maximum context size at which model loads.

        Uses binary search to efficiently find the limit.

        Args:
            model: Model to test.
            min_context: Minimum context to test.
            max_context: Maximum context to test (defaults to model's declared limit).

        Returns:
            Tuple of (max_loadable_context, log_path).
        """
        max_context = max_context or model.context_limit
        log_path = get_context_test_log_path(model.id)

        logger.info(f"Finding max loadable context for {model.id}")
        logger.info(f"Testing range: {min_context} - {max_context}")

        left, right = min_context, max_context
        best_loadable = 0

        while left <= right:
            mid = (left + right) // 2

            result = await self._test_at_context(model, mid, log_path)

            if result.load_success:
                best_loadable = mid
                left = mid + 1
            else:
                right = mid - 1

        logger.info(f"Max loadable context for {model.id}: {best_loadable}")
        return best_loadable, log_path

    async def find_max_working_context(
        self,
        model: Model,
        min_context: int = 32,
        max_context: int | None = None,
    ) -> tuple[int, int, Path]:
        """Find maximum context size that produces correct output.

        Args:
            model: Model to test.
            min_context: Minimum context to test.
            max_context: Maximum context to test.

        Returns:
            Tuple of (max_working_context, max_loadable_context, log_path).
        """
        # First find max loadable
        max_loadable, log_path = await self.find_max_loadable_context(
            model, min_context, max_context
        )

        if max_loadable == 0:
            return 0, 0, log_path

        logger.info(f"Finding max working context for {model.id}")
        logger.info(f"Testing range: {min_context} - {max_loadable}")

        # Binary search for max working context
        left, right = min_context, max_loadable
        best_working = 0

        while left <= right:
            mid = (left + right) // 2

            result = await self._test_at_context(model, mid, log_path)

            if result.inference_success and result.is_valid_response(self.expected_response):
                best_working = mid
                left = mid + 1
            else:
                right = mid - 1

        logger.info(f"Max working context for {model.id}: {best_working}")
        return best_working, max_loadable, log_path

    async def test_model(
        self,
        model: Model,
        min_context: int = 32,
        max_context: int | None = None,
    ) -> Model:
        """Run full context test on a model.

        Args:
            model: Model to test.
            min_context: Minimum context to test.
            max_context: Maximum context to test.

        Returns:
            Updated model with test results.
        """
        logger.info(f"Starting context test for {model.id}")

        # Update status
        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()

        try:
            # Run the test
            max_working, max_loadable, log_path = await self.find_max_working_context(
                model, min_context, max_context
            )

            # Update model with results
            model.tested_max_context = max_working
            model.loadable_max_context = max_loadable
            model.context_test_log = str(log_path)
            model.context_test_status = ContextTestStatus.COMPLETED

            logger.info(
                f"Context test completed for {model.id}: "
                f"working={max_working}, loadable={max_loadable}"
            )

        except Exception as e:
            logger.error(f"Context test failed for {model.id}: {e}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = str(e)

        return model
