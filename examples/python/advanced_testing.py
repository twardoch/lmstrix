#!/usr/bin/env python3
"""
advanced_testing.py - Advanced context testing scenarios

This example demonstrates advanced usage of the context testing functionality:
- Custom testing configurations
- Batch testing multiple models
- Monitoring test progress
- Handling test failures
- Analyzing test results
"""

import asyncio
import time
from typing import List, Dict, Any

from lmstrix.core.context_tester import ContextTester
from lmstrix.core.models import Model, TestStatus
from lmstrix.loaders.model_loader import load_model_registry, save_model_registry


async def test_single_model_with_monitoring(model: Model) -> Model:
    """Test a single model with progress monitoring."""
    print(f"\n=== Testing {model.id} ===")
    print(f"Declared context limit: {model.context_limit:,}")
    
    # Create tester instance
    tester = ContextTester(verbose=True)
    
    # Start timing
    start_time = time.time()
    
    # Run the test
    print("Starting context test...")
    updated_model = await tester.test_model(model)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Display results
    print(f"\nTest completed in {duration:.1f} seconds")
    print(f"Status: {updated_model.context_test_status.value}")
    
    if updated_model.tested_max_context:
        print(f"Maximum working context: {updated_model.tested_max_context:,}")
        efficiency = (updated_model.tested_max_context / model.context_limit) * 100
        print(f"Context efficiency: {efficiency:.1f}%")
    else:
        print("No working context found - model may have issues")
    
    return updated_model


async def batch_test_models(models: List[Model], concurrent: bool = False) -> Dict[str, Model]:
    """Test multiple models either sequentially or concurrently."""
    print(f"\n=== Batch Testing {len(models)} Models ===")
    print(f"Mode: {'Concurrent' if concurrent else 'Sequential'}")
    
    results = {}
    
    if concurrent:
        # Test models concurrently (be careful with resource usage!)
        tasks = [test_single_model_with_monitoring(model) for model in models]
        tested_models = await asyncio.gather(*tasks, return_exceptions=True)
        
        for model, result in zip(models, tested_models):
            if isinstance(result, Exception):
                print(f"Error testing {model.id}: {result}")
                results[model.id] = model
            else:
                results[model.id] = result
    else:
        # Test models sequentially
        for i, model in enumerate(models, 1):
            print(f"\nTesting model {i}/{len(models)}")
            try:
                tested_model = await test_single_model_with_monitoring(model)
                results[model.id] = tested_model
            except Exception as e:
                print(f"Error testing {model.id}: {e}")
                results[model.id] = model
    
    return results


async def test_with_custom_parameters():
    """Example of testing with custom parameters."""
    print("\n=== Custom Testing Parameters ===")
    
    registry = load_model_registry()
    models = registry.list_models()
    
    if not models:
        print("No models available")
        return
    
    model = models[0]
    
    # Create custom tester with specific configurations
    # Note: The actual ContextTester might need modifications to support these
    tester = ContextTester(verbose=True)
    
    # You could extend ContextTester to support custom parameters like:
    # - Initial context size to start testing from
    # - Step size for binary search
    # - Number of retries on failure
    # - Custom timeout values
    
    print(f"Testing {model.id} with custom parameters")
    updated_model = await tester.test_model(model)
    
    print(f"Test result: {updated_model.context_test_status.value}")


