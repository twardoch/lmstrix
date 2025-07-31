#!/usr/bin/env python3
# this_file: examples/python/custom_inference.py
"""Demonstrates custom inference workflows with the LMStrix Python API."""

from pathlib import Path

from lmstrix import LMStrix
from lmstrix.api.exceptions import InferenceError, ModelLoadError
from lmstrix.loaders.prompt_loader import load_single_prompt
from lmstrix.utils.logging import logger


def main() -> None:
    """Demonstrates custom inference workflows with the LMStrix Python API."""
    logger.info("### LMStrix Python API: Custom Inference ###")

    # Initialize LMStrix
    lms = LMStrix(verbose=False)  # Set to True for detailed output

    # Scan and get models
    lms.scan()
    models = lms.list()

    if not models:
        logger.info("No models found. Please download a model in LM Studio.")
        return

    model_id = models[0].id
    logger.info(f"\n--- Using model: {model_id} ---")

    # 1. Context control with in_ctx and out_ctx
    logger.info("\n--- 1. Context Control Demonstration ---")
    prompt = "Explain the concept of recursion in programming."
    logger.info(f"Prompt: {prompt}")
    logger.info("Loading model with 8192 token context, generating max 150 tokens")

    try:
        result = lms.infer(
            prompt=prompt,
            model_id=model_id,
            in_ctx=8192,  # Load model with 8K context
            out_ctx=150,  # Generate up to 150 tokens
            temperature=0.7,
        )
        logger.info("\nResponse:")
        logger.info(result.response)
    except (ModelLoadError, InferenceError) as e:
        logger.info(f"Error: {e}")

    # 2. Temperature control for creativity
    logger.info("\n\n--- 2. Temperature Control ---")
    prompt = "Write a haiku about artificial intelligence."

    # Low temperature (more focused)
    logger.info(f"Prompt: {prompt}")
    logger.info("Low temperature (0.3) - More deterministic:")
    try:
        result = lms.infer(prompt, model_id, temperature=0.3, out_ctx=50)
        logger.info(result.response)
    except Exception as e:
        logger.info(f"Error: {e}")

    # High temperature (more creative)
    logger.info("\nHigh temperature (1.5) - More creative:")
    try:
        result = lms.infer(prompt, model_id, temperature=1.5, out_ctx=50)
        logger.info(result.response)
    except Exception as e:
        logger.info(f"Error: {e}")

    # 3. TOML prompt templates
    logger.info("\n\n--- 3. TOML Prompt Templates ---")

    # Check if prompts.toml exists
    prompt_file = Path("examples/prompts.toml")
    if not prompt_file.exists():
        prompt_file = Path("prompts.toml")

    if prompt_file.exists():
        logger.info(f"Loading prompts from: {prompt_file}")

        # Example 1: Simple greeting
        try:
            resolved = load_single_prompt(
                toml_path=prompt_file,
                prompt_name="greetings.professional",
                name="Dr. Smith",
                topic="machine learning research",
            )
            logger.info(f"\nResolved prompt: {resolved.resolved}")

            result = lms.infer(resolved.resolved, model_id, out_ctx=100)
            logger.info(f"Response: {result.response}")
        except Exception as e:
            logger.info(f"Error with greeting: {e}")

        # Example 2: Code review template
        try:
            resolved = load_single_prompt(
                toml_path=prompt_file,
                prompt_name="code.review",
                language="Python",
                code="def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            )
            logger.info(f"\n\nCode review prompt resolved ({len(resolved.resolved)} chars)")

            result = lms.infer(resolved.resolved, model_id, out_ctx=300, temperature=0.5)
            logger.info(f"Code Review:\n{result.response}")
        except Exception as e:
            logger.info(f"Error with code review: {e}")
    else:
        logger.info(f"No prompts.toml found at {prompt_file}")

    # 4. Structured output (JSON)
    logger.info("\n\n--- 4. Structured JSON Output ---")
    json_prompt = """Generate a JSON object describing a book with the following structure:
{
  "title": "string",
  "author": "string",
  "year": number,
  "genres": ["string", "string"],
  "rating": number (1-5)
}

Create an entry for a science fiction novel."""

    logger.info("Requesting structured JSON output...")
    try:
        result = lms.infer(
            prompt=json_prompt,
            model_id=model_id,
            temperature=0.7,
            out_ctx=200,
        )
        logger.info("\nJSON Response:")
        logger.info(result.response)
    except Exception as e:
        logger.info(f"Error: {e}")

    # 5. Model state reuse
    logger.info("\n\n--- 5. Model State Reuse ---")
    logger.info("The model should already be loaded from previous inferences.")
    logger.info("This call should reuse the loaded model:")

    try:
        result = lms.infer("What is 10 + 15?", model_id, out_ctx=20)
        logger.info(f"Quick calculation: {result.response}")
        logger.info("(Model was reused, not reloaded)")
    except Exception as e:
        logger.info(f"Error: {e}")

    # 6. Force reload demonstration
    logger.info("\n\n--- 6. Force Reload ---")
    logger.info("Now forcing a model reload with different context:")

    try:
        result = lms.infer(
            prompt="What is the meaning of life?",
            model_id=model_id,
            in_ctx=16384,  # Different context size
            out_ctx=100,
            temperature=0.9,
        )
        logger.info(f"Response after reload: {result.response}")
    except Exception as e:
        logger.info(f"Error: {e}")

    logger.info("\n### Custom Inference Demo Complete ###")
    logger.info("\nKey features demonstrated:")
    logger.info("- Context control with in_ctx and out_ctx")
    logger.info("- Temperature adjustment for creativity")
    logger.info("- TOML prompt templates with placeholders")
    logger.info("- Structured JSON output generation")
    logger.info("- Model state reuse for efficiency")
    logger.info("- Force reload with different context")


if __name__ == "__main__":
    main()
