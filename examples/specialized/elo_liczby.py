#!/usr/bin/env -S uv run -s
# /// script
# dependencies = [
#   "fire>=0.5",
#   "rich>=13.9.4",
#   "python-slugify",
#   "lmstudio>=1.4.1",
#   "httpx>=0.24",
#   "loguru>=0.7",
#   "pydantic>=2.0",
#   "tenacity>=8.5.0",
#   "tiktoken>=0.5",
#   "toml>=0.10"
# ]
# ///
# this_file: _keep_this/elo_liczby.py

"""
This tool uses the lmstrix package to load models and their tested context limits.

We take an --input file (a text file) and then:

- We load a model with its tested context limit
- We split the input file into paragraphs (separated by two empty lines)
- We send each paragraph to the model with Polish number conversion prompt
- We save results to a new file with specific naming convention using slugify
"""

import sys
from pathlib import Path

# Add the src directory to Python path to import lmstrix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import fire
from rich.console import Console
from slugify import slugify

from lmstrix.core.inference_manager import InferenceManager
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.utils.logging import logger

console = Console()


def process_text_with_model(
    input_file: str,
    model_id: str | None = None,
    verbose: bool = False,
) -> str:
    """
    Process a text file by sending paragraphs to a model for number-to-words conversion.

    Args:
        input_file: Path to the input text file
        model_id: Specific model ID to use. If None, uses the first available model.
        verbose: Enable verbose logging

    Returns:
        Path to the output file
    """
    input_path = Path(input_file)

    if not input_path.exists():
        logger.error(f"Input file '{input_file}' not found.")
        return ""

    # Load model registry
    logger.debug("Loading model registry...")
    registry = load_model_registry(verbose=verbose)

    if not registry._models:
        logger.error("No models found in registry. Run 'lmstrix scan' first.")
        return ""

    # Select model
    if model_id:
        model = registry.find_model(model_id)
        if not model:
            # Try fuzzy matching by searching for models that contain the identifier
            matching_models = []
            search_term = model_id.lower()
            for m in registry.list_models():
                # Check if the search term appears in the ID or short_id
                if search_term in m.id.lower() or search_term in m.get_short_id().lower():
                    matching_models.append(m)

            if len(matching_models) == 1:
                model = matching_models[0]
                logger.success(f"Found matching model: {model.id}")
            elif len(matching_models) > 1:
                logger.debug(f"Multiple models found matching '{model_id}':")
                for m in matching_models[:5]:  # Show first 5 matches
                    logger.debug(f"  - {m.id}")
                if len(matching_models) > 5:
                    logger.debug(f"  ... and {len(matching_models) - 5} more")
                return ""
            else:
                logger.error(f"No model found matching '{model_id}'.")
                available_models = [m.id for m in registry.list_models()]
                logger.debug(f"Available models: {len(available_models)} total")
                return ""
    else:
        # Use first available model with tested context
        models_with_context = [
            m for m in registry.list_models() if m.tested_max_context and m.tested_max_context > 0
        ]
        if not models_with_context:
            # Fallback to any available model
            all_models = registry.list_models()
            if not all_models:
                logger.error("No models available.")
                return ""
            model = all_models[0]
        else:
            model = models_with_context[0]

        logger.success(f"Using model: {model.id}")

    # Read input file
    logger.debug(f"Reading input file: {input_path}")
    try:
        text_content = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.error("Could not read file as UTF-8. Please check file encoding.")
        return ""

    # Split into paragraphs (separated by two empty lines)
    paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]
    logger.debug(f"Found {len(paragraphs)} paragraphs to process")

    if not paragraphs:
        logger.debug("Warning: No paragraphs found in input file.")
        return ""

    # Initialize inference manager
    logger.debug("Initializing inference manager...")
    manager = InferenceManager(verbose=verbose)

    # Process each paragraph
    results = []
    prompt_template = "Convert numbers to words in the following text: <text>{text}</text>"

    for i, paragraph in enumerate(paragraphs, 1):
        logger.debug(f"Processing paragraph {i}/{len(paragraphs)}...")

        if verbose:
            logger.debug(
                f"Input: {paragraph[:100]}{'...' if len(paragraph) > 100 else ''}",
            )

        prompt = prompt_template.format(text=paragraph)

        try:
            result = manager.infer(
                model_id=model.id,
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent results
                out_ctx=4096,  # Very generous token limit
            )

            if result["succeeded"]:
                results.append(result["response"].strip())
                if verbose:
                    logger.success("✓ Succes")
            else:
                logger.debug(f"✗ Failed: {result['error']}")
                results.append(f"[ERROR: {result['error'] or 'Unknown error'}]")

        except Exception as e:
            logger.debug(f"✗ Exception: {e}")
            results.append(f"[ERROR: {e}]")

    # Generate output filename
    script_basename = Path(__file__).stem  # "elo_liczby"
    model_slug = slugify(model.id)
    output_filename = f"{input_path.stem}--{script_basename}--{model_slug}{input_path.suffix}"
    output_path = input_path.parent / output_filename

    # Write results
    logger.debug(f"Writing results to: {output_path}")
    output_content = "\n\n".join(results)

    try:
        output_path.write_text(output_content, encoding="utf-8")
        logger.success(f"✓ Successfully processed {len(paragraphs)} paragraph")
        logger.success(f"✓ Output saved to: {output_path}")
        return str(output_path)
    except Exception as e:
        logger.debug(f"Error writing output file: {e}")
        return ""


def main() -> None:
    """Main entry point using Fire CLI."""
    fire.Fire(process_text_with_model)


if __name__ == "__main__":
    main()
