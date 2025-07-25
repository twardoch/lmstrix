# examples/python/batch_processing.py
import time

from lmstrix.api.client import LmsClient


def main() -> None:
    """
    Demonstrates batch processing of multiple models for testing or inference.
    """
    print("### LMStrix Python API: Batch Processing ###")

    client = LmsClient()

    # 1. Scan and load all models
    print("\n--- Scanning for all available models ---")
    client.scan_models()
    all_models = client.get_all_models()

    if not all_models:
        print("No models found. Aborting.")
        return

    print(f"Found {len(all_models)} models.")

    # 2. Batch Context Testing
    # Test all models that haven't been tested yet.
    print("\n--- Batch testing all untested models (up to 2048 tokens) ---")
    for model in all_models:
        if model.max_context_tested is None:
            print(f"\nTesting model: {model.path}...")
            try:
                start_time = time.time()
                result = model.test_context(max_context=2048)
                end_time = time.time()
                print(
                    f"Test complete for {model.id}. "
                    f"Max context: {result}. "
                    f"Time taken: {end_time - start_time:.2f}s",
                )
            except Exception as e:
                print(f"Could not test model {model.id}. Error: {e}")
        else:
            print(
                f"\nSkipping already tested model: {model.id} "
                f"(Max context: {model.max_context_tested})",
            )

    # Save results to disk
    client.save_registry()
    print("\n--- All test results saved. ---")

    # 3. Batch Inference
    # Run the same prompt on all available models.
    print("\n--- Running the same prompt on all models ---")
    prompt = "What is the most interesting fact you know?"
    for model in all_models:
        print(f"\n--- Querying model: {model.path} ---")
        print(f"Prompt: {prompt}")
        try:
            response_stream = model.infer(prompt, max_tokens=150)
            print("Response: ", end="")
            for chunk in response_stream:
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"Could not run inference on model {model.id}. Error: {e}")


if __name__ == "__main__":
    main()
