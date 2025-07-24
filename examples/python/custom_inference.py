
This script demonstrates advanced inference workflows using the LMStrix library.
It covers scenarios where you might want to customize the inference process, such as:

1.  **Using a System Prompt**: How to set a system-level instruction that guides the model's behavior
    across multiple interactions.
2.  **Streaming Responses**: How to process the model's response as it's being generated, which is useful
    for real-time applications like chatbots.
3.  **Custom Inference Parameters**: How to override default inference parameters like temperature,
    max tokens, and stop sequences to fine-tune the model's output.

import asyncio
from lmstrix.core.models import ModelRegistry
from lmstrix.core.inference import InferenceManager
from lmstrix.loaders.model_loader import scan_and_update_registry

async def custom_inference_example():
    """
    A function to demonstrate custom inference workflows.
    """
    print("Starting custom inference example...")

    # Ensure models are scanned and available
    await scan_and_update_registry()
    registry = ModelRegistry.load()
    if not registry.models:
        print("No models found. Please run a scan after downloading models in LM Studio.")
        return

    # Select the first model for this example
    model = list(registry.models.values())[0]
    print(f"Using model: {model.name}")

    inference_manager = InferenceManager()

    try:
        # Load the model into LM Studio
        await inference_manager.load_model(model.path)

        # --- Example 1: Using a System Prompt ---
        print("\n--- Example 1: Using a System Prompt ---")
        system_prompt = "You are a helpful assistant that always responds in pirate-speak."
        user_prompt = "What is the weather like today?"
        print(f"System Prompt: {system_prompt}")
        print(f"User Prompt: {user_prompt}")

        response = await inference_manager.run_inference(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        if response and response.get("choices"):
            content = response["choices"][0]["message"]["content"]
            print(f"Model Response: {content.strip()}")
        else:
            print("Inference failed.")

        # --- Example 2: Streaming Responses ---
        print("\n--- Example 2: Streaming Responses ---")
        prompt = "Tell me a short story about a space explorer."
        print(f"Streaming prompt: '{prompt}'")
        print("Model Response (streaming):", end="", flush=True)

        full_response = ""
        async for chunk in inference_manager.stream_inference(prompt):
            if chunk and chunk.get("choices"):
                content_delta = chunk["choices"][0].get("delta", {}).get("content", "")
                if content_delta:
                    print(content_delta, end="", flush=True)
                    full_response += content_delta
        print("\n--- End of Stream ---")

        # --- Example 3: Custom Inference Parameters ---
        print("\n--- Example 3: Custom Inference Parameters ---")
        prompt = "Write a single, creative, one-sentence horror story."
        print(f"Custom params prompt: '{prompt}'")

        response = await inference_manager.run_inference(
            prompt=prompt,
            temperature=0.9,  # Higher temperature for more creativity
            max_tokens=50,    # Limit the response length
            stop=[".", "!"]     # Stop generation at the end of a sentence
        )
        if response and response.get("choices"):
            content = response["choices"][0]["message"]["content"]
            print(f"Model Response (creative): {content.strip()}")
        else:
            print("Inference failed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Unload the model
        await inference_manager.unload_model()
        print("\nModel unloaded.")

    print("\nCustom inference example finished.")

if __name__ == "__main__":
    # Requires LM Studio to be running.
    # Run with `python -m examples.python.custom_inference`
    asyncio.run(custom_inference_example())
