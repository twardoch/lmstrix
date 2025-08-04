#!/usr/bin/env python3
"""
Script to retrieve out_ctx values from the lmstrix database.
"""
# this_file: get_out_ctx.py

import sys
from pathlib import Path

# Add src to path so we can import lmstrix
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lmstrix.core.models import ModelRegistry


def get_out_ctx_for_model(model_id: str) -> int | None:
    """Get the out_ctx value for a specific model."""
    registry = ModelRegistry()
    model = registry.find_model(model_id)

    if model:
        return model.context_out
    print(f"Model '{model_id}' not found in registry")
    return None


def get_all_out_ctx_values() -> dict[str, int]:
    """Get out_ctx values for all models in the registry."""
    registry = ModelRegistry()
    models = registry.list_models()

    result = {}
    for model in models:
        result[model.id] = model.context_out

    return result


def main() -> None:
    """Main function to demonstrate getting out_ctx values."""
    print("=" * 60)
    print("🔍 RETRIEVING OUT_CTX VALUES FROM DATABASE")
    print("=" * 60)

    # Get all out_ctx values
    all_out_ctx = get_all_out_ctx_values()

    if not all_out_ctx:
        print("No models found in registry")
        return

    print(f"Found {len(all_out_ctx)} models:")
    print()

    # Display all models and their out_ctx values
    for model_id, out_ctx in all_out_ctx.items():
        print(f"  {model_id}: out_ctx = {out_ctx}")

    print()
    print("=" * 60)

    # Example: Get out_ctx for a specific model
    specific_model = "slim-extract-qwen-0.5b"
    out_ctx_value = get_out_ctx_for_model(specific_model)

    if out_ctx_value is not None:
        print(f"🎯 {specific_model}: out_ctx = {out_ctx_value}")

    # Show how to access the value programmatically
    print()
    print("💡 PROGRAMMATIC ACCESS:")
    print("```python")
    print("from lmstrix.core.models import ModelRegistry")
    print()
    print("registry = ModelRegistry()")
    print("model = registry.find_model('your-model-id')")
    print("if model:")
    print("    out_ctx = model.context_out")
    print("    print(f'out_ctx: {out_ctx}')")
    print("```")


if __name__ == "__main__":
    main()