def analyze_test_results():
    """Analyze and report on all test results."""
    print("\n=== Test Results Analysis ===")
    
    registry = load_model_registry()
    all_models = registry.list_models()
    
    # Categorize models by status
    status_counts = {
        "untested": 0,
        "testing": 0,
        "completed": 0,
        "failed": 0
    }
    
    tested_models = []
    
    for model in all_models:
        status_counts[model.context_test_status.value] += 1
        if model.tested_max_context:
            tested_models.append(model)
    
    # Display summary
    print("\nModel Status Summary:")
    for status, count in status_counts.items():
        print(f"  {status.capitalize()}: {count}")
    
    if tested_models:
        # Calculate statistics
        efficiencies = [
            (m.tested_max_context / m.context_limit) * 100 
            for m in tested_models
        ]
        
        print(f"\nTested Models Statistics:")
        print(f"  Total tested: {len(tested_models)}")
        print(f"  Average efficiency: {sum(efficiencies) / len(efficiencies):.1f}%")
        print(f"  Lowest efficiency: {min(efficiencies):.1f}%")
        print(f"  Highest efficiency: {max(efficiencies):.1f}%")
        
        # Find outliers
        print("\nNotable findings:")
        for model in tested_models:
            efficiency = (model.tested_max_context / model.context_limit) * 100
            if efficiency < 50:
                print(f"  - {model.id}: Only {efficiency:.1f}% of declared context works")
            elif efficiency > 95:
                print(f"  - {model.id}: Excellent - {efficiency:.1f}% of declared context works")


async def retry_failed_tests():
    """Retry testing for models that previously failed."""
    print("\n=== Retrying Failed Tests ===")
    
    registry = load_model_registry()
    
    # Find failed models
    failed_models = [
        m for m in registry.list_models() 
        if m.context_test_status == TestStatus.FAILED
    ]
    
    if not failed_models:
        print("No failed tests to retry")
        return
    
    print(f"Found {len(failed_models)} failed tests")
    
    # Retry each failed model
    for model in failed_models:
        print(f"\nRetrying {model.id}...")
        
        try:
            tester = ContextTester()
            updated_model = await tester.test_model(model)
            
            # Update registry
            registry.add_model(updated_model)
            save_model_registry(registry)
            
            if updated_model.context_test_status == TestStatus.COMPLETED:
                print(f"Success! Found working context: {updated_model.tested_max_context:,}")
            else:
                print("Test failed again")
                
        except Exception as e:
            print(f"Error during retry: {e}")


async def smart_testing_strategy():
    """Implement a smart testing strategy based on model characteristics."""
    print("\n=== Smart Testing Strategy ===")
    
    registry = load_model_registry()
    all_models = registry.list_models()
    
    # Categorize models for testing priority
    untested = [m for m in all_models if m.context_test_status == TestStatus.UNTESTED]
    
    if not untested:
        print("All models have been tested!")
        return
    
    # Sort by priority (smaller models first, as they test faster)
    untested.sort(key=lambda m: m.size_bytes or float('inf'))
    
    print(f"Testing strategy for {len(untested)} models:")
    print("1. Starting with smaller models (faster testing)")
    print("2. Moving to larger models")
    print("3. Saving progress after each test")
    
    # Test in order
    for i, model in enumerate(untested, 1):
        print(f"\n[{i}/{len(untested)}] Testing {model.id}")
        print(f"Size: {model.size_bytes / (1024**3):.2f} GB")
        
        tester = ContextTester()
        updated_model = await tester.test_model(model)
        
        # Save after each test
        registry.add_model(updated_model)
        save_model_registry(registry)
        
        # Optional: Add delay between tests to avoid overloading system
        if i < len(untested):
            print("Pausing before next test...")
            await asyncio.sleep(5)


async def main():
    """Run all advanced testing examples."""
    
    # Load registry
    registry = load_model_registry()
    models = registry.list_models()
    
    if not models:
        print("No models found. Please run basic_usage.py first to scan for models.")
        return
    
    # Example 1: Test a single model with monitoring
    untested = [m for m in models if m.context_test_status == TestStatus.UNTESTED]
    if untested:
        await test_single_model_with_monitoring(untested[0])
    
    # Example 2: Batch test multiple models
    if len(untested) > 1:
        # Test up to 3 models sequentially
        await batch_test_models(untested[:3], concurrent=False)
    
    # Example 3: Custom parameters (demonstration)
    await test_with_custom_parameters()
    
    # Example 4: Analyze results
    analyze_test_results()
    
    # Example 5: Retry failed tests
    await retry_failed_tests()
    
    # Example 6: Smart testing strategy
    # Commented out as it would test all models
    # await smart_testing_strategy()
    
    print("\n=== Advanced Testing Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())