#!/bin/bash
# This script demonstrates a basic, complete workflow for using the LMStrix CLI.
# It covers the main commands in a logical sequence:
# 1. Scan: Discover models downloaded in LM Studio.
# 2. List: View the models found.
# 3. Test: Run a context length test on a specific model.
# 4. Infer: Run a simple inference with the tested model.

# --- Introduction ---
echo "LMStrix Basic Workflow Example"
echo "---------------------------------"
echo "This script requires LM Studio to be running."
echo "Make sure you have at least one model downloaded."

# --- Step 1: Scan for Models ---
echo "\nStep 1: Scanning for models..."
# The `scan` command finds all models in your LM Studio models folder
# and updates the local `lmstrix.json` registry.
lmstrix scan

# --- Step 2: List Models ---
echo "\nStep 2: Listing available models..."
# The `list` command displays all models found in the registry.
# It shows their name, path, and whether they have been tested.
lmstrix list

# --- Step 3: Test a Model's Context Length ---
echo "\nStep 3: Testing a model's context length..."
# The `test` command runs a binary search to find the maximum working context.
# We will try to find the first model from the list to test.
# Note: This can take several minutes depending on the model and your hardware.

# Get the path of the first model from the registry (using jq to parse the JSON)
MODEL_PATH=$(lmstrix list --json | jq -r 'keys[0]')

if [ -z "$MODEL_PATH" ] || [ "$MODEL_PATH" == "null" ]; then
    echo "Error: Could not find a model to test. Please make sure models are downloaded and scanned."
    exit 1
fi

echo "Testing model: $MODEL_PATH"
# The `--model` flag specifies which model to test.
lmstrix test --model "$MODEL_PATH"

# --- Step 4: Run Inference ---
echo "\nStep 4: Running inference with the tested model..."
# The `infer` command runs a prompt through the specified model.
PROMPT="What is the capital of the United Kingdom?"

echo "Using prompt: '$PROMPT'"
lmstrix infer --model "$MODEL_PATH" --prompt "$PROMPT"

# --- Step 5: Review Results ---
echo "\nStep 5: Reviewing updated model list..."
# After testing, the list command will show the updated status and max context length.
lmstrix list

echo "\nWorkflow complete."
