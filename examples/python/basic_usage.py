# examples/python/basic_usage.py
from lmstrix.api.client import LmsClient


def main() -> None:
    """Demonstrates basic usage of the LMStrix Python API."""
    print("### LMStrix Python API: Basic Usage ###")

    # Initialize the client. It automatically finds your LM Studio installation.
    client = LmsClient()

    # 1. Scan for models
    print("\n--- Scanning for models... ---")
    client.scan_models()
    print("Scan complete.")

    # 2. List models
    # The model registry is available as a dictionary.
    print("\n--- Listing models ---")
    if not client.models:
        print("No models found. Please download a model in LM Studio.")
        return

    for model_id, model_info in client.models.items():
        print(f"ID: {model_id}, Path: {model_info.path}")

    # 3. Get a specific model
    # Use the first model found for this example.
    model_id = next(iter(client.models.keys()))
    print(f"\n--- Selecting model: {model_id} ---")
    model = client.get_model(model_id)

    if not model:
        print(f"Could not find model with ID: {model_id}")
        return

    # 4. Run inference
    print("\n--- Running inference ---")
    prompt = "What are the three main laws of robotics?"
    print(f"Prompt: {prompt}")

    try:
        response_generator = model.infer(prompt, temperature=0.7)
        print("Response: ", end="")
        for chunk in response_generator:
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"\nAn error occurred during inference: {e}")


if __name__ == "__main__":
    main()
