#!/usr/bin/env python3
"""
Debug script to compare lmstrix infer vs direct lmstudio calls.
Focuses on slim-extract-qwen-0.5b model to identify inference issues.
"""
# this_file: debug_inference.py

import sys
import time
from pathlib import Path

# Add src to path so we can import lmstrix
sys.path.insert(0, str(Path(__file__).parent / "src"))

import lmstudio

from lmstrix.api.client import LMStudioClient
from lmstrix.core.inference import InferenceEngine
from lmstrix.core.models import ModelRegistry
from lmstrix.utils.logging import logger

# Enable detailed logging
logger.enable("lmstrix")

MODEL_ID = "slim-extract-qwen-0.5b"
TEST_CONTEXT = 2047
TEST_PROMPT = "Write 'ninety-six' as a number using only digits"


def print_separator(title: str) -> None:
    """Print a nice separator."""
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)


def test_direct_lmstudio() -> bool | None:
    """Test direct lmstudio calls without lmstrix wrapper."""
    print_separator("DIRECT LMSTUDIO TEST")

    try:
        # First, check if model exists
        downloaded_models = lmstudio.list_downloaded_models()
        model_found = False
        actual_model_key = None

        print(f"🔍 Looking for model: {MODEL_ID}")
        for model in downloaded_models:
            info = model.info
            model_key = getattr(info, "model_key", getattr(info, "modelKey", ""))
            display_name = getattr(info, "display_name", getattr(info, "displayName", ""))
            path = getattr(info, "path", "")

            print(f"   Available: {model_key} (display: {display_name})")

            if MODEL_ID in (model_key, display_name) or MODEL_ID in str(path):
                model_found = True
                actual_model_key = model_key
                print(f"   ✓ Found match: {MODEL_ID} -> {actual_model_key}")
                break

        if not model_found:
            print(f"❌ Model {MODEL_ID} not found in downloaded models")
            return False

        # Try direct lmstudio loading and inference
        print("\n🚀 Loading model directly with lmstudio.llm()...")
        print(f"   Model Key: {actual_model_key}")
        print(f"   Context: {TEST_CONTEXT}")

        # Unload any existing models first
        try:
            lmstudio.unload()
            time.sleep(0.5)
        except:
            pass

        # Load with explicit config
        config = {"contextLength": TEST_CONTEXT}
        llm = lmstudio.llm(actual_model_key, config=config)

        print("✓ Model loaded successfully")
        print(f"   LLM object: {type(llm)}")
        print(f"   LLM ID: {getattr(llm, 'id', 'N/A')}")
        print(f"   Model Key: {getattr(llm, 'model_key', 'N/A')}")

        if hasattr(llm, "config"):
            print(f"   Config: {llm.config}")

        # Test simple inference
        print(f"\n📝 Testing inference with prompt: '{TEST_PROMPT}'")

        inference_config = {
            "maxTokens": 10,
            "temperature": 0.1,
            "topKSampling": 40,
            "topPSampling": 0.95,
            "repeatPenalty": 1.1,
            "minPSampling": 0.05,
        }

        start_time = time.time()
        response = llm.complete(TEST_PROMPT, config=inference_config)
        inference_time = time.time() - start_time

        print(f"✓ Inference completed in {inference_time:.2f}s")
        print(f"   Response type: {type(response)}")

        # Extract content
        content = ""
        if hasattr(response, "content"):
            content = response.content
        elif hasattr(response, "text"):
            content = response.text
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)

        print(f"   Response content: '{content.strip()}'")
        print(f"   Success: {'96' in content}")

        # Check stats if available
        if hasattr(response, "stats") and response.stats:
            stats = response.stats
            print(f"   Stats available: {dir(stats)}")
            if hasattr(stats, "tokens_per_second"):
                print(f"   Tokens/sec: {stats.tokens_per_second}")

        # Unload
        try:
            llm.unload()
            print("✓ Model unloaded successfully")
        except Exception as e:
            print(f"⚠️  Unload warning: {e}")

        return True

    except Exception as e:
        print(f"❌ Direct lmstudio test failed: {e}")
        print(f"   Error type: {type(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_lmstrix_client() -> bool | None:
    """Test lmstrix client calls."""
    print_separator("LMSTRIX CLIENT TEST")

    try:
        client = LMStudioClient(verbose=True)

        # Test model listing
        models = client.list_models()
        print(f"🔍 Found {len(models)} models via lmstrix client")

        target_model = None
        for model in models:
            if MODEL_ID in model.get("id", ""):
                target_model = model
                print(f"   ✓ Found target model: {model}")
                break

        if not target_model:
            print(f"❌ Model {MODEL_ID} not found via lmstrix client")
            return False

        # Test model loading
        print("\n🚀 Loading model via lmstrix client...")
        llm = client.load_model_by_id(MODEL_ID, TEST_CONTEXT)

        print("✓ Model loaded via client")
        print(f"   LLM object: {type(llm)}")

        # Test completion
        print("\n📝 Testing completion via lmstrix client...")
        response = client.completion(
            llm=llm, prompt=TEST_PROMPT, out_ctx=10, temperature=0.1, model_id=MODEL_ID
        )

        print("✓ Completion via client successful")
        print(f"   Response: {response}")
        print(f"   Content: '{response.content.strip()}'")
        print(f"   Success: {'96' in response.content}")

        # Unload
        try:
            llm.unload()
            print("✓ Model unloaded via client")
        except Exception as e:
            print(f"⚠️  Client unload warning: {e}")

        return True

    except Exception as e:
        print(f"❌ LMStrix client test failed: {e}")
        print(f"   Error type: {type(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_lmstrix_inference_engine():
    """Test lmstrix inference engine."""
    print_separator("LMSTRIX INFERENCE ENGINE TEST")

    try:
        # Initialize registry and engine
        registry = ModelRegistry()
        engine = InferenceEngine(verbose=True, model_registry=registry)

        # Check if model is in registry
        model = registry.find_model(MODEL_ID)
        if not model:
            print(f"❌ Model {MODEL_ID} not found in registry")
            # Try to scan for models
            print("🔍 Scanning for models...")
            from lmstrix.core.scanner import ModelScanner

            scanner = ModelScanner(registry=registry)
            scanner.scan_models()
            model = registry.find_model(MODEL_ID)

        if not model:
            print(f"❌ Model {MODEL_ID} still not found after scan")
            return False

        print(f"✓ Model found in registry: {model}")

        # Test inference
        print("\n📝 Testing inference via engine...")
        result = engine.infer(
            model_id=MODEL_ID, prompt=TEST_PROMPT, in_ctx=TEST_CONTEXT, out_ctx=10, temperature=0.1
        )

        print(f"✓ Inference engine result: {result}")
        print(f"   Success: {result.succeeded}")
        print(f"   Response: '{result.response.strip()}'")
        print(f"   Error: {result.error}")
        print(f"   Inference time: {result.inference_time:.2f}s")

        return result.succeeded

    except Exception as e:
        print(f"❌ LMStrix inference engine test failed: {e}")
        print(f"   Error type: {type(e)}")
        import traceback

        traceback.print_exc()
        return False


def main() -> None:
    """Run all diagnostic tests."""
    print_separator("LMSTRIX INFERENCE DIAGNOSTIC")
    print(f"Target Model: {MODEL_ID}")
    print(f"Test Context: {TEST_CONTEXT}")
    print(f"Test Prompt: '{TEST_PROMPT}'")

    results = {}

    # Test 1: Direct lmstudio
    results["direct_lmstudio"] = test_direct_lmstudio()

    # Test 2: LMStrix client
    results["lmstrix_client"] = test_lmstrix_client()

    # Test 3: LMStrix inference engine
    results["lmstrix_engine"] = test_lmstrix_inference_engine()

    # Summary
    print_separator("TEST SUMMARY")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")

    # Analysis
    print("\n🔍 ANALYSIS:")
    if results["direct_lmstudio"] and not results["lmstrix_client"]:
        print("   • Direct lmstudio works, but lmstrix client fails")
        print("   • Issue likely in LMStudioClient wrapper")
    elif results["lmstrix_client"] and not results["lmstrix_engine"]:
        print("   • Client works, but inference engine fails")
        print("   • Issue likely in InferenceEngine logic")
    elif not results["direct_lmstudio"]:
        print("   • Even direct lmstudio fails")
        print("   • Issue with model itself or LM Studio setup")
    elif all(results.values()):
        print("   • All tests pass - issue may be context-specific")
    else:
        print("   • Mixed results - need deeper investigation")


if __name__ == "__main__":
    main()
