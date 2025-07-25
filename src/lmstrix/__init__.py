# this_file: src/lmstrix/__init__.py
"""High-level API for LMStrix functionality."""

import asyncio
from importlib.metadata import PackageNotFoundError, version
from typing import List

from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference import InferenceEngine, InferenceResult
from lmstrix.core.models import Model
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)

try:
    from lmstrix._version import __version__
except ImportError:
    try:
        __version__ = version("lmstrix")
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"


class LMStrix:
    """Provides a high-level, simplified interface to LMStrix's core features."""

    def __init__(self, verbose: bool = False):
        """Initializes the LMStrix API wrapper.

        Args:
            verbose: Enable verbose logging throughout operations.
        """
        self.verbose = verbose

    def scan(self) -> list[Model]:
        """Scans for LM Studio models, updates the registry, and returns all models."""
        registry = scan_and_update_registry(verbose=self.verbose)
        return registry.list_models()

    def list_models(self) -> list[Model]:
        """Lists all models currently in the registry."""
        registry = load_model_registry(verbose=self.verbose)
        return registry.list_models()

    def test_model(self, model_id: str) -> Model:
        """Runs the context-length test on a specific model and returns the updated model data."""
        registry = load_model_registry(verbose=self.verbose)
        model = registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model '{model_id}' not found in the registry.")

        tester = ContextTester()
        updated_model = asyncio.run(tester.test_model(model))

        registry.update_model(updated_model.id, updated_model)
        save_model_registry(registry)

        return updated_model

    async def infer(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = -1,
        temperature: float = 0.7,
    ) -> InferenceResult:
        """Runs inference on a specified model.

        Args:
            model_id: The ID of the model to use.
            prompt: The prompt to send to the model.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature.

        Returns:
            An InferenceResult object with the response and metadata.
        """
        registry = load_model_registry(verbose=self.verbose)
        engine = InferenceEngine(model_registry=registry, verbose=self.verbose)
        return await engine.infer(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )


__all__ = [
    "InferenceResult",
    "LMStrix",
    "Model",
    "__version__",
]
