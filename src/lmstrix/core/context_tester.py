"""Context testing functionality for discovering true model limits."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from lmstrix.api import LMStudioClient
from lmstrix.api.exceptions import ModelLoadError
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

    def is_valid_response(self, expected: str) -> bool:
        """Check if response matches expected output."""
        return self.response.strip() == expected.strip()


class ContextTester:
    """Tests models to find their true operational context limits.

    Uses a binary search algorithm to efficiently discover the maximum context
    size that a model can reliably handle. The test sends a simple mathematical
    prompt ("2+2=") padded with filler text to reach various context sizes,
    and validates that the model returns the correct answer ("4").

    Attributes:
        client: LMStudioClient instance for model operations.
        test_prompt: The prompt used for testing (default: "2+2=").
        expected_response: The expected response (default: "4").
    """

    def __init__(self, client: LMStudioClient | None = None) -> None:
        """Initialize context tester."""
        self.client = client or LMStudioClient()
        self.test_prompt = "2+2="
        self.expected_response = "4"

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
        llm = None
        try:
            # Add a small delay to avoid rapid operations
            import asyncio

            await asyncio.sleep(0.5)

            llm = self.client.load_model(model_id, context_len=context_size)
            logger.debug(f"Model {model_id} loaded successfully at {context_size}.")

            response = await self.client.acompletion(
                llm=llm,
                prompt=self.test_prompt,
                max_tokens=10,
                temperature=0.0,
                model_id=model_id,
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
            result = ContextTestResult(
                context_size=context_size,
                load_success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Inference failed for {model_id} at context {context_size}: {e}")
            result = ContextTestResult(
                context_size=context_size,
                load_success=True,
                inference_success=False,
                prompt=self.test_prompt,
                error=str(e),
            )
        finally:
            if llm:
                llm.unload()
                logger.debug(f"Model {model_id} unloaded.")
                # Add delay after unload to ensure clean state
                await asyncio.sleep(0.5)

        self._log_result(log_path, result)
        return result

    async def test_model(
        self,
        model: Model,
        min_context: int = 2048,
        max_context: int | None = None,
    ) -> Model:
        """Run full context test on a model using binary search."""
        logger.info(f"Starting context test for {model.id}")
        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()

        max_context = max_context or model.context_limit
        log_path = get_context_test_log_path(model.id)

        logger.info(f"Testing range for {model.id}: {min_context} - {max_context}")

        left, right = min_context, max_context
        best_working_context = 0

        try:
            while left <= right:
                mid = (left + right) // 2
                if mid == 0:
                    break

                result = await self._test_at_context(model.id, mid, log_path)

                if (
                    result.load_success
                    and result.inference_success
                    and result.is_valid_response(self.expected_response)
                ):
                    best_working_context = mid
                    left = mid + 1  # Try for a larger context
                else:
                    right = mid - 1  # This context failed, try smaller

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

        except Exception as e:
            logger.error(f"An unexpected error occurred during context test for {model.id}: {e}")
            model.context_test_status = ContextTestStatus.FAILED
            model.error_msg = str(e)

        return model
