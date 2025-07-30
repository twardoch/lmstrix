#!/usr/bin/env python3
# this_file: examples/python/basic_usage.py
"""Demonstrates basic usage of the LMStrix Python API."""

from lmstrix import LMStrix
from lmstrix.api.exceptions import InferenceError, ModelLoadError, ModelNotFoundError


def main() -> None:
    """Demonstrates basic usage of the LMStrix Python API."""
    print("### LMStrix Python API: Basic Usage ###")

    # Initialize LMStrix with verbose mode for detailed output
    lms = LMStrix(verbose=True)

    # 1. Scan for models
    print("\n--- Scanning for models... ---")
    scan_result = lms.scan()
    print(f"Scan complete. Found {scan_result.models_found} models.")

    # 2. List models
    print("\n--- Listing models ---")
    models = lms.list()

    if not models:
        print("No models found. Please download a model in LM Studio.")
        return

    # Display first few models
    print(f"Total models: {len(models)}")
    for i, model in enumerate(models[:3]):
        print(f"{i + 1}. ID: {model.id}")
        print(f"   Size: {model.size_bytes / 1024**3:.1f} GB")
        print(f"   Context Limit: {model.context_limit:,} tokens")
        if model.tested_max_context:
            print(f"   Tested Max: {model.tested_max_context:,} tokens")

    # 3. Get a specific model
    # Use the first model found for this example
    model_id = models[0].id
    print(f"\n--- Selecting model: {model_id} ---")

    # 4. Test the model's context (optional)
    print("\n--- Testing model context (optional) ---")
    print("Note: Context testing can take a few minutes.")
    print("Skipping for demo - uncomment the next line to test:")
    # test_result = lms.test(model_id, fast_mode=True)
    # if test_result.succeeded:
    #     print(f"Test complete! Optimal context: {test_result.optimal_context:,} tokens")

    # 5. Run inference
    print("\n--- Running inference ---")
    prompt = "What are the three main laws of robotics?"
    print(f"Prompt: {prompt}")

    try:
        # Basic inference
        result = lms.infer(
            prompt=prompt,
            model_id=model_id,
            out_ctx=200,  # Limit output to 200 tokens
            temperature=0.7,
        )

        print(f"\nResponse ({result.tokens_used} tokens in {result.inference_time:.1f}s):")
        print(result.response)

    except ModelNotFoundError as e:
        print(f"Model not found: {e}")
        print("Available models:", e.available_models[:3], "...")
    except (ModelLoadError, InferenceError) as e:
        print(f"An error occurred during inference: {e}")

    # 6. Advanced inference with context control
    print("\n--- Advanced inference with context control ---")
    try:
        # Load model with specific context size
        result = lms.infer(
            prompt="Explain quantum computing in one paragraph.",
            model_id=model_id,
            in_ctx=4096,  # Load model with 4096 token context
            out_ctx=150,  # Generate up to 150 tokens
            temperature=0.5,  # Lower temperature for more focused output
        )

        print("\nResponse with 4096 context:")
        print(result.response)

    except Exception as e:
        print(f"Advanced inference failed: {e}")

    # 7. Model state detection demo
    print("\n--- Model state detection ---")
    print("Running another inference to demonstrate model reuse...")
    try:
        # This should reuse the already loaded model
        result = lms.infer(
            prompt="What is Python?",
            model_id=model_id,
            out_ctx=50,
        )
        print("Response:", result.response[:100], "...")
        print("(Model was reused, not reloaded)")

    except Exception as e:
        print(f"Reuse demo failed: {e}")

    print("\n### Basic Usage Demo Complete ###")


if __name__ == "__main__":
    main()
