
"""
This script provides a basic example of how to use the LMStrix Python package 
to interact with models in LM Studio. It demonstrates the essential functionalities:

1.  **Scanning for Models**: It discovers all models that have been downloaded in LM Studio
    and updates a local registry file (`lmstrix.json`).
2.  **Listing Models**: It loads the model registry and prints a list of all discovered models,
    including their name, path, and any available test results.
3.  **Running Inference**: It loads a specific model, runs a simple inference with a given prompt,
    and prints the model's response.

This example is a great starting point for understanding the core features of the LMStrix library.
"""

import asyncio
from lmstrix.core.models import ModelRegistry
from lmstrix.core.inference import InferenceManager
from lmstrix.loaders.model_loader import scan_and_update_registry

async def basic_usage_example():
    """
    A function to demonstrate the basic usage of the LMStrix library.
    """
    print("Starting basic usage example...")

    # 1. Scan for models and update the local registry
    print("\nStep 1: Scanning for available models...")
    await scan_and_update_registry()
    print("Model scan complete.")

    # 2. List all available models from the registry
    print("\nStep 2: Listing all registered models...")
    registry = ModelRegistry.load()
    if not registry.models:
        print("No models found. Please download models in LM Studio and run the scan again.")
        return

    print(f"Found {len(registry.models)} models:")
    for model_path, model in registry.models.items():
        status = "Tested" if model.test_result else "Not Tested"
        print(f"  - {model.name} (Status: {status})")

    # 3. Run inference with the first available model
    print("\nStep 3: Running inference with a sample model...")
    target_model = list(registry.models.values())[0]
    print(f"Using model: {target_model.name}")

    inference_manager = InferenceManager()
    try:
        # Load the model
        print("Loading model into LM Studio...")
        await inference_manager.load_model(target_model.path)

        # Define a prompt and run inference
        prompt = "Explain the theory of relativity in simple terms."
        print(f"Sending prompt: '{prompt}'")
        response = await inference_manager.run_inference(prompt)

        # Print the response from the model
        if response and response.get("choices"):
            content = response["choices"][0].get("message", {}).get("content", "(No content received)")
            print(f"\nModel Response:\n{content.strip()}")
        else:
            print("\nInference returned no response or an unexpected format.")

    except Exception as e:
        print(f"An error occurred during inference: {e}")
    finally:
        # Unload the model to free up resources
        await inference_manager.unload_model()
        print("\nModel unloaded.")

    print("\nBasic usage example finished.")

if __name__ == "__main__":
    # This example requires LM Studio to be running in the background.
    # Run this script with `python -m examples.python.basic_usage`
    asyncio.run(basic_usage_example())
