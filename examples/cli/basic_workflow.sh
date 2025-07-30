#!/bin/bash
#
# This script demonstrates the complete, basic workflow of LMStrix.
# 1. Scan for downloaded models.
# 2. List the models found with various display options.
# 3. Test the context length of a specific model.
# 4. Run inference with the tested model using new features.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Basic Workflow Demo ###"

# Step 1: Scan for models
# This command discovers all models downloaded in your LM Studio installation
# and updates the local registry file (lmstrix.json).
echo -e "\n--- Step 1: Scanning for models ---"
lmstrix scan --verbose
echo "Scan complete. Model registry updated."

# Step 2: List models with different display options
# This demonstrates the new --show and --sort options
echo -e "\n--- Step 2a: Listing models (default view) ---"
lmstrix list
echo -e "\n--- Step 2b: Listing models sorted by context size ---"
lmstrix list --sort ctx
echo -e "\n--- Step 2c: Showing just model IDs ---"
lmstrix list --show id
echo "Model listing demonstrations complete."

# Step 3: Test a model's context length
# We'll use a common model identifier that users might have
echo -e "\n--- Step 3: Testing a model's context length ---"
echo "Note: This may take several minutes depending on the model and your hardware."
# Common model patterns users might have:
# "llama", "mistral", "qwen", "phi", "gemma", "codellama"
MODEL_ID="llama" # <--- CHANGE THIS to match a model you have downloaded
echo "Looking for models matching: $MODEL_ID"
# Show models matching the pattern
lmstrix list --show id | grep -i "$MODEL_ID" || echo "No models found matching '$MODEL_ID'"
echo -e "\nTesting model: $MODEL_ID"
lmstrix test --model_id "$MODEL_ID" --verbose
echo "Context test complete."

# Step 4: Run inference with new context control features
# Demonstrates --out_ctx instead of deprecated --max_tokens
echo -e "\n--- Step 4a: Running basic inference ---"
lmstrix infer "What is the capital of France?" "$MODEL_ID" --out_ctx 50

echo -e "\n--- Step 4b: Running inference with specific loading context ---"
lmstrix infer "Explain quantum computing in simple terms." "$MODEL_ID" --in_ctx 4096 --out_ctx 200

echo -e "\n--- Step 4c: Checking if model is already loaded (reuse demo) ---"
lmstrix infer "What is 2+2?" "$MODEL_ID" --out_ctx 10

echo -e "\nInference demonstrations complete."

echo -e "\n### Workflow Demo Finished ###"