"""Adaptive context optimizer for finding optimal context window sizes."""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from lmstrix.api.client import LMStudioClient
from lmstrix.api.exceptions import InferenceError, ModelLoadError
from lmstrix.core.models import Model
from lmstrix.utils.logging import logger


class OptimizationResult(BaseModel):
    """Result from context optimization."""

    model_id: str = Field(..., description="ID of the model")
    declared_limit: int = Field(..., description="Model's declared context limit")
    optimal_context: int = Field(..., description="Optimal context size found")
    attempts: int = Field(0, description="Number of attempts made")
    error: str | None = Field(None, description="Error message if optimization failed")

    @property
    def succeeded(self) -> bool:
        """Check if optimization was successful."""
        return self.error is None and self.optimal_context > 0


class ContextOptimizer:
    """Finds the maximum effective context window for models."""

    def __init__(
        self,
        client: LMStudioClient | None = None,
        cache_file: Path | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize the context optimizer."""
        self.client = client or LMStudioClient(verbose=verbose)
        self.cache_file = cache_file or Path("context_cache.json")
        self.verbose = verbose
        self._cache: dict[str, int] = self._load_cache()

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def _load_cache(self) -> dict[str, int]:
        """Load cached optimization results."""
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text())
                return data if isinstance(data, dict) else {}
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Save optimization results to cache."""
        try:
            self.cache_file.write_text(json.dumps(self._cache, indent=2))
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def _generate_test_prompt(self, size: int) -> str:
        """Generate a test prompt of approximately the given token size."""
        word_count = int(size / 1.3)
        base_text = "The quick brown fox jumps over the lazy dog. "
        words_per_base = len(base_text.split())
        repetitions = max(1, word_count // words_per_base)

        prompt = base_text * repetitions
        return f"Please summarize the following text:\n\n{prompt}"

    def _test_context_size(
        self,
        model_id: str,
        context_size: int,
        test_prompt: str | None = None,
    ) -> tuple[bool, str]:
        """Test if a model can handle a specific context size."""
        if test_prompt is None:
            test_prompt = self._generate_test_prompt(context_size)

        try:
            # Load the model with specified context size
            llm = self.client.load_model(model_id, context_len=context_size)

            response = self.client.completion(
                llm=llm,
                prompt=test_prompt,
                out_ctx=50,
                temperature=0.1,
                model_id=model_id,
            )

            # Unload the model after testing
            if hasattr(llm, "unload"):
                llm.unload()

            return bool(response.content), ""
        except (ModelLoadError, InferenceError) as e:
            return False, str(e)

    def find_optimal_context(
        self,
        model: Model,
        initial_size: int | None = None,
        min_size: int = 2048,
        max_attempts: int = 20,
    ) -> OptimizationResult:
        """Find the optimal context size for a model using binary search."""
        model_id = model.id
        logger.info(f"Starting context optimization for {model_id}")

        if model_id in self._cache:
            logger.info(f"Using cached result for {model_id}: {self._cache[model_id]}")
            return OptimizationResult(
                model_id=model_id,
                declared_limit=model.context_limit,
                optimal_context=self._cache[model_id],
                attempts=0,
                error=None,
            )

        high = initial_size or model.context_limit
        low = min_size
        optimal = low
        attempts = 0

        while low <= high and attempts < max_attempts:
            attempts += 1
            mid = (low + high) // 2
            logger.debug(f"Testing context size {mid} (attempt {attempts})")

            success, error = self._test_context_size(model_id, mid)

            if success:
                optimal = mid
                low = mid + 1
                logger.debug(f"Success at {mid}, trying higher")
            else:
                high = mid - 1
                logger.debug(f"Failed at {mid}: {error}, trying lower")

        self._cache[model_id] = optimal
        self._save_cache()

        logger.info(f"Optimal context for {model_id}: {optimal} (from {model.context_limit})")

        return OptimizationResult(
            model_id=model_id,
            declared_limit=model.context_limit,
            optimal_context=optimal,
            attempts=attempts,
            error=None,
        )
