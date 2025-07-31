#!/usr/bin/env python3
"""Quick test script to demonstrate streaming functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from lmstrix.api.client import LMStudioClient
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.core.models import ModelRegistry


def test_streaming() -> None:
    """Test streaming inference."""
    print("Testing streaming inference...")

    # Initialize components
    client = LMStudioClient(verbose=True)
    registry = ModelRegistry()
    manager = InferenceManager(client=client, registry=registry, verbose=True)

    # Get first available model
    models = registry.list_models()
    if not models:
        print("No models available in registry")
        return

    model = models[0]
    print(f"Using model: {model.id}")

    # Test prompt
    prompt = "Write a haiku about artificial intelligence"

    try:
        print("\n=== Streaming Output ===")
        # Stream the response
        for token in manager.stream_infer(
            model_id=model.id,
            prompt=prompt,
            temperature=0.8,
            out_ctx=100,  # Limit output for demo
        ):
            print(token, end="", flush=True)
        print("\n=== End of Stream ===")

    except Exception as e:
        print(f"Error during streaming: {e}")


if __name__ == "__main__":
    test_streaming()
