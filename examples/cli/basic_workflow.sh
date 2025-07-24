#!/bin/bash
# basic_workflow.sh - Complete workflow demonstration for lmstrix CLI
# This example shows the typical workflow: scan models, list them, test context limits, and run inference

echo "=== LMStrix Basic Workflow Example ==="
echo "This example demonstrates the complete workflow for using lmstrix CLI"
echo

# Step 1: Scan for available LM Studio models
echo "Step 1: Scanning for LM Studio models..."
echo "Command: python -m lmstrix scan"
python -m lmstrix scan
echo

# Step 2: List all discovered models
echo "Step 2: Listing all discovered models..."
echo "Command: python -m lmstrix list"
python -m lmstrix list
echo

# Step 3: Test context limits for a specific model
# Note: Replace 'model-id' with an actual model ID from the list
echo "Step 3: Testing context limits for a model..."
echo "Command: python -m lmstrix test --model_id='your-model-id'"
echo "(In a real scenario, replace 'your-model-id' with an actual model ID)"
# python -m lmstrix test --model_id="llama-3.2-1b-instruct"
echo

# Step 4: Test all untested models
echo "Step 4: Testing all untested models..."
echo "Command: python -m lmstrix test --all"
# python -m lmstrix test --all
echo

# Step 5: Run inference with a simple prompt
echo "Step 5: Running inference with a model..."
echo "Command: python -m lmstrix infer 'Hello, how are you?' --model_id='your-model-id'"
echo "(In a real scenario, replace 'your-model-id' with an actual model ID)"
# python -m lmstrix infer "Hello, how are you?" --model_id="llama-3.2-1b-instruct"
echo

# Step 6: Run inference with custom parameters
echo "Step 6: Running inference with custom parameters..."
echo "Command: python -m lmstrix infer 'Explain quantum computing' --model_id='your-model-id' --temperature=0.3 --max_tokens=150"
# python -m lmstrix infer "Explain quantum computing in simple terms" --model_id="llama-3.2-1b-instruct" --temperature=0.3 --max_tokens=150
echo

echo "=== Workflow Complete ==="
echo "This example showed how to:"
echo "1. Discover models with 'scan'"
echo "2. View models with 'list'"
echo "3. Test context limits with 'test'"
echo "4. Run inference with 'infer'"
echo
echo "For more detailed examples, see:"
echo "- model_testing.sh for context testing examples"
echo "- inference_examples.sh for various inference scenarios"