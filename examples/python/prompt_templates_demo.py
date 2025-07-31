#!/usr/bin/env python3
# this_file: examples/python/prompt_templates_demo.py
"""Demonstrates advanced prompt template features with TOML files."""

from pathlib import Path

import toml

from lmstrix import LMStrix
from lmstrix.core.prompts import PromptResolver
from lmstrix.loaders.prompt_loader import load_prompts, load_single_prompt
from lmstrix.utils.logging import logger


def main() -> None:
    """Demonstrates prompt template features."""
    logger.info("### LMStrix Python API: Prompt Templates Demo ###")

    # Initialize components
    lms = LMStrix(verbose=False)
    resolver = PromptResolver(verbose=True)

    # Get a model for testing
    lms.scan()
    models = lms.list()
    if not models:
        logger.info("No models found. Please download a model in LM Studio.")
        return

    model_id = models[0].id
    logger.info(f"Using model: {model_id}")

    # 1. Create example prompts programmatically
    logger.info("\n--- Example 1: Creating Prompts Programmatically ---")

    prompts_data = {
        "assistant": {
            "base": "You are a helpful AI assistant specializing in {{domain}}.",
            "task": "{{assistant.base}} Please {{action}} the following {{content_type}}: {{content}}",
        },
        "analysis": {
            "sentiment": "Analyze the sentiment of this text and classify it as positive, negative, or neutral: {{text}}",
            "summary": "Summarize the following {{content_type}} in {{length}} sentences: {{content}}",
        },
        "creative": {
            "story": "Write a {{genre}} story about {{character}} who {{plot}}. Make it {{tone}}.",
            "poem": "Compose a {{style}} poem about {{subject}} using {{technique}}",
        },
    }

    # Save to temporary TOML file
    temp_prompts = Path("temp_prompts.toml")
    with open(temp_prompts, "w") as f:
        toml.dump(prompts_data, f)
    logger.info(f"Created temporary prompts file: {temp_prompts}")

    # 2. Basic placeholder resolution
    logger.info("\n--- Example 2: Basic Placeholder Resolution ---")

    # Resolve a simple prompt
    resolved = resolver.resolve_prompt(
        prompt_name="analysis.sentiment",
        prompts_data=prompts_data,
        text="I absolutely love this new LMStrix tool! It makes testing models so much easier.",
    )

    logger.info(f"Template: {resolved.template}")
    logger.info(f"Resolved: {resolved.resolved}")
    logger.info(f"Tokens: {resolved.tokens}")

    # Run inference
    try:
        result = lms.infer(resolved.resolved, model_id, out_ctx=50)
        logger.info(f"Analysis: {result.response}")
    except Exception as e:
        logger.info(f"Inference error: {e}")

    # 3. Nested template resolution
    logger.info("\n--- Example 3: Nested Template Resolution ---")

    # Resolve a prompt with internal references
    resolved = resolver.resolve_prompt(
        prompt_name="assistant.task",
        prompts_data=prompts_data,
        domain="Python programming",
        action="explain",
        content_type="code",
        content="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    )

    logger.info(f"Template: {resolved.template}")
    logger.info(f"Resolved: {resolved.resolved}")
    logger.info(f"Placeholders found: {resolved.placeholders_found}")
    logger.info(f"Placeholders resolved: {resolved.placeholders_resolved}")

    # 4. Complex multi-parameter example
    logger.info("\n--- Example 4: Complex Story Generation ---")

    resolved = resolver.resolve_prompt(
        prompt_name="creative.story",
        prompts_data=prompts_data,
        genre="science fiction",
        character="an AI researcher",
        plot="discovers their AI has become sentient",
        tone="thought-provoking and philosophical",
    )

    logger.info(f"Story prompt: {resolved.resolved}")

    try:
        result = lms.infer(resolved.resolved, model_id, out_ctx=200, temperature=0.8)
        logger.info(f"\nGenerated story:\n{result.response}")
    except Exception as e:
        logger.info(f"Inference error: {e}")

    # 5. Using load_single_prompt helper
    logger.info("\n--- Example 5: Using load_single_prompt Helper ---")

    try:
        resolved = load_single_prompt(
            toml_path=temp_prompts,
            prompt_name="analysis.summary",
            content_type="research paper",
            length="three",
            content="Quantum computing represents a fundamental shift in computational paradigms...",
        )

        logger.info(f"Summary prompt: {resolved.resolved}")
        logger.info(f"Unresolved placeholders: {resolved.placeholders_unresolved}")

    except Exception as e:
        logger.info(f"Error loading prompt: {e}")

    # 6. Batch prompt resolution
    logger.info("\n--- Example 6: Batch Prompt Resolution ---")

    # Resolve all prompts with common parameters
    common_params = {
        "domain": "machine learning",
        "style": "haiku",
        "subject": "neural networks",
        "technique": "metaphor",
    }

    all_resolved = resolver.resolve_all_prompts(prompts_data, **common_params)

    logger.info(f"Resolved {len(all_resolved)} prompts:")
    for name, resolved in list(all_resolved.items())[:3]:
        logger.info(f"\n{name}:")
        logger.info(f"  Template length: {len(resolved.template)}")
        logger.info(f"  Resolved length: {len(resolved.resolved)}")
        logger.info(f"  Unresolved: {resolved.placeholders_unresolved}")

    # 7. Error handling for missing placeholders
    logger.info("\n--- Example 7: Handling Missing Placeholders ---")

    # Try to resolve with missing parameters
    resolved = resolver.resolve_prompt(
        prompt_name="creative.poem",
        prompts_data=prompts_data,
        style="haiku",
        # Missing: subject, technique
    )

    logger.info(f"Template: {resolved.template}")
    logger.info(f"Partially resolved: {resolved.resolved}")
    logger.info(f"Missing placeholders: {resolved.placeholders_unresolved}")

    # 8. Loading from actual prompts.toml
    logger.info("\n--- Example 8: Loading from examples/prompts.toml ---")

    examples_prompts = Path("examples/prompts.toml")
    if examples_prompts.exists():
        prompts = load_prompts(examples_prompts)
        logger.info(f"Loaded {len(prompts)} prompt categories")

        # Show available prompts
        for category, prompts_dict in prompts.items():
            if isinstance(prompts_dict, dict):
                logger.info(f"\n{category}:")
                for prompt_name in list(prompts_dict.keys())[:3]:
                    logger.info(f"  - {prompt_name}")

    # 9. Advanced: Context injection
    logger.info("\n--- Example 9: Context Injection ---")

    # Create a prompt with context placeholder
    qa_prompt = "Based on the following context:\n{{context}}\n\nAnswer this question: {{question}}"

    # Large context that might need truncation
    large_context = "A" * 10000  # Simulate large document

    # Use inject_context to handle truncation
    final_prompt = resolver.inject_context(
        prompt=qa_prompt,
        context=large_context,
        context_placeholder="{{context}}",
        out_ctx=500,  # Limit total prompt size
    )

    logger.info(f"Original context length: {len(large_context)}")
    logger.info(f"Final prompt length: {len(final_prompt)}")
    logger.info("Context was automatically truncated to fit!")

    # Cleanup
    if temp_prompts.exists():
        temp_prompts.unlink()
        logger.info(f"\nCleaned up {temp_prompts}")

    logger.info("\n### Prompt Templates Demo Complete ###")
    logger.info("\nKey features demonstrated:")
    logger.info("- Creating prompts programmatically")
    logger.info("- Basic and nested placeholder resolution")
    logger.info("- Loading prompts from TOML files")
    logger.info("- Batch prompt resolution")
    logger.info("- Handling missing placeholders")
    logger.info("- Context injection with truncation")


if __name__ == "__main__":
    main()
