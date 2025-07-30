#!/usr/bin/env python3
# this_file: examples/python/prompt_templates_demo.py
"""Demonstrates advanced prompt template features with TOML files."""

from pathlib import Path

import toml

from lmstrix import LMStrix
from lmstrix.core.prompts import PromptResolver
from lmstrix.loaders.prompt_loader import load_prompts, load_single_prompt


def main() -> None:
    """Demonstrates prompt template features."""
    print("### LMStrix Python API: Prompt Templates Demo ###")

    # Initialize components
    lms = LMStrix(verbose=False)
    resolver = PromptResolver(verbose=True)

    # Get a model for testing
    lms.scan()
    models = lms.list()
    if not models:
        print("No models found. Please download a model in LM Studio.")
        return

    model_id = models[0].id
    print(f"Using model: {model_id}")

    # 1. Create example prompts programmatically
    print("\n--- Example 1: Creating Prompts Programmatically ---")

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
    print(f"Created temporary prompts file: {temp_prompts}")

    # 2. Basic placeholder resolution
    print("\n--- Example 2: Basic Placeholder Resolution ---")

    # Resolve a simple prompt
    resolved = resolver.resolve_prompt(
        prompt_name="analysis.sentiment",
        prompts_data=prompts_data,
        text="I absolutely love this new LMStrix tool! It makes testing models so much easier.",
    )

    print(f"Template: {resolved.template}")
    print(f"Resolved: {resolved.resolved}")
    print(f"Tokens: {resolved.tokens}")

    # Run inference
    try:
        result = lms.infer(resolved.resolved, model_id, out_ctx=50)
        print(f"Analysis: {result.response}")
    except Exception as e:
        print(f"Inference error: {e}")

    # 3. Nested template resolution
    print("\n--- Example 3: Nested Template Resolution ---")

    # Resolve a prompt with internal references
    resolved = resolver.resolve_prompt(
        prompt_name="assistant.task",
        prompts_data=prompts_data,
        domain="Python programming",
        action="explain",
        content_type="code",
        content="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    )

    print(f"Template: {resolved.template}")
    print(f"Resolved: {resolved.resolved}")
    print(f"Placeholders found: {resolved.placeholders_found}")
    print(f"Placeholders resolved: {resolved.placeholders_resolved}")

    # 4. Complex multi-parameter example
    print("\n--- Example 4: Complex Story Generation ---")

    resolved = resolver.resolve_prompt(
        prompt_name="creative.story",
        prompts_data=prompts_data,
        genre="science fiction",
        character="an AI researcher",
        plot="discovers their AI has become sentient",
        tone="thought-provoking and philosophical",
    )

    print(f"Story prompt: {resolved.resolved}")

    try:
        result = lms.infer(resolved.resolved, model_id, out_ctx=200, temperature=0.8)
        print(f"\nGenerated story:\n{result.response}")
    except Exception as e:
        print(f"Inference error: {e}")

    # 5. Using load_single_prompt helper
    print("\n--- Example 5: Using load_single_prompt Helper ---")

    try:
        resolved = load_single_prompt(
            toml_path=temp_prompts,
            prompt_name="analysis.summary",
            content_type="research paper",
            length="three",
            content="Quantum computing represents a fundamental shift in computational paradigms...",
        )

        print(f"Summary prompt: {resolved.resolved}")
        print(f"Unresolved placeholders: {resolved.placeholders_unresolved}")

    except Exception as e:
        print(f"Error loading prompt: {e}")

    # 6. Batch prompt resolution
    print("\n--- Example 6: Batch Prompt Resolution ---")

    # Resolve all prompts with common parameters
    common_params = {
        "domain": "machine learning",
        "style": "haiku",
        "subject": "neural networks",
        "technique": "metaphor",
    }

    all_resolved = resolver.resolve_all_prompts(prompts_data, **common_params)

    print(f"Resolved {len(all_resolved)} prompts:")
    for name, resolved in list(all_resolved.items())[:3]:
        print(f"\n{name}:")
        print(f"  Template length: {len(resolved.template)}")
        print(f"  Resolved length: {len(resolved.resolved)}")
        print(f"  Unresolved: {resolved.placeholders_unresolved}")

    # 7. Error handling for missing placeholders
    print("\n--- Example 7: Handling Missing Placeholders ---")

    # Try to resolve with missing parameters
    resolved = resolver.resolve_prompt(
        prompt_name="creative.poem",
        prompts_data=prompts_data,
        style="haiku",
        # Missing: subject, technique
    )

    print(f"Template: {resolved.template}")
    print(f"Partially resolved: {resolved.resolved}")
    print(f"Missing placeholders: {resolved.placeholders_unresolved}")

    # 8. Loading from actual prompts.toml
    print("\n--- Example 8: Loading from examples/prompts.toml ---")

    examples_prompts = Path("examples/prompts.toml")
    if examples_prompts.exists():
        prompts = load_prompts(examples_prompts)
        print(f"Loaded {len(prompts)} prompt categories")

        # Show available prompts
        for category, prompts_dict in prompts.items():
            if isinstance(prompts_dict, dict):
                print(f"\n{category}:")
                for prompt_name in list(prompts_dict.keys())[:3]:
                    print(f"  - {prompt_name}")

    # 9. Advanced: Context injection
    print("\n--- Example 9: Context Injection ---")

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

    print(f"Original context length: {len(large_context)}")
    print(f"Final prompt length: {len(final_prompt)}")
    print("Context was automatically truncated to fit!")

    # Cleanup
    if temp_prompts.exists():
        temp_prompts.unlink()
        print(f"\nCleaned up {temp_prompts}")

    print("\n### Prompt Templates Demo Complete ###")
    print("\nKey features demonstrated:")
    print("- Creating prompts programmatically")
    print("- Basic and nested placeholder resolution")
    print("- Loading prompts from TOML files")
    print("- Batch prompt resolution")
    print("- Handling missing placeholders")
    print("- Context injection with truncation")


if __name__ == "__main__":
    main()
