#!/usr/bin/env python3
"""Test the limit and threshold logic for save command."""


def calculate_context_to_save(tested_context: int, limit: int = 100, threshold: int = 0) -> int:
    """Calculate the context value to save based on limit and threshold.

    This mimics the logic in ConcreteConfigManager.save_model_config
    """
    if tested_context > threshold and limit < 100:
        # Apply the percentage limit only if above threshold
        context_to_save = int(tested_context * limit / 100)
        print(f"Applying {limit}% limit: {tested_context} -> {context_to_save}")
    else:
        # Use 100% if at or below threshold
        context_to_save = tested_context
        if tested_context <= threshold and limit < 100:
            print(f"Context ({tested_context}) <= threshold ({threshold}), using 100%")
        else:
            print(f"Using 100% of context: {tested_context}")

    return context_to_save


# Test cases
print("Test Case 1: Model with 20000 context, limit=50, threshold=19000")
print(f"Result: {calculate_context_to_save(20000, 50, 19000)}")
print()

print("Test Case 2: Model with 20000 context, limit=50, threshold=30000")
print(f"Result: {calculate_context_to_save(20000, 50, 30000)}")
print()

print("Test Case 3: Model with 4096 context, limit=75, threshold=10000")
print(f"Result: {calculate_context_to_save(4096, 75, 10000)}")
print()

print("Test Case 4: Model with 100000 context, limit=75, threshold=0")
print(f"Result: {calculate_context_to_save(100000, 75, 0)}")
print()

print("Test Case 5: Model with 100000 context, limit=75, threshold=50000")
print(f"Result: {calculate_context_to_save(100000, 75, 50000)}")
print()

print("Test Case 6: Default behavior - limit=100, threshold=0")
print(f"Result: {calculate_context_to_save(65536, 100, 0)}")
