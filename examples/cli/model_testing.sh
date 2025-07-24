#!/bin/bash
#
# This script demonstrates focused examples of context testing with LMStrix.
# It covers different testing strategies and options.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Model Testing Examples ###"

# Replace "model-identifier" with a unique part of your model's path.
# For example, if you have "gemma-2b-it-q8_0.gguf", you can use "gemma-2b".
MODEL_ID="phi" # <--- CHANGE THIS to a model you have downloaded

# Example 1: Standard Binary Search Test
# This is the most efficient way to find the maximum context size.
# It starts high and narrows down the search space.
echo -e "
--- Example 1: Standard Binary Search Test ---"
echo "Testing model '$MODEL_ID' with binary search up to 8192 tokens."
lmstrix test "$MODEL_ID" --max-context 8192 --test-pattern binary
echo "Binary search test complete."

# Example 2: Linear Ramp-Up Test
# This tests context sizes incrementally from a starting point.
# It's slower but can be useful for debugging models that fail unpredictably.
echo -e "
--- Example 2: Linear Ramp-Up Test ---"
echo "Testing model '$MODEL_ID' with linear ramp-up from 1024 to 4096 tokens."
lmstrix test "$MODEL_ID" --start-context 1024 --max-context 4096 --step 1024 --test-pattern linear
echo "Linear ramp-up test complete."

# Example 3: Force Re-test
# Use the --force flag to ignore previous test results and run the test again.
echo -e "
--- Example 3: Force Re-test ---"
echo "Forcing a re-test of model '$MODEL_ID'."
lmstrix test "$MODEL_ID" --max-context 4096 --force
echo "Forced re-test complete."

# Example 4: Custom Test Prompt
# You can provide a custom prompt template for the context test.
# This is useful for models that require a specific instruction format.
echo -e "
--- Example 4: Custom Test Prompt ---"
echo "Testing with a custom prompt."
lmstrix test "$MODEL_ID" --max-context 2048 --prompt "USER: {prompt} ASSISTANT:"
echo "Custom prompt test complete."

echo -e "
### Model Testing Examples Finished ###"