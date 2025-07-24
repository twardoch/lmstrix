#!/bin/bash
#
# This script demonstrates the complete, basic workflow of LMStrix.
# 1. Scan for downloaded models.
# 2. List the models found.
# 3. Test the context length of a specific model.
# 4. Run inference with the tested model.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Basic Workflow Demo ###"

# Step 1: Scan for models
# This command discovers all models downloaded in your LM Studio installation
# and updates the local registry file (lmstrix.json).
echo -e "
--- Step 1: Scanning for models ---"
lmstrix scan
echo "Scan complete. Model registry updated."

# Step 2: List models
# This command displays the models found in the registry, along with any
# test results or metadata.
echo -e "
--- Step 2: Listing available models ---"
lmstrix list
echo "Model list displayed."

# Step 3: Test a model's context length
# Replace "model-identifier" with a unique part of your model's path from the list.
# For example, if you have "gemma-2b-it-q8_0.gguf", you can use "gemma-2b".
# This test will determine the maximum context size the model can handle.
echo -e "
--- Step 3: Testing a model's context length ---"
echo "Note: This may take several minutes depending on the model and your hardware."
# We will use a placeholder model identifier here.
# In a real scenario, you would replace 'phi' with a model you have.
MODEL_ID="phi" # <--- CHANGE THIS to a model you have downloaded
echo "Testing model: $MODEL_ID"
lmstrix test "$MODEL_ID" --max-context 8192 --test-pattern binary
echo "Context test complete."

# Step 4: Run inference
# Use the same model identifier to run a simple inference task.
echo -e "
--- Step 4: Running inference ---"
lmstrix infer "$MODEL_ID" "What is the capital of France?"
echo -e "
Inference complete."

echo -e "
### Workflow Demo Finished ###"