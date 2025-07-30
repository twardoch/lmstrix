#!/bin/bash
#
# This script demonstrates various context testing scenarios with LMStrix.
# Shows new features: --threshold, --all --ctx, --fast, and test resumption.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Model Testing Examples ###"

# Replace with a model identifier that matches your downloaded models
# Common patterns: "llama", "mistral", "qwen", "phi", "gemma", "codellama"
MODEL_ID="llama" # <--- CHANGE THIS to match a model you have downloaded

# Example 1: Standard Test with New Fixed Context Strategy
# Tests at fixed context sizes: 30k, 40k, 60k, 80k, 100k, 120k, and declared_max-1
echo -e "\n--- Example 1: Standard Context Test ---"
echo "Testing model '$MODEL_ID' with fixed context strategy"
lmstrix test --model_id "$MODEL_ID" --verbose
echo "Standard test complete."

# Example 2: Test with Threshold Limit
# Prevents initial test from exceeding specified threshold (default: 102,400)
echo -e "\n--- Example 2: Test with Custom Threshold ---"
echo "Testing with maximum initial context of 50,000 tokens"
lmstrix test --model_id "$MODEL_ID" --threshold 50000
echo "Threshold test complete."

# Example 3: Fast Mode Testing
# Only checks if model can load and generate, skips semantic verification
echo -e "\n--- Example 3: Fast Mode Test ---"
echo "Running fast test (skip semantic verification)"
lmstrix test --model_id "$MODEL_ID" --fast
echo "Fast test complete."

# Example 4: Test at Specific Context Size
# Tests a model at a specific context size only
echo -e "\n--- Example 4: Test at Specific Context ---"
echo "Testing model at exactly 8192 tokens"
lmstrix test --model_id "$MODEL_ID" --ctx 8192
echo "Specific context test complete."

# Example 5: Batch Test All Models
# Tests all untested models in the registry
echo -e "\n--- Example 5: Batch Test All Models ---"
echo "Testing all models (this may take a while)..."
echo "Note: This will test ALL models. Press Ctrl+C to cancel."
read -p "Press Enter to continue..." -t 5 || true
lmstrix test --all --verbose
echo "Batch test complete."

# Example 6: Batch Test with Context Limit
# Tests all models at a specific context size
echo -e "\n--- Example 6: Batch Test at Specific Context ---"
echo "Testing all untested models at 4096 tokens"
lmstrix test --all --ctx 4096
echo "Batch context test complete."

# Example 7: Fast Batch Testing
# Quick test of all models without semantic verification
echo -e "\n--- Example 7: Fast Batch Test ---"
echo "Running fast test on all models"
lmstrix test --all --fast
echo "Fast batch test complete."

# Example 8: Show Test Results
# Display models sorted by their tested context size
echo -e "\n--- Example 8: View Test Results ---"
echo "Models sorted by tested context size:"
lmstrix list --sort ctx
echo -e "\nModels sorted by efficiency (tested/declared ratio):"
lmstrix list --sort eff

# Example 9: Test with Smart Sorting
# When testing all models, they're sorted for efficiency
echo -e "\n--- Example 9: Smart Sorted Batch Test ---"
echo "Testing all models with smart sorting (smaller models first)"
lmstrix test --all --threshold 30000 --fast
echo "Smart sorted test complete."

# Example 10: Resume Interrupted Test
# If a test is interrupted, it can resume from where it left off
echo -e "\n--- Example 10: Test Resumption Demo ---"
echo "LMStrix automatically saves progress during testing."
echo "If a test is interrupted, simply run the same command again."
echo "The test will resume from the last successful context size."

echo -e "\n### Model Testing Examples Finished ###"
echo -e "\nKey takeaways:"
echo "- New fixed context testing strategy (30k, 40k, 60k, etc.)"
echo "- Use --threshold to limit maximum initial test size"
echo "- Use --fast for quick testing without semantic checks"
echo "- Use --ctx to test at specific context sizes"
echo "- Batch testing with --all supports all options"
echo "- Tests automatically resume if interrupted"