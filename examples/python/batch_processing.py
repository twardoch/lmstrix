#!/usr/bin/env python3
# this_file: examples/python/batch_processing.py
"""Demonstrates batch processing of multiple models for testing or inference."""

import time

from lmstrix import LMStrix
from lmstrix.core.models import ContextTestStatus


def main() -> None:
    """Demonstrates batch processing of multiple models for testing or inference."""
    print("### LMStrix Python API: Batch Processing ###")

    # Initialize LMStrix
    lms = LMStrix(verbose=False)  # Set to True for detailed output

    # 1. Scan and load all models
    print("\n--- Scanning for all available models ---")
    lms.scan()
    all_models = lms.list()

    if not all_models:
        print("No models found. Please download models in LM Studio.")
        return

    print(f"Found {len(all_models)} models.")

    # Show model summary
    untested = [m for m in all_models if m.test_status != ContextTestStatus.COMPLETED]
    tested = [m for m in all_models if m.test_status == ContextTestStatus.COMPLETED]
    print(f"  - Tested: {len(tested)}")
    print(f"  - Untested: {len(untested)}")

    # 2. Batch Context Testing
    print("\n--- Batch Testing Untested Models ---")
    print(f"Will test {len(untested)} models in fast mode...")

    if untested:
        # Sort by size for efficient testing (smaller models first)
        untested.sort(key=lambda m: m.size_bytes)

        start_time = time.time()
        successful_tests = 0

        for i, model in enumerate(untested[:5], 1):  # Test up to 5 models for demo
            print(f"\n[{i}/{min(5, len(untested))}] Testing: {model.id}")
            print(f"  Size: {model.size_bytes / 1024**3:.1f} GB")
            print(f"  Declared context: {model.context_limit:,} tokens")

            try:
                # Use fast mode for quicker testing
                test_result = lms.test(model.id, fast_mode=True)

                if test_result.succeeded:
                    print(f"  ✓ Success! Optimal context: {test_result.optimal_context:,} tokens")
                    print(f"  Efficiency: {test_result.efficiency:.1%}")
                    successful_tests += 1
                else:
                    print(f"  ✗ Failed: {test_result.error}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        elapsed = time.time() - start_time
        print("\n--- Batch testing complete ---")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Successful tests: {successful_tests}/{min(5, len(untested))}")
    else:
        print("All models have already been tested!")

    # 3. Batch Inference - Compare Models
    print("\n\n--- Batch Inference: Comparing Model Responses ---")
    test_prompt = "Explain the concept of recursion in one sentence."
    print(f"Test prompt: '{test_prompt}'")

    # Select a few models for comparison
    compare_models = all_models[:3]  # First 3 models

    responses = []
    for i, model in enumerate(compare_models, 1):
        print(f"\n[{i}/{len(compare_models)}] Model: {model.id}")

        try:
            result = lms.infer(
                prompt=test_prompt,
                model_id=model.id,
                out_ctx=50,  # Short response
                temperature=0.7,
            )

            response_preview = result.response.strip()
            if len(response_preview) > 150:
                response_preview = response_preview[:147] + "..."

            print(f"Response: {response_preview}")
            responses.append(
                {
                    "model": model.id,
                    "response": result.response,
                    "time": result.inference_time,
                }
            )

        except Exception as e:
            print(f"Error: {e}")
            responses.append(
                {
                    "model": model.id,
                    "response": f"[Error: {e}]",
                    "time": 0.0,
                }
            )

    # 4. Performance Comparison
    print("\n\n--- Performance Summary ---")
    if responses:
        # Sort by inference time
        responses.sort(key=lambda x: x["time"])

        print("Models ranked by speed:")
        for i, resp in enumerate(responses, 1):
            if resp["time"] > 0:
                print(f"{i}. {resp['model']}: {resp['time']:.2f}s")
            else:
                print(f"{i}. {resp['model']}: Failed")

    # 5. Efficiency Analysis
    print("\n\n--- Model Efficiency Analysis ---")
    tested_models = [m for m in all_models if m.tested_max_context]

    if tested_models:
        # Sort by efficiency
        tested_models.sort(key=lambda m: m.efficiency or 0, reverse=True)

        print("Top 5 most efficient models (tested/declared ratio):")
        for i, model in enumerate(tested_models[:5], 1):
            eff = model.efficiency or 0
            print(f"{i}. {model.id}")
            print(f"   Efficiency: {eff:.1%}")
            print(f"   Tested: {model.tested_max_context:,} / Declared: {model.context_limit:,}")

    # 6. Smart Batch Testing Demo
    print("\n\n--- Smart Batch Testing Strategy ---")
    print("When testing all models, LMStrix uses smart sorting:")
    print("1. Models are sorted by size + context for optimal testing order")
    print("2. Smaller models are tested first to warm up")
    print("3. Progress is saved after each test for resumability")
    print("4. Failed models are automatically retried with reduced context")

    print("\nTo test all models efficiently, run:")
    print("  lmstrix test --all --fast")

    print("\n### Batch Processing Demo Complete ###")
    print("\nKey features demonstrated:")
    print("- Batch testing of multiple models")
    print("- Fast mode for quick validation")
    print("- Comparing responses across models")
    print("- Performance and efficiency analysis")
    print("- Smart testing strategies")


if __name__ == "__main__":
    main()
