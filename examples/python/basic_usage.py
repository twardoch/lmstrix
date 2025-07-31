#!/usr/bin/env python3
# this_file: examples/python/basic_usage.py
"""Demonstrates basic usage of the LMStrix Python API."""

from lmstrix import LMStrix
from lmstrix.api.exceptions import InferenceError, ModelLoadError, ModelNotFoundError
from lmstrix.utils.logging import logger


def main() -> None:
    """Demonstrates basic usage of the LMStrix Python API."""
    logger.info("### LMStrix Python API: Basic Usage ###")

    # Initialize LMStrix with verbose mode for detailed output
    lms = LMStrix(verbose=True)

    # 1. Scan for models
    logger.info("\n--- Scanning for models... ---")
    scan_result = lms.scan()
    logger.info(f"Scan complete. Found {scan_result.models_found} models.")

    # 2. List models
    logger.info("\n--- Listing models ---")
    models = lms.list()

    if not models:
        logger.info("No models found. Please download a model in LM Studio.")
        return

    # Display first few models
    logger.info(f"Total models: {len(models)}")
    for i, model in enumerate(models[:3]):
        logger.info(f"{i + 1}. ID: {model.id}")
        logger.info(f"   Size: {model.size_bytes / 1024**3:.1f} GB")
        logger.info(f"   Context Limit: {model.context_limit:,} tokens")
        if model.tested_max_context:
            logger.info(f"   Tested Max: {model.tested_max_context:,} tokens")

    # 3. Get a specific model
    # Use the first model found for this example
    model_id = models[0].id
    logger.info(f"\n--- Selecting model: {model_id} ---")

    # 4. Test the model's context (optional)
    logger.info("\n--- Testing model context (optional) ---")
    logger.info("Note: Context testing can take a few minutes.")
    logger.info("Skipping for demo - uncomment the next line to test:")

    # 5. Run inference
    logger.info("\n--- Running inference ---")
    prompt = "What are the three main laws of robotics?"
    logger.info(f"Prompt: {prompt}")

    try:
        # Basic inference
        result = lms.infer(
            prompt=prompt,
            model_id=model_id,
            out_ctx=200,  # Limit output to 200 tokens
            temperature=0.7,
        )

        logger.info(f"\nResponse ({result.tokens_used} tokens in {result.inference_time:.1f}s):")
        logger.info(result.response)

    except ModelNotFoundError as e:
        logger.info(f"Model not found: {e}")
        logger.info("Available models:", e.available_models[:3], "...")
    except (ModelLoadError, InferenceError) as e:
        logger.info(f"An error occurred during inference: {e}")

    # 6. Advanced inference with context control
    logger.info("\n--- Advanced inference with context control ---")
    try:
        # Load model with specific context size
        result = lms.infer(
            prompt="Explain quantum computing in one paragraph.",
            model_id=model_id,
            in_ctx=4096,  # Load model with 4096 token context
            out_ctx=150,  # Generate up to 150 tokens
            temperature=0.5,  # Lower temperature for more focused output
        )

        logger.info("\nResponse with 4096 context:")
        logger.info(result.response)

    except Exception as e:
        logger.info(f"Advanced inference failed: {e}")

    # 7. Model state detection demo
    logger.info("\n--- Model state detection ---")
    logger.info("Running another inference to demonstrate model reuse...")
    try:
        # This should reuse the already loaded model
        result = lms.infer(
            prompt="What is Python?",
            model_id=model_id,
            out_ctx=50,
        )
        logger.info("Response:", result.response[:100], "...")
        logger.info("(Model was reused, not reloaded)")

    except Exception as e:
        logger.info(f"Reuse demo failed: {e}")

    logger.info("\n### Basic Usage Demo Complete ###")


if __name__ == "__main__":
    main()
