#!/bin/bash
# this_file: examples/cli/model_state_demo.sh
#
# Demonstration of model state persistence in LMStrix
# Shows how models remain loaded across multiple infer calls
#

set -e

echo "### LMStrix Model State Persistence Demo ###"
echo ""
echo "This demo shows how LMStrix now keeps models loaded between calls"
echo "for better performance and resource efficiency."
echo ""

MODEL_ID="llama-3.2-3b-instruct"  # Change this to match your model

# Step 1: First inference with explicit model and context
echo "=== Step 1: First inference with explicit model and context ==="
echo "Command: lmstrix infer \"What is 2+2?\" -m \"$MODEL_ID\" --out_ctx \"25%\" --verbose"
echo "(This will load the model with specified context)"
echo ""
lmstrix infer "What is 2+2?" -m "$MODEL_ID" --out_ctx "25%" --verbose || echo "Failed"

echo ""
echo "=== Step 2: Second inference without in_ctx ==="
echo "Command: lmstrix infer \"What is 3+3?\" -m \"$MODEL_ID\" --verbose"
echo "(This should reuse the already loaded model)"
echo ""
sleep 2
lmstrix infer "What is 3+3?" -m "$MODEL_ID" --verbose || echo "Failed"

echo ""
echo "=== Step 3: Third inference without model_id ==="
echo "Command: lmstrix infer \"What is 4+4?\" --verbose"
echo "(This should use the last-used model: $MODEL_ID)"
echo ""
sleep 2
lmstrix infer "What is 4+4?" --verbose || echo "Failed"

echo ""
echo "=== Demo Complete ==="
echo ""
echo "Key features demonstrated:"
echo "1. Models stay loaded between infer calls when in_ctx is not specified"
echo "2. Last-used model is remembered when -m is not specified"
echo "3. Better performance by avoiding repeated model loading/unloading"
echo ""
echo "Check the verbose output above to see:"
echo "- First call: 'Loading with optimal context...'"
echo "- Second call: 'Model already loaded... reusing...'"
echo "- Third call: 'Using last-used model...'"