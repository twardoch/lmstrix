# this_file: src/lmstrix/__init__.py
"""LMStrix - A toolkit for managing and utilizing models with LM Studio.

This package provides a robust, user-friendly, and extensible toolkit for managing
and running inference with models via the LM Studio local server. The core feature
is an Adaptive Context Optimizer that automatically determines the maximum operational
context length for any given model.
"""

from lmstrix.__version__ import __version__
from lmstrix.api import CompletionResponse, LMStudioClient
from lmstrix.core import (
    ContextOptimizer,
    InferenceEngine,
    Model,
    ModelRegistry,
    PromptResolver,
)
from lmstrix.loaders import load_context, load_model_registry, load_prompts


# High-level convenience class
class LMStrix:
    """High-level interface for LMStrix functionality."""

    def __init__(
        self,
        endpoint: str = "http://localhost:1234/v1",
        models_file: str | None = None,
        verbose: bool = False,
    ):
        """Initialize LMStrix client.

        Args:
            endpoint: LM Studio API endpoint.
            models_file: Path to models JSON file. If None, searches default locations.
            verbose: Enable verbose logging.
        """
        self.endpoint = endpoint
        self.verbose = verbose

        # Initialize components
        self.client = LMStudioClient(endpoint=endpoint, verbose=verbose)
        self.registry = load_model_registry(models_file, verbose=verbose)
        self.engine = InferenceEngine(
            client=self.client,
            model_registry=self.registry,
            verbose=verbose,
        )
        self.optimizer = ContextOptimizer(client=self.client, verbose=verbose)
        self.prompt_resolver = PromptResolver(verbose=verbose)

    async def list_models(self) -> list[Model]:
        """List all available models."""
        return self.registry.list_models()

    async def get_model(self, model_id: str) -> Model | None:
        """Get a specific model by ID."""
        return self.registry.get_model(model_id)

    async def infer(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ):
        """Run inference on a model."""
        return await self.engine.infer(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

    async def optimize_context(self, model_id: str):
        """Find optimal context size for a model."""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        return await self.optimizer.find_optimal_context(model)


__all__ = [
    "__version__",
    # High-level interface
    "LMStrix",
    # Core classes
    "Model",
    "ModelRegistry",
    "InferenceEngine",
    "ContextOptimizer",
    "PromptResolver",
    # API classes
    "LMStudioClient",
    "CompletionResponse",
    # Convenience functions
    "load_model_registry",
    "load_prompts",
    "load_context",
]
