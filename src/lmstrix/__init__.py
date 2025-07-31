"""High-level API for LMStrix functionality."""

from importlib.metadata import PackageNotFoundError, version

from lmstrix.api.exceptions import ModelNotFoundError
from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.core.models import Model
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)
from lmstrix.utils.context_parser import get_model_max_context, parse_out_ctx
from lmstrix.utils.logging import logger

try:
    from lmstrix._version import __version__
except ImportError:
    try:
        __version__ = version("lmstrix")
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"


class LMStrix:
    """High-level interface to LMStrix's core features.

    This class provides a simplified API for common LMStrix operations including
    model scanning, listing, context testing, and inference. It handles the
    underlying async operations and registry management automatically.

    Example:
        >>> lms = LMStrix(verbose=True)
        >>> models = lms.scan()  # Discover all LM Studio models
        >>> lms.test_model(models[0].id)  # Test context limits
        >>> lms.infer(models[0].id, "Hello, world!")
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initializes the LMStrix API wrapper.

        Args:
            verbose: Enable verbose logging throughout operations.
        """
        self.verbose = verbose

    def scan(self) -> list[Model]:
        """Scan for LM Studio models and update the registry.

        Discovers all models currently available in LM Studio, updates the
        local registry with any new models found, and returns the complete
        list of models.

        Returns:
            List of all Model objects found in LM Studio.

        Example:
            >>> lms = LMStrix()
            >>> models = lms.scan()
            >>> logger.info(f"Found {len(models)} models")
        """
        registry = scan_and_update_registry(verbose=self.verbose)
        return registry.list_models()

    def list_models(self) -> list[Model]:
        """List all models currently in the registry.

        Returns the cached list of models from the local registry without
        performing a new scan. Use scan() to update the registry first.

        Returns:
            List of Model objects from the local registry.

        Example:
            >>> lms = LMStrix()
            >>> models = lms.list_models()
            >>> for model in models:
            ...     logger.info(f"{model.id}: {model.context_test_status}")
        """
        registry = load_model_registry(verbose=self.verbose)
        return registry.list_models()

    def test_model(self, model_id: str) -> Model:
        """Test a model's true operational context limits.

        Performs a binary search to find the maximum context size that the
        model can reliably handle on the current hardware. The test uses
        a simple prompt ("2+2=") padded with filler text to various lengths
        and validates that the model returns the correct answer ("4").

        Args:
            model_id: The ID of the model to test.

        Returns:
            Updated Model object with test results.

        Raises:
            ValueError: If the model is not found in the registry.

        Example:
            >>> lms = LMStrix()
            >>> model = lms.test_model("llama-model-id")
            >>> logger.info(f"Max context: {model.tested_max_context} tokens")
        """
        registry = load_model_registry(verbose=self.verbose)
        model = registry.get_model(model_id)
        if not model:
            available_models = [m.id for m in registry.list_models()]
            raise ModelNotFoundError(model_id, available_models)

        tester = ContextTester()
        updated_model = tester.test_model(model)

        registry.update_model(updated_model.id, updated_model)
        save_model_registry(registry)

        return updated_model

    def infer(
        self,
        model_id: str,
        prompt: str,
        out_ctx: int | str = -1,
        temperature: float = 0.7,
    ) -> dict:
        """Runs inference on a specified model.

        Args:
            model_id: The ID of the model to use.
            prompt: The prompt to send to the model.
            out_ctx: The maximum number of tokens to generate (-1 for unlimited, or "50%" for percentage).
            temperature: The sampling temperature.

        Returns:
            A dictionary with inference results:
                - model_id: str
                - prompt: str
                - response: str
                - tokens_used: int
                - inference_time: float
                - error: str | None
                - succeeded: bool
        """
        registry = load_model_registry(verbose=self.verbose)

        # Parse out_ctx if it's a percentage
        if isinstance(out_ctx, str) and out_ctx != "-1":
            model = registry.find_model(model_id)
            if not model:
                raise ModelNotFoundError(model_id, [m.id for m in registry.list_models()])

            max_context = get_model_max_context(model, use_tested=True)
            if not max_context:
                max_context = model.context_limit
            out_ctx = parse_out_ctx(out_ctx, max_context)

        manager = InferenceManager(registry=registry, verbose=self.verbose)
        return manager.infer(
            model_id=model_id,
            prompt=prompt,
            out_ctx=out_ctx,
            temperature=temperature,
        )


__all__ = [
    "LMStrix",
    "Model",
    "__version__",
]
