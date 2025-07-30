#!/bin/bash
#
# This script demonstrates various inference scenarios using LMStrix.
# Shows new features: --in_ctx, --out_ctx, --file_prompt, --dict, --force-reload
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Inference Examples ###"

# Replace with a model identifier that matches your downloaded models
# Common patterns: "llama", "mistral", "qwen", "phi", "gemma", "codellama"
MODEL_ID="llama" # <--- CHANGE THIS to match a model you have downloaded

# Example 1: Simple Question with new --out_ctx parameter
echo -e "\n--- Example 1: Simple Question with Output Context Control ---"
lmstrix infer "Explain the theory of relativity in simple terms." "$MODEL_ID" --out_ctx 200

# Example 2: Context Control - Load model with specific context size
echo -e "\n--- Example 2: Load Model with Specific Context Size ---"
lmstrix infer "What are the benefits of renewable energy?" "$MODEL_ID" --in_ctx 8192 --out_ctx 150

# Example 3: Load model without context specification (--in_ctx 0)
echo -e "\n--- Example 3: Load Model with Default Context ---"
lmstrix infer "What is machine learning?" "$MODEL_ID" --in_ctx 0 --out_ctx 100

# Example 4: Model State Detection - Second call reuses loaded model
echo -e "\n--- Example 4: Model State Detection (Reuse) ---"
echo "First call - loads the model:"
lmstrix infer "What is Python?" "$MODEL_ID" --out_ctx 50
echo -e "\nSecond call - reuses loaded model:"
lmstrix infer "What is JavaScript?" "$MODEL_ID" --out_ctx 50

# Example 5: Force Reload - Reload model even if already loaded
echo -e "\n--- Example 5: Force Model Reload ---"
lmstrix infer "What is artificial intelligence?" "$MODEL_ID" --force-reload --out_ctx 100

# Example 6: Using TOML Prompt Files with Parameters
echo -e "\n--- Example 6: Using Prompt Templates from TOML ---"
# First, let's check if prompts.toml exists
if [ -f "examples/prompts.toml" ]; then
    PROMPT_FILE="examples/prompts.toml"
elif [ -f "prompts.toml" ]; then
    PROMPT_FILE="prompts.toml"
else
    # Create a simple prompts.toml for demonstration
    cat > temp_prompts.toml <<EOL
[greetings]
formal = "Good day, {{name}}. How may I assist you with {{topic}}?"
casual = "Hey {{name}}! What's up with {{topic}}?"

[code]
review = "Please review this {{language}} code and suggest improvements: {{code}}"
explain = "Explain this {{language}} code in simple terms: {{code}}"
EOL
    PROMPT_FILE="temp_prompts.toml"
fi

echo "Using prompt file: $PROMPT_FILE"
lmstrix infer greetings.formal "$MODEL_ID" --file_prompt "$PROMPT_FILE" --dict "name=Alice,topic=Python" --out_ctx 100

# Example 7: Multiple Parameters with Different Format
echo -e "\n--- Example 7: Code Review with Template ---"
lmstrix infer code.review "$MODEL_ID" --file_prompt "$PROMPT_FILE" --dict "language=Python,code=def factorial(n): return 1 if n <= 1 else n * factorial(n-1)" --out_ctx 300

# Example 8: Adjusting Temperature for Creative Output
echo -e "\n--- Example 8: Creative Writing with High Temperature ---"
lmstrix infer "Write a short poem about the sea." "$MODEL_ID" --temperature 1.5 --out_ctx 150

# Example 9: Low Temperature for Deterministic Output
echo -e "\n--- Example 9: Math Problem with Low Temperature ---"
lmstrix infer "Calculate: 25 * 4 + 10 - 5" "$MODEL_ID" --temperature 0.1 --out_ctx 20

# Example 10: Combining Features - Context Control + Template + Temperature
echo -e "\n--- Example 10: Combined Features Demo ---"
lmstrix infer greetings.casual "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --dict "name=Bob,topic=quantum computing" \
    --in_ctx 4096 \
    --out_ctx 150 \
    --temperature 0.8

# Cleanup temporary file if created
if [ "$PROMPT_FILE" = "temp_prompts.toml" ]; then
    rm temp_prompts.toml
fi

echo -e "\n### Inference Examples Finished ###"
echo -e "\nKey takeaways:"
echo "- Use --out_ctx instead of deprecated --max_tokens"
echo "- Use --in_ctx to control model loading context size"
echo "- Use --file_prompt with --dict for template-based prompts"
echo "- Models are reused when already loaded (unless --force-reload)"
echo "- Combine features for advanced use cases"