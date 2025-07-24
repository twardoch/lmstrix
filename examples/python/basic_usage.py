#!/usr/bin/env python3
"""
basic_usage.py - Simple examples using the lmstrix Python API

This example demonstrates basic usage of the lmstrix package for:
- Loading the model registry
- Listing available models
- Running inference
- Checking test results
"""

import asyncio
from pathlib import Path

# Import lmstrix components
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)
from lmstrix.core.inference import InferenceEngine
from lmstrix.core.models import Model, ModelRegistry


def example_load_and_list_models():
    """Example 1: Load model registry and list all models."""
    print("=== Example 1: Loading and Listing Models ===")
    
    # Load the model registry
    registry = load_model_registry()
    
    # Get all models
    models = registry.list_models()
    
    if not models:
        print("No models found. Run 'scan_and_update_registry()' first.")
        return
    
    # Display model information
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"\nModel: {model.id}")
        print(f"  Path: {model.path}")
        print(f"  Size: {model.size_bytes / (1024**3):.2f} GB")
        print(f"  Context Limit: {model.context_limit:,}")
        print(f"  Tested Context: {model.tested_max_context or 'Not tested'}")
        print(f"  Status: {model.context_test_status.value}")


def example_scan_for_models():
    """Example 2: Scan for new models and update registry."""
    print("\n=== Example 2: Scanning for Models ===")
    
    # Scan and update the registry
    print("Scanning for LM Studio models...")
    scan_and_update_registry(verbose=True)
    
    # Load and display updated registry
    registry = load_model_registry()
    models = registry.list_models()
    print(f"Registry now contains {len(models)} models")


async def example_simple_inference():
    """Example 3: Run simple inference with a model."""
    print("\n=== Example 3: Simple Inference ===")
    
    # Load registry and create inference engine
    registry = load_model_registry()
    engine = InferenceEngine(model_registry=registry)
    
    # Get first available model
    models = registry.list_models()
    if not models:
        print("No models available for inference")
        return
    
    model_id = models[0].id
    print(f"Using model: {model_id}")
    
    # Run inference
    result = await engine.infer(
        model_id=model_id,
        prompt="What is the capital of France?",
        temperature=0.7,
        max_tokens=50
    )
    
    if result.succeeded:
        print(f"Response: {result.response}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Time: {result.inference_time:.2f}s")
    else:
        print(f"Inference failed: {result.error}")


async def example_custom_inference():
    """Example 4: Inference with custom parameters."""
    print("\n=== Example 4: Custom Inference Parameters ===")
    
    registry = load_model_registry()
    engine = InferenceEngine(model_registry=registry, verbose=True)
    
    models = registry.list_models()
    if not models:
        print("No models available")
        return
    
    model_id = models[0].id
    
    # Example: Creative writing with high temperature
    creative_result = await engine.infer(
        model_id=model_id,
        prompt="Write a haiku about programming",
        temperature=0.9,  # High temperature for creativity
        max_tokens=100
    )
    
    print("Creative response (high temperature):")
    if creative_result.succeeded:
        print(creative_result.response)
    
    # Example: Factual response with low temperature
    factual_result = await engine.infer(
        model_id=model_id,
        prompt="List three programming languages",
        temperature=0.1,  # Low temperature for consistency
        max_tokens=100
    )
    
    print("\nFactual response (low temperature):")
    if factual_result.succeeded:
        print(factual_result.response)


def example_filter_models():
    """Example 5: Filter models by various criteria."""
    print("\n=== Example 5: Filtering Models ===")
    
    registry = load_model_registry()
    all_models = registry.list_models()
    
    # Filter tested models
    tested_models = [m for m in all_models if m.tested_max_context is not None]
    print(f"Tested models: {len(tested_models)}")
    
    # Filter untested models
    untested_models = [m for m in all_models if m.context_test_status.value == "untested"]
    print(f"Untested models: {len(untested_models)}")
    
    # Filter large models (> 5GB)
    large_models = [m for m in all_models if m.size_bytes and m.size_bytes > 5 * 1024**3]
    print(f"Large models (>5GB): {len(large_models)}")
    
    # Filter models with high context limits
    high_context_models = [m for m in all_models if m.context_limit > 8192]
    print(f"High context models (>8k): {len(high_context_models)}")
    
    # Find model with highest tested context
    if tested_models:
        best_model = max(tested_models, key=lambda m: m.tested_max_context or 0)
        print(f"\nBest tested model: {best_model.id}")
        print(f"  Tested context: {best_model.tested_max_context:,}")


def example_model_details():
    """Example 6: Get detailed information about a specific model."""
    print("\n=== Example 6: Model Details ===")
    
    registry = load_model_registry()
    
    # Get a specific model (use first available as example)
    models = registry.list_models()
    if not models:
        print("No models available")
        return
    
    model_id = models[0].id
    model = registry.get_model(model_id)
    
    if model:
        print(f"Detailed info for: {model.id}")
        print(f"  Full path: {model.path}")
        print(f"  Size: {model.size_bytes / (1024**3):.2f} GB")
        print(f"  Context In: {model.ctx_in}")
        print(f"  Context Out: {model.ctx_out}")
        print(f"  Has Tools: {model.has_tools}")
        print(f"  Has Vision: {model.has_vision}")
        print(f"  Test Status: {model.context_test_status.value}")
        
        if model.tested_max_context:
            efficiency = (model.tested_max_context / model.context_limit) * 100
            print(f"  Context Efficiency: {efficiency:.1f}%")


def main():
    """Run all examples."""
    # Basic examples
    example_load_and_list_models()
    example_scan_for_models()
    
    # Async examples
    asyncio.run(example_simple_inference())
    asyncio.run(example_custom_inference())
    
    # Advanced examples
    example_filter_models()
    example_model_details()


if __name__ == "__main__":
    main()