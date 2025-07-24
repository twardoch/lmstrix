#!/usr/bin/env python3
"""
custom_inference.py - Custom inference workflows

This example demonstrates advanced inference patterns:
- Prompt templating and formatting
- Context-aware inference
- Streaming responses (if supported)
- Error handling and retries
- Performance optimization
"""

import asyncio
import time
from typing import List, Dict, Optional
import json

from lmstrix.core.inference import InferenceEngine, InferenceResult
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.core.models import Model


class CustomInferenceWorkflow:
    """Custom inference workflow with advanced features."""
    
    def __init__(self, verbose: bool = False):
        self.registry = load_model_registry(verbose=verbose)
        self.engine = InferenceEngine(model_registry=self.registry, verbose=verbose)
    
    async def inference_with_template(
        self, 
        model_id: str, 
        template: str, 
        variables: Dict[str, str],
        **kwargs
    ) -> InferenceResult:
        """Run inference with a prompt template."""
        # Replace variables in template
        prompt = template
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", value)
        
        print(f"\nGenerated prompt:\n{prompt}\n")
        
        return await self.engine.infer(
            model_id=model_id,
            prompt=prompt,
            **kwargs
        )
    
    async def context_aware_inference(
        self,
        model_id: str,
        prompt: str,
        context_percentage: float = 0.8,
        **kwargs
    ) -> InferenceResult:
        """Run inference with context limit awareness."""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Use tested context if available, otherwise use declared
        max_context = model.tested_max_context or model.context_limit
        safe_context = int(max_context * context_percentage)
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        prompt_tokens = len(prompt) // 4
        
        print(f"\nContext-aware inference:")
        print(f"  Model: {model_id}")
        print(f"  Max context: {max_context:,}")
        print(f"  Safe context ({int(context_percentage*100)}%): {safe_context:,}")
        print(f"  Prompt tokens (est.): {prompt_tokens:,}")
        
        if prompt_tokens > safe_context:
            print(f"  WARNING: Prompt may exceed safe context limit!")
        
        return await self.engine.infer(
            model_id=model_id,
            prompt=prompt,
            **kwargs
        )
    
    async def inference_with_retry(
        self,
        model_id: str,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Optional[InferenceResult]:
        """Run inference with automatic retry on failure."""
        for attempt in range(max_retries):
            try:
                print(f"\nAttempt {attempt + 1}/{max_retries}")
                result = await self.engine.infer(
                    model_id=model_id,
                    prompt=prompt,
                    **kwargs
                )
                
                if result.succeeded:
                    return result
                else:
                    print(f"Inference failed: {result.error}")
                    
            except Exception as e:
                print(f"Error during inference: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        print("All retry attempts failed")
        return None
    
    async def compare_model_responses(
        self,
        prompt: str,
        model_ids: List[str],
        **kwargs
    ) -> Dict[str, InferenceResult]:
        """Compare responses from multiple models."""
        print(f"\n=== Comparing {len(model_ids)} Models ===")
        print(f"Prompt: {prompt[:100]}...")
        
        results = {}
        
        for model_id in model_ids:
            print(f"\n--- Model: {model_id} ---")
            result = await self.engine.infer(
                model_id=model_id,
                prompt=prompt,
                **kwargs
            )
            results[model_id] = result
            
            if result.succeeded:
                print(f"Response: {result.response[:200]}...")
                print(f"Tokens: {result.tokens_used}, Time: {result.inference_time:.2f}s")
            else:
                print(f"Failed: {result.error}")
        
        return results
    
    async def benchmark_inference(
        self,
        model_id: str,
        prompts: List[str],
        **kwargs
    ) -> Dict[str, any]:
        """Benchmark inference performance across multiple prompts."""
        print(f"\n=== Benchmarking {model_id} ===")
        print(f"Testing with {len(prompts)} prompts")
        
        times = []
        tokens = []
        successes = 0
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}/{len(prompts)}: {prompt[:50]}...")
            
            start_time = time.time()
            result = await self.engine.infer(
                model_id=model_id,
                prompt=prompt,
                **kwargs
            )
            elapsed = time.time() - start_time
            
            if result.succeeded:
                times.append(elapsed)
                tokens.append(result.tokens_used)
                successes += 1
                print(f"  Success: {elapsed:.2f}s, {result.tokens_used} tokens")
            else:
                print(f"  Failed: {result.error}")
        
        # Calculate statistics
        if times:
            avg_time = sum(times) / len(times)
            avg_tokens = sum(tokens) / len(tokens)
            tokens_per_sec = sum(tokens) / sum(times)
        else:
            avg_time = avg_tokens = tokens_per_sec = 0
        
        stats = {
            "model_id": model_id,
            "total_prompts": len(prompts),
            "successful": successes,
            "failed": len(prompts) - successes,
            "average_time": avg_time,
            "average_tokens": avg_tokens,
            "tokens_per_second": tokens_per_sec,
            "total_time": sum(times)
        }
        
        print(f"\n--- Benchmark Results ---")
        print(f"Success rate: {successes}/{len(prompts)} ({successes/len(prompts)*100:.1f}%)")
        print(f"Average time: {avg_time:.2f}s")
        print(f"Average tokens: {avg_tokens:.0f}")
        print(f"Throughput: {tokens_per_sec:.1f} tokens/sec")
        
        return stats


async def example_template_inference():
    """Example: Using prompt templates."""
    workflow = CustomInferenceWorkflow()
    
    # Code review template
    code_review_template = """You are a senior software engineer reviewing code.

Code to review:
{{code}}

Please provide:
1. Overall assessment
2. Potential issues
3. Suggestions for improvement

Keep your response concise and actionable."""
    
    code_sample = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)
"""
    
    result = await workflow.inference_with_template(
        model_id="your-model-id",  # Replace with actual model
        template=code_review_template,
        variables={"code": code_sample},
        temperature=0.3,
        max_tokens=300
    )
    
    if result and result.succeeded:
        print("Code Review Result:")
        print(result.response)


async def example_context_aware():
    """Example: Context-aware inference."""
    workflow = CustomInferenceWorkflow()
    
    # Create a long prompt to test context limits
    long_context = "Background information: " + ("This is some context. " * 100)
    question = "Based on the above context, what can you tell me?"
    full_prompt = long_context + "\n\n" + question
    
    result = await workflow.context_aware_inference(
        model_id="your-model-id",  # Replace with actual model
        prompt=full_prompt,
        context_percentage=0.8,  # Use only 80% of available context
        temperature=0.5
    )
    
    if result and result.succeeded:
        print("Response with context awareness:")
        print(result.response[:200] + "...")


async def example_retry_logic():
    """Example: Inference with retry logic."""
    workflow = CustomInferenceWorkflow()
    
    # This might fail if the model is not loaded
    result = await workflow.inference_with_retry(
        model_id="potentially-problematic-model",
        prompt="Test prompt for retry logic",
        max_retries=3,
        temperature=0.7
    )
    
    if result and result.succeeded:
        print("Success after retries:")
        print(result.response)
    else:
        print("Failed even after retries")


async def example_model_comparison():
    """Example: Compare multiple models."""
    workflow = CustomInferenceWorkflow()
    
    # Get available models
    models = workflow.registry.list_models()
    if len(models) < 2:
        print("Need at least 2 models for comparison")
        return
    
    # Compare first two models
    model_ids = [m.id for m in models[:2]]
    
    results = await workflow.compare_model_responses(
        prompt="Explain the concept of recursion in programming",
        model_ids=model_ids,
        temperature=0.5,
        max_tokens=200
    )
    
    # Analyze differences
    print("\n=== Comparison Summary ===")
    for model_id, result in results.items():
        if result.succeeded:
            print(f"{model_id}: {len(result.response)} chars, {result.inference_time:.2f}s")


async def example_performance_benchmark():
    """Example: Benchmark model performance."""
    workflow = CustomInferenceWorkflow()
    
    # Test prompts of varying complexity
    test_prompts = [
        "What is 2+2?",
        "Explain quantum computing in one sentence.",
        "Write a Python function to sort a list.",
        "What are the main causes of climate change?",
        "Translate 'Hello, world!' to Spanish, French, and German."
    ]
    
    models = workflow.registry.list_models()
    if not models:
        print("No models available for benchmarking")
        return
    
    # Benchmark first available model
    stats = await workflow.benchmark_inference(
        model_id=models[0].id,
        prompts=test_prompts,
        temperature=0.5,
        max_tokens=100
    )
    
    # Save benchmark results
    with open("benchmark_results.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("\nBenchmark results saved to benchmark_results.json")


async def main():
    """Run all custom inference examples."""
    print("=== Custom Inference Examples ===")
    
    # Note: Replace 'your-model-id' with actual model IDs from your registry
    
    # Example 1: Template-based inference
    # await example_template_inference()
    
    # Example 2: Context-aware inference
    # await example_context_aware()
    
    # Example 3: Retry logic
    # await example_retry_logic()
    
    # Example 4: Model comparison
    # await example_model_comparison()
    
    # Example 5: Performance benchmarking
    # await example_performance_benchmark()
    
    print("\nNote: Uncomment examples in main() and replace model IDs to run")


if __name__ == "__main__":
    asyncio.run(main())