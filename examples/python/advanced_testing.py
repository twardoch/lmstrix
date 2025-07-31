#!/usr/bin/env python3
# this_file: examples/python/advanced_testing.py
"""Demonstrates advanced context testing with the LMStrix Python API."""

from lmstrix import LMStrix
from lmstrix.core.models import ContextTestStatus
from lmstrix.utils.logging import logger


def main() -> None:
    """Demonstrates advanced context testing with the LMStrix Python API."""
    logger.info("### LMStrix Python API: Advanced Testing ###")

    # Initialize LMStrix
    lms = LMStrix(verbose=True)

    # Scan for models
    logger.info("\n--- Scanning for models ---")
    lms.scan()
    models = lms.list()

    if not models:
        logger.info("No models found. Please download a model in LM Studio to test.")
        return

    # Select a model for testing
    # Prefer an untested model, or the smallest model
    untested = [m for m in models if m.test_status != ContextTestStatus.COMPLETED]
    if untested:
        model = untested[0]
        logger.info(f"\n--- Selected untested model: {model.id} ---")
    else:
        model = min(models, key=lambda m: m.size_bytes)
        logger.info(f"\n--- Selected smallest model: {model.id} ---")

    # 1. Standard test with new fixed context strategy
    logger.info("\n--- Example 1: Standard Context Test ---")
    logger.info("Tests at fixed sizes: 30k, 40k, 60k, 80k, 100k, 120k, and declared_max-1")
    try:
        result = lms.test(model.id)
        if result.succeeded:
            logger.info(f"✓ Test complete! Optimal context: {result.optimal_context:,} tokens")
            logger.info(f"  Efficiency: {result.efficiency:.1%}")
        else:
            logger.info(f"✗ Test failed: {result.error}")
    except Exception as e:
        logger.info(f"Error during standard test: {e}")

    # 2. Fast mode test (skip semantic verification)
    logger.info("\n--- Example 2: Fast Mode Test ---")
    logger.info("Only checks if model can load and generate output")
    try:
        # Select another model for variety
        model2 = models[1] if len(models) > 1 else model

        result = lms.test(model2.id, fast_mode=True)
        if result.succeeded:
            logger.info(f"✓ Fast test complete! Model works at: {result.optimal_context:,} tokens")
        else:
            logger.info(f"✗ Fast test failed: {result.error}")
    except Exception as e:
        logger.info(f"Error during fast test: {e}")

    # 3. Test with custom threshold
    logger.info("\n--- Example 3: Test with Custom Threshold ---")
    logger.info("Limit maximum initial test context to 50,000 tokens")
    try:
        result = lms.test(model.id, threshold=50000, force=True)
        if result.succeeded:
            logger.info(f"✓ Threshold test complete! Optimal: {result.optimal_context:,} tokens")
    except Exception as e:
        logger.info(f"Error during threshold test: {e}")

    # 4. Test at specific context size
    logger.info("\n--- Example 4: Test at Specific Context Size ---")
    logger.info("Testing model at exactly 8192 tokens")
    try:
        result = lms.test(model.id, ctx=8192)
        if result.succeeded:
            logger.info("✓ Model works at 8192 tokens!")
        else:
            logger.info(f"✗ Model failed at 8192 tokens: {result.error}")
    except Exception as e:
        logger.info(f"Error during specific context test: {e}")

    # 5. Batch testing demonstration
    logger.info("\n--- Example 5: Batch Testing (First 3 Models) ---")
    logger.info("Testing multiple models efficiently")
    try:
        # Test first 3 models in fast mode
        test_models = models[:3]
        for i, test_model in enumerate(test_models, 1):
            logger.info(f"\n[{i}/{len(test_models)}] Testing {test_model.id}...")
            result = lms.test(test_model.id, fast_mode=True)
            if result.succeeded:
                logger.info(f"  ✓ Optimal: {result.optimal_context:,} tokens")
            else:
                logger.info(f"  ✗ Failed: {result.error}")
    except Exception as e:
        logger.info(f"Error during batch test: {e}")

    # 6. View test results
    logger.info("\n--- Example 6: View Test Results ---")
    # Re-list models to get updated test results
    models = lms.list()
    tested_models = [m for m in models if m.test_status == ContextTestStatus.COMPLETED]

    if tested_models:
        logger.info(f"Found {len(tested_models)} tested models:")
        # Sort by efficiency
        tested_models.sort(key=lambda m: m.efficiency or 0, reverse=True)

        for m in tested_models[:5]:  # Show top 5
            eff = f"{m.efficiency:.1%}" if m.efficiency else "N/A"
            logger.info(f"  {m.id}:")
            logger.info(f"    Tested Max: {m.tested_max_context:,} tokens")
            logger.info(f"    Declared: {m.context_limit:,} tokens")
            logger.info(f"    Efficiency: {eff}")
    else:
        logger.info("No tested models found yet.")

    # 7. Test progress persistence demo
    logger.info("\n--- Example 7: Test Progress Persistence ---")
    logger.info("LMStrix saves test progress automatically.")
    logger.info("If a test is interrupted, it resumes from the last successful context.")
    logger.info("This is especially useful for long-running tests on large models.")

    logger.info("\n### Advanced Testing Demo Complete ###")
    logger.info("\nKey features demonstrated:")
    logger.info("- Fixed context testing strategy (30k, 40k, 60k, etc.)")
    logger.info("- Fast mode for quick validation")
    logger.info("- Threshold limits for safety")
    logger.info("- Specific context testing")
    logger.info("- Batch testing capabilities")
    logger.info("- Test result persistence")


if __name__ == "__main__":
    main()
