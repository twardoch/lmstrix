# examples/python/advanced_testing.py
from lmstrix.api.client import LmsClient
from lmstrix.api.exceptions import InferenceError, ModelLoadError
from lmstrix.core.context_tester import TestPattern


def main() -> None:
    """Demonstrates advanced context testing with the LMStrix Python API."""
    print("### LMStrix Python API: Advanced Testing ###")

    client = LmsClient()
    client.scan_models()

    if not client.models:
        print("No models found. Please download a model in LM Studio to test.")
        return

    # Select the first model for testing.
    # In a real application, you would select a specific model.
    model_id = next(iter(client.models.keys()))
    model = client.get_model(model_id)
    print(f"\n--- Preparing to test model: {model.path} ---")

    # 1. Run a standard binary search test
    # This is the most efficient test for finding the max context.
    print("\n--- Running binary search test (max_context=4096) ---")
    try:
        result = model.test_context(
            max_context=4096,
            pattern=TestPattern.BINARY,
        )
        print(f"Binary search complete. Max working context: {result} tokens.")
    except (ModelLoadError, InferenceError) as e:
        print(f"An error occurred: {e}")

    # 2. Run a linear ramp-up test
    # This is slower but useful for debugging. It tests at each step.
    print("\n--- Running linear ramp-up test (2048 to 3072, step 1024) ---")
    try:
        result = model.test_context(
            start_context=2048,
            max_context=3072,
            step=1024,
            pattern=TestPattern.LINEAR,
            force=True,  # Force re-test, ignoring previous results
        )
        print(f"Linear test complete. Max working context: {result} tokens.")
    except (ModelLoadError, InferenceError) as e:
        print(f"An error occurred: {e}")

    # 3. Save the results
    # Test results are automatically saved to the registry.
    # We can explicitly save the registry to disk.
    print("\n--- Saving updated model registry ---")
    client.save_registry()
    print("Registry saved to lmstrix.json")

    # You can now inspect the lmstrix.json file to see the stored test results.
    print(f"\nModel '{model_id}' now has test data:")
    print(client.models[model_id].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
