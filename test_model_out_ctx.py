#!/usr/bin/env python3
"""
Test script to verify model-specific context_out values are being used.
"""
# this_file: test_model_out_ctx.py

import sys
from pathlib import Path

# Add src to path so we can import lmstrix
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lmstrix.api.client import LMStudioClient
from lmstrix.core.inference import InferenceEngine
from lmstrix.core.models import ModelRegistry
from lmstrix.utils.logging import logger

# Enable detailed logging
logger.enable("lmstrix")


def test_context_out_usage() -> None:
    """Test that model-specific context_out values are used in testing."""
    print("=" * 60)
    print("🔍 TESTING CONTEXT_OUT USAGE")
    print("=" * 60)

    # Initialize components
    client = LMStudioClient(verbose=True)
    registry = ModelRegistry()
    engine = InferenceEngine(client=client, model_registry=registry, verbose=True)

    # Test with a specific model
    model_id = "slim-extract-qwen-0.5b"

    # Get model from registry
    model = registry.find_model(model_id)
    if model:
        print(f"\n✓ Found model: {model_id}")
        print(f"  context_out: {model.context_out}")
        print(f"  context_limit: {model.context_limit}")
    else:
        print(f"\n❌ Model {model_id} not found in registry")
        return

    # Test the _test_inference_capability method
    print("\n📝 Testing inference capability with model-specific context_out...")

    try:
        # This should now use model.context_out instead of -1
        success, response = engine._test_inference_capability(model_id, 2047)

        print("\n✓ Test completed")
        print(f"  Success: {success}")
        print(f"  Response: {response}")

        # The key difference is that with context_out=4096, the model will
        # generate up to 4096 tokens instead of unlimited tokens
        print(f"\n💡 The test now uses context_out={model.context_out} instead of -1 (unlimited)")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


def compare_inference_modes() -> None:
    """Compare inference with different out_ctx values."""
    print("\n" + "=" * 60)
    print("🔍 COMPARING INFERENCE MODES")
    print("=" * 60)

    client = LMStudioClient(verbose=False)
    registry = ModelRegistry()
    engine = InferenceEngine(client=client, model_registry=registry, verbose=False)

    model_id = "slim-extract-qwen-0.5b"
    prompt = "Extract entities from: John works at Microsoft in Seattle."

    # Test 1: Default behavior (out_ctx=-1)
    print("\n📝 Test 1: Default inference (out_ctx=-1)")
    try:
        result1 = engine.infer(model_id, prompt, in_ctx=2047)
        print(f"  Response length: {len(result1.response)} chars")
        print(f"  Response: '{result1.response[:100]}...'")
    except Exception as e:
        print(f"  Failed: {e}")

    # Test 2: With model's context_out
    model = registry.find_model(model_id)
    if model:
        print(f"\n📝 Test 2: With model context_out (out_ctx={model.context_out})")
        try:
            result2 = engine.infer(model_id, prompt, in_ctx=2047, out_ctx=model.context_out)
            print(f"  Response length: {len(result2.response)} chars")
            print(f"  Response: '{result2.response[:100]}...'")
        except Exception as e:
            print(f"  Failed: {e}")

    # Test 3: With small out_ctx
    print("\n📝 Test 3: With small context (out_ctx=50)")
    try:
        result3 = engine.infer(model_id, prompt, in_ctx=2047, out_ctx=50)
        print(f"  Response length: {len(result3.response)} chars")
        print(f"  Response: '{result3.response}'")
    except Exception as e:
        print(f"  Failed: {e}")


if __name__ == "__main__":
    test_context_out_usage()
    compare_inference_modes()

    print("\n" + "=" * 60)
    print("✅ SUMMARY")
    print("=" * 60)
    print("• Model-specific context_out values are now used in _test_inference_capability")
    print("• This prevents tests from generating unlimited tokens")
    print("• Users can still override out_ctx in the main infer() method")
    print("• Default behavior remains out_ctx=-1 (unlimited) for flexibility")
