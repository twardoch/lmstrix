"""
This script demonstrates advanced context testing scenarios with LMStrix.
It covers how to:

1.  **Initiate a Full Scan**: Run a comprehensive context length test on all models that
    haven't been tested yet. This is useful for initial setup or after downloading
    several new models.
2.  **Test a Specific Model**: Target a single model for context testing. This is useful
    when you want to re-test a model or test a newly downloaded one without running
    a full scan.
3.  **Force a Retest**: Re-run the context test on a model that already has existing
    test results. This can be useful if you suspect the previous results were inaccurate
    or if you've made changes to your system that might affect performance.
"""

import asyncio
from lmstrix.core.models import ModelRegistry
from lmstrix.core.context_tester import ContextTester
from lmstrix.loaders.model_loader import scan_and_update_registry

async def advanced_testing_example():
    """
    A function to demonstrate advanced context testing scenarios.
    """
    print("Starting advanced context testing example...")

    # First, ensure the model registry is up-to-date
    await scan_and_update_registry()
    registry = ModelRegistry.load()
    if not registry.models:
        print("No models found. Please download models in LM Studio first.")
        return

    tester = ContextTester()

    # --- Example 1: Run a full scan on all untested models ---
    print("\n--- Example 1: Full Scan on Untested Models ---")
    print("This will test all models that do not have a test result.")
    # Note: This can take a long time depending on the number of models.
    # await tester.test_all_models()
    print("Full scan example complete (commented out by default to prevent long runs).")

    # --- Example 2: Test a specific model by name ---
    print("\n--- Example 2: Test a Specific Model ---")
    # Find a model to test. Let's pick the first one that hasn't been tested.
    untested_model = next((m for m in registry.models.values() if not m.test_result), None)

    if untested_model:
        print(f"Found an untested model: {untested_model.name}")
        print("Starting test...")
        # await tester.test_model(untested_model.path)
        print(f"Test for {untested_model.name} complete (commented out).")
    else:
        print("No untested models found for this example.")

    # --- Example 3: Force a retest on an already tested model ---
    print("\n--- Example 3: Force a Retest ---")
    # Find a model that has already been tested.
    tested_model = next((m for m in registry.models.values() if m.test_result), None)

    if tested_model:
        print(f"Found a tested model to re-test: {tested_model.name}")
        print(f"Previous max context: {tested_model.test_result.max_context_length}")
        print("Forcing a retest...")
        # await tester.test_model(tested_model.path, force_retest=True)
        print(f"Retest for {tested_model.name} complete (commented out).")
    else:
        print("No tested models found to demonstrate a forced retest.")

    print("\nAdvanced testing example finished.")
    print("Note: The actual test calls are commented out to prevent accidental long-running tests.")
    print("Uncomment the `await tester.test...` lines to run them.")

if __name__ == "__main__":
    # Requires LM Studio to be running.
    # Run with `python -m examples.python.advanced_testing`
    asyncio.run(advanced_testing_example())