#!/bin/bash
# This script demonstrates various ways to use the `lmstrix test` command
# for verifying the context length of models in LM Studio.

# --- Introduction ---
echo "LMStrix Model Testing Examples"
echo "------------------------------"
echo "This script requires LM Studio to be running."

# --- Prerequisite: Scan for models ---
echo "First, ensuring the model registry is up-to-date..."
lmstrix scan

# --- Example 1: Test a Specific Model by Path ---
echo "\nExample 1: Test a specific model by its full path."
# Find the path of the first model in the registry to use as an example.
MODEL_PATH=$(lmstrix list --json | jq -r 'keys[0]')

if [ -z "$MODEL_PATH" ] || [ "$MODEL_PATH" == "null" ]; then
    echo "Error: No models found. Please download a model in LM Studio and run `lmstrix scan`."
    exit 1
fi

echo "Testing model: $MODEL_PATH"
# The `--model` flag is used to specify the model to test.
# lmstrix test --model "$MODEL_PATH"

echo "(Example 1 test is commented out to prevent long run times)."

# --- Example 2: Force a Retest of a Model ---
echo "\nExample 2: Force a retest on a model that may already have results."
# The `--force` flag tells the tester to ignore any previous test results and run again.

echo "Retesting model: $MODEL_PATH"
# lmstrix test --model "$MODEL_PATH" --force

echo "(Example 2 test is commented out)."

# --- Example 3: Run a Full Test on All Untested Models ---
echo "\nExample 3: Test all models that don't have existing results."
# Running `lmstrix test` without a specific model will start a full scan.
# It will iterate through all models in the registry and test each one
# that does not already have a `test_result`.

echo "Starting a full test run on all untested models..."
# lmstrix test

echo "(Example 3 test is commented out)."

# --- Example 4: Customizing the Test with Different Context Sizes ---
echo "\nExample 4: Customize the test range."
# You can specify the minimum and maximum context sizes to test.
# This is useful if you want to narrow the search range.

echo "Testing model with a custom range (1024-4096 tokens): $MODEL_PATH"
# lmstrix test --model "$MODEL_PATH" --min-context 1024 --max-context 4096

echo "(Example 4 test is commented out)."


echo "\nModel testing examples complete."
echo "Uncomment the 'lmstrix test ...' lines to run the commands."
