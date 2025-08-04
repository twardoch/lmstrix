#!/usr/bin/env python3
"""
Debug script to understand the test logic differences.
Shows exactly what the test prompts produce vs expectations.
"""
# this_file: debug_test_logic.py

import sys
import time
from pathlib import Path

# Add src to path so we can import lmstrix
sys.path.insert(0, str(Path(__file__).parent / "src"))

import builtins
import contextlib

import lmstudio

from lmstrix.utils.logging import logger

# Enable detailed logging
logger.enable("lmstrix")

MODEL_ID = "slim-extract-qwen-0.5b"
TEST_CONTEXT = 2047


def test_both_prompts() -> None:
    """Test both standard prompts and show why tests fail."""
    print("=" * 80)
    print("🔍 TESTING BOTH STANDARD PROMPTS")
    print("=" * 80)

    # Test prompts from the inference engine
    test_prompt_1 = "Write 'ninety-six' as a number using only digits"
    test_prompt_2 = "2+3="

    try:
        # Unload and load model (try unloading any existing models)
        try:
            loaded_models = lmstudio.list_loaded_models()
            for llm_obj in loaded_models:
                with contextlib.suppress(builtins.BaseException):
                    llm_obj.unload()
            time.sleep(0.5)
        except:
            pass

        config = {"contextLength": TEST_CONTEXT}
        llm = lmstudio.llm(MODEL_ID, config=config)

        print(f"✓ Model loaded: {MODEL_ID}")

        # Test 1: Number words to digits
        print(f"\n📝 TEST 1: '{test_prompt_1}'")
        print("Expected: Response containing '96'")

        inference_config = {
            "maxTokens": 10,
            "temperature": 0.1,
            "topKSampling": 40,
            "topPSampling": 0.95,
            "repeatPenalty": 1.1,
            "minPSampling": 0.05,
        }

        response_1 = llm.complete(test_prompt_1, config=inference_config)
        content_1 = response_1.content if hasattr(response_1, "content") else str(response_1)

        test_1_pass = "96" in content_1
        print(f"Actual: '{content_1.strip()}'")
        print(f"Contains '96': {test_1_pass} {'✓' if test_1_pass else '✗'}")

        # Test 2: Simple arithmetic
        print(f"\n📝 TEST 2: '{test_prompt_2}'")
        print("Expected: Response containing '5'")

        response_2 = llm.complete(test_prompt_2, config=inference_config)
        content_2 = response_2.content if hasattr(response_2, "content") else str(response_2)

        test_2_pass = "5" in content_2
        print(f"Actual: '{content_2.strip()}'")
        print(f"Contains '5': {test_2_pass} {'✓' if test_2_pass else '✗'}")

        # Overall result
        overall_pass = test_1_pass or test_2_pass
        print(f"\n🎯 OVERALL RESULT: {overall_pass} {'✅ PASS' if overall_pass else '❌ FAIL'}")
        print("Logic: Pass if ANY test passes (test_1_pass OR test_2_pass)")

        # Test different prompts that might work better
        print("\n" + "=" * 80)
        print("🧪 TESTING ALTERNATIVE PROMPTS")
        print("=" * 80)

        alternative_prompts = [
            ("Say hello", "hello"),
            ("What is 96?", "96"),
            ("Answer: 5", "5"),
            ("The number ninety-six is:", "96"),
            ("Complete: 2+3=", "5"),
        ]

        for prompt, expected in alternative_prompts:
            print(f"\n📝 PROMPT: '{prompt}'")
            print(f"Looking for: '{expected}'")

            response = llm.complete(prompt, config=inference_config)
            content = response.content if hasattr(response, "content") else str(response)

            contains_expected = expected.lower() in content.lower()
            print(f"Response: '{content.strip()}'")
            print(f"Contains '{expected}': {contains_expected} {'✓' if contains_expected else '✗'}")

        llm.unload()

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


