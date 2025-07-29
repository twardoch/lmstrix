# examples/python/custom_inference.py
from lmstrix.api.client import LmsClient
from lmstrix.api.exceptions import InferenceError, ModelLoadError


def main() -> None:
    """Demonstrates custom inference workflows with the LMStrix Python API."""
    print("### LMStrix Python API: Custom Inference ###")

    client = LmsClient()
    client.scan_models()

    if not client.models:
        print("No models found. Please download a model in LM Studio.")
        return

    model_id = next(iter(client.models.keys()))
    model = client.get_model(model_id)
    print(f"\n--- Using model: {model.path} ---")

    # 1. Custom system prompt
    # Guide the model's behavior, personality, or output format.
    print("\n--- 1. Inference with a custom system prompt ---")
    prompt = "Generate a list of three creative names for a new coffee shop."
    system_prompt = "You are a branding expert. You provide concise, creative, and memorable names."
    print(f"Prompt: {prompt}")
    print(f"System Prompt: {system_prompt}")

    try:
        response_stream = model.infer(prompt, system_prompt=system_prompt)
        print("Response:")
        for chunk in response_stream:
            print(chunk, end="", flush=True)
        print("\n")
    except (ModelLoadError, InferenceError) as e:
        print(f"\nAn error occurred: {e}\n")

    # 2. Adjusting inference parameters
    # Control creativity (temperature) and response length (out_ctx).
    print("\n--- 2. Adjusting temperature and out_ctx ---")
    prompt = "Write a single sentence that is surprising and philosophical."
    print(f"Prompt: {prompt}")
    print("Settings: temperature=1.8 (highly creative), out_ctx=50")

    try:
        response_stream = model.infer(prompt, temperature=1.8, out_ctx=50)
        print("Response:")
        for chunk in response_stream:
            print(chunk, end="", flush=True)
        print("\n")
    except (ModelLoadError, InferenceError) as e:
        print(f"\nAn error occurred: {e}\n")

    # 3. Structured output (JSON)
    # Instructing the model to return JSON. This works best with capable models.
    print("\n--- 3. Requesting structured JSON output ---")
    prompt = (
        "Return a JSON object with two keys: 'city' and 'population', for the capital of Japan."
    )
    system_prompt = "You are a helpful assistant that only returns valid, raw JSON objects."
    print(f"Prompt: {prompt}")

    try:
        response_stream = model.infer(prompt, system_prompt=system_prompt)
        print("Response:")
        full_response = "".join(response_stream)
        print(full_response)
    except (ModelLoadError, InferenceError) as e:
        print(f"\nAn error occurred: {e}\n")


if __name__ == "__main__":
    main()
