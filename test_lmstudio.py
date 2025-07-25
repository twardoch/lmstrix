#!/usr/bin/env python3
"""Test script to understand lmstudio API"""

import asyncio

import lmstudio


async def test_api() -> None:
    # List models
    models = lmstudio.list_downloaded_models()
    print("Models found:", len(models))

    if models:
        # Try to load first model
        model = models[0]
        print(f"\nTesting with model: {model.info.path}")

        # Load the model
        llm = lmstudio.llm(model.info.path)
        print(f"Model loaded: {llm}")

        # Test completion
        prompt = "Hello, how are you?"
        print(f"\nPrompt: {prompt}")

        try:
            # Try simple complete
            response = await llm.complete(prompt)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error with simple complete: {e}")

        # Try with unload
        try:
            llm.unload()
            print("Model unloaded")
        except Exception as e:
            print(f"Error unloading: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