def test_with_more_tokens() -> None:
    """Test with more output tokens to see if model just needs more space."""
    print("\n" + "=" * 80)
    print("🔍 TESTING WITH MORE OUTPUT TOKENS")
    print("=" * 80)

    try:
        try:
            loaded_models = lmstudio.list_loaded_models()
            for llm_obj in loaded_models:
                with contextlib.suppress(builtins.BaseException):
                    llm_obj.unload()
            time.sleep(0.5)
        except:
            pass

        config = {"contextLength": TEST_CONTEXT}
        llm = lmstudio.llm(MODEL_ID, config=config)

        test_prompts = [
            "Write 'ninety-six' as a number using only digits",
            "2+3=",
        ]

        token_limits = [10, 20, 50]

        for prompt in test_prompts:
            print(f"\n📝 PROMPT: '{prompt}'")

            for max_tokens in token_limits:
                print(f"\n  🎯 Max tokens: {max_tokens}")

                inference_config = {
                    "maxTokens": max_tokens,
                    "temperature": 0.1,
                    "topKSampling": 40,
                    "topPSampling": 0.95,
                    "repeatPenalty": 1.1,
                    "minPSampling": 0.05,
                }

                response = llm.complete(prompt, config=inference_config)
                content = response.content if hasattr(response, "content") else str(response)

                print(f"  Response: '{content.strip()}'")

                # Check for expected answers
                if "ninety-six" in prompt:
                    contains_96 = "96" in content
                    print(f"  Contains '96': {contains_96} {'✓' if contains_96 else '✗'}")
                elif "2+3=" in prompt:
                    contains_5 = "5" in content
                    print(f"  Contains '5': {contains_5} {'✓' if contains_5 else '✗'}")

        llm.unload()

    except Exception as e:
        print(f"❌ Error during extended testing: {e}")


def test_other_models() -> None:
    """Test a few other models to see if they behave differently."""
    print("\n" + "=" * 80)
    print("🔍 TESTING OTHER SLIM MODELS FOR COMPARISON")
    print("=" * 80)

    other_models = [
        "slim-extract-qwen-1.5b",
        "slim-extract-tool",
        # Add any other models you want to test
    ]

    test_prompt = "Write 'ninety-six' as a number using only digits"

    for model_id in other_models:
        print(f"\n🤖 MODEL: {model_id}")

        try:
            try:
                loaded_models = lmstudio.list_loaded_models()
                for llm_obj in loaded_models:
                    with contextlib.suppress(builtins.BaseException):
                        llm_obj.unload()
                time.sleep(0.5)
            except:
                pass

            config = {"contextLength": TEST_CONTEXT}
            llm = lmstudio.llm(model_id, config=config)

            inference_config = {
                "maxTokens": 20,
                "temperature": 0.1,
                "topKSampling": 40,
                "topPSampling": 0.95,
                "repeatPenalty": 1.1,
                "minPSampling": 0.05,
            }

            response = llm.complete(test_prompt, config=inference_config)
            content = response.content if hasattr(response, "content") else str(response)

            contains_96 = "96" in content
            print(f"  Response: '{content.strip()}'")
            print(f"  Contains '96': {contains_96} {'✓' if contains_96 else '✗'}")

            llm.unload()

        except Exception as e:
            print(f"  ❌ Failed to test {model_id}: {e}")


def main() -> None:
    """Run all diagnostic tests."""
    test_both_prompts()
    test_with_more_tokens()
    test_other_models()

    print("\n" + "=" * 80)
    print("🔍 SUMMARY")
    print("=" * 80)
    print("The issue is likely that slim-extract-qwen-0.5b doesn't follow")
    print("basic instruction-following prompts well. It's designed for")
    print("specific extraction tasks, not general Q&A.")
    print("")
    print("Recommendations:")
    print("1. Use task-specific prompts for extraction models")
    print("2. Consider different test prompts for different model types")
    print("3. Test with models that have more general capabilities")


if __name__ == "__main__":
    main()
