"""
This script demonstrates how to use the LMStrix library to perform batch processing on multiple models.
It showcases the following workflow:
1.  Scan for all available models.
2.  Filter for models that have successfully passed context length verification.
3.  Run a batch inference job on the filtered models using a specified prompt.
4.  Print the results for each model.
"""

import asyncio
from lmstrix.core.models import LmsModel, ModelRegistry
from lmstrix.core.inference import InferenceManager
from lmstrix.loaders.model_loader import scan_and_update_registry
from lmstrix.utils.paths import get_default_models_file

async def batch_inference_example():
    """
    An example function that demonstrates batch processing of models.
    """
    print("Starting batch processing example...")

    # 1. Scan for models and update the local registry
    print("Scanning for available models...")
    await scan_and_update_registry()
    print("Model scan complete.")

    # Load the registry
    registry = ModelRegistry.load()
    if not registry.models:
        print("No models found. Please download models in LM Studio and run the scan command.")
        return

    # 2. Filter for models that are ready for inference
    # For this example, we'll consider models that have a known working context > 0.
    ready_models = [
        model for model in registry.models.values()
        if model.test_result and model.test_result.max_context_length > 0
    ]

    if not ready_models:
        print("No models have passed context verification yet.")
        print("Please run the context tester before running batch inference.")
        return

    print(f"Found {len(ready_models)} models ready for batch inference.")

    # 3. Define the prompt for the batch job
    prompt = "What is the capital of France?"
    print(f"Using prompt: '{prompt}'")

    # 4. Run inference on each ready model
    inference_manager = InferenceManager()
    for model in ready_models:
        print(f"--- Running inference on: {model.name} ---")
        try:
            # Ensure the model is loaded
            loaded_model = await inference_manager.load_model(model.path)

            # Run inference
            response = await inference_manager.run_inference(prompt)

            # Print the response
            if response and response.get("choices"):
                content = response["choices"][0].get("message", {}).get("content", "No content returned.")
                print(f"Model response: {content.strip()}")
            else:
                print("Inference failed or returned an empty response.")

        except Exception as e:
            print(f"An error occurred during inference for model {model.name}: {e}")
        finally:
            # Unload the model to free up resources for the next one
            await inference_manager.unload_model()
            print("--- Finished with model ---")


if __name__ == "__main__":
    # To run this example, you need to have LM Studio running.
    # You can run this script directly using `python -m examples.python.batch_processing`
    asyncio.run(batch_inference_example())
