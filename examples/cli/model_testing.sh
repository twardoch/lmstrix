#!/bin/bash
# model_testing.sh - Context testing focused examples for lmstrix CLI
# This example demonstrates various ways to test model context limits

echo "=== LMStrix Model Context Testing Examples ==="
echo "This example shows different ways to test model context limits"
echo

# Example 1: Test a specific model by ID
echo "Example 1: Testing a specific model"
echo "Command: python -m lmstrix test --model_id='llama-3.2-1b-instruct'"
echo "This tests the context limits of a single model"
# python -m lmstrix test --model_id="llama-3.2-1b-instruct"
echo

# Example 2: Test all untested models
echo "Example 2: Testing all untested models"
echo "Command: python -m lmstrix test --all"
echo "This tests all models that haven't been tested yet"
# python -m lmstrix test --all
echo

# Example 3: Test with verbose output
echo "Example 3: Testing with verbose output for debugging"
echo "Command: python -m lmstrix test --model_id='your-model-id' --verbose"
echo "Verbose mode shows detailed progress and debug information"
# python -m lmstrix test --model_id="llama-3.2-1b-instruct" --verbose
echo

# Example 4: Re-test a previously failed model
echo "Example 4: Re-testing a model that previously failed"
echo "First, list models to see which ones failed:"
echo "Command: python -m lmstrix list"
# python -m lmstrix list
echo
echo "Then re-test the failed model:"
echo "Command: python -m lmstrix test --model_id='failed-model-id'"
# python -m lmstrix test --model_id="failed-model-id"
echo

# Example 5: Understanding test results
echo "Example 5: Understanding test results"
echo "After testing, use 'list' to see the results:"
echo "Command: python -m lmstrix list"
echo
echo "The output shows:"
echo "- Declared Ctx: What the model claims to support"
echo "- Tested Ctx: The actual working context limit found"
echo "- Status: untested, testing, completed, or failed"
echo

# Example 6: Testing workflow for new models
echo "Example 6: Complete testing workflow for new models"
echo "1. Scan for new models: python -m lmstrix scan"
echo "2. List to see new models: python -m lmstrix list"
echo "3. Test new models: python -m lmstrix test --all"
echo "4. Verify results: python -m lmstrix list"
echo

echo "=== Context Testing Tips ==="
echo "- Testing can take several minutes per model"
echo "- The tool uses binary search to efficiently find the maximum context"
echo "- Results are saved automatically to the registry"
echo "- Failed tests can be retried - the tool will start fresh"
echo "- Use --verbose flag to see detailed progress during testing"