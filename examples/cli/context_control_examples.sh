#!/bin/bash
#
# This script demonstrates advanced context control features in LMStrix.
# Shows --in_ctx usage, model state detection, and context optimization.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Context Control Examples ###"

# Replace with a model identifier that matches your downloaded models
MODEL_ID="llama" # <--- CHANGE THIS to match a model you have downloaded

# Example 1: Understanding Context Parameters
echo -e "\n--- Example 1: Understanding Context Parameters ---"
echo "LMStrix has two context parameters:"
echo "  --in_ctx: Controls the context size when LOADING the model"
echo "  --out_ctx: Controls the maximum tokens to GENERATE"
echo -e "\nLet's see them in action..."

# Example 2: Default Context Loading
echo -e "\n--- Example 2: Default Context Loading ---"
echo "When --in_ctx is not specified, LMStrix uses the optimal context:"
lmstrix infer "What is machine learning?" "$MODEL_ID" --out_ctx 50 --verbose
echo "(Model loaded with optimal context based on testing or declared limit)"

# Example 3: Specific Context Loading
echo -e "\n--- Example 3: Loading with Specific Context ---"
echo "Load model with exactly 4096 tokens of context:"
lmstrix infer "Explain neural networks briefly." "$MODEL_ID" --in_ctx 4096 --out_ctx 100 --verbose
echo "(Model loaded with 4096 token context)"

# Example 4: Model State Detection
echo -e "\n--- Example 4: Model State Detection ---"
echo "First inference - model loads:"
lmstrix infer "What is 5 + 5?" "$MODEL_ID" --out_ctx 10
echo -e "\nSecond inference - model already loaded (should be faster):"
lmstrix infer "What is 10 + 10?" "$MODEL_ID" --out_ctx 10
echo "(Notice: Model was reused, not reloaded)"

# Example 5: Context Size Impact
echo -e "\n--- Example 5: Context Size Impact ---"
echo "Smaller context (faster loading, less memory):"
time lmstrix infer "Hello!" "$MODEL_ID" --in_ctx 2048 --out_ctx 10

echo -e "\nLarger context (slower loading, more memory):"
time lmstrix infer "Hello!" "$MODEL_ID" --in_ctx 16384 --out_ctx 10

# Example 6: Zero Context Loading
echo -e "\n--- Example 6: Zero Context Loading (--in_ctx 0) ---"
echo "Load model without specifying context (uses model's default):"
lmstrix infer "What is Python?" "$MODEL_ID" --in_ctx 0 --out_ctx 50
echo "(Model loaded with its default context configuration)"

# Example 7: Context Optimization Strategy
echo -e "\n--- Example 7: Context Optimization Strategy ---"
echo "For best performance:"
echo "1. Test your model first to find optimal context:"
echo "   lmstrix test --model_id $MODEL_ID"
echo -e "\n2. Use the tested context for inference:"
echo "   lmstrix infer 'prompt' $MODEL_ID --in_ctx <tested_value>"
echo -e "\n3. Or let LMStrix choose automatically (omit --in_ctx)"

# Example 8: Long Context Use Case
echo -e "\n--- Example 8: Long Context Use Case ---"
echo "Processing a long document (simulated):"
LONG_PROMPT="Summarize this text: The history of artificial intelligence began in antiquity, with myths, stories and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. The seeds of modern AI were planted by classical philosophers who attempted to describe the process of human thinking as the mechanical manipulation of symbols."
echo "Prompt length: ${#LONG_PROMPT} characters"
lmstrix infer "$LONG_PROMPT" "$MODEL_ID" --in_ctx 8192 --out_ctx 150

# Example 9: Memory-Conscious Loading
echo -e "\n--- Example 9: Memory-Conscious Loading ---"
echo "For limited memory systems, use smaller context:"
lmstrix infer "What is RAM?" "$MODEL_ID" --in_ctx 2048 --out_ctx 50
echo "(Smaller context = less GPU/RAM usage)"

# Example 10: Comparing Context Sizes
echo -e "\n--- Example 10: Context Size Comparison ---"
echo "Let's compare the same prompt with different contexts:"

echo -e "\nWith 2K context:"
lmstrix infer "Explain quantum computing" "$MODEL_ID" --in_ctx 2048 --out_ctx 100

echo -e "\nWith 8K context:"
lmstrix infer "Explain quantum computing" "$MODEL_ID" --in_ctx 8192 --out_ctx 100

echo -e "\nNote: Larger context doesn't always mean better output for simple prompts"

echo -e "\n### Context Control Examples Finished ###"
echo -e "\nKey takeaways:"
echo "- --in_ctx controls model loading context (memory usage)"
echo "- --out_ctx controls generation length"
echo "- Models are reused when possible for efficiency"
echo "- Optimal context depends on your use case"
echo "- Test models first to find their true limits"