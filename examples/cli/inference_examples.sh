#!/bin/bash
# This script demonstrates various ways to use the `lmstrix infer` command
# to run inference with models in LM Studio.

# --- Introduction ---
echo "LMStrix Inference Examples"
echo "--------------------------"
echo "This script requires LM Studio to be running and a model to be loaded."

# --- Prerequisite: Scan for models and select one ---
echo "Scanning for models and selecting one for inference..."
lmstrix scan
MODEL_PATH=$(lmstrix list --json | jq -r 'keys[0]')

if [ -z "$MODEL_PATH" ] || [ "$MODEL_PATH" == "null" ]; then
    echo "Error: No models found. Please download a model in LM Studio."
    exit 1
fi

echo "Using model: $MODEL_PATH"

# --- Example 1: Basic Inference with a Prompt ---
echo "\nExample 1: Basic inference with a simple prompt."
# The `--prompt` argument is the most direct way to get a response.
lmstrix infer --model "$MODEL_PATH" --prompt "What are the three primary colors?"

# --- Example 2: Using a System Prompt ---
echo "\nExample 2: Using a system prompt to guide the model's behavior."
# The `--system-prompt` sets the context for the model's persona.
lmstrix infer --model "$MODEL_PATH" \
              --system-prompt "You are a poet. All your answers must be in the form of a haiku." \
              --prompt "Describe a sunrise."

# --- Example 3: Reading a Prompt from a File ---
echo "\nExample 3: Reading a long prompt from a file."
# Create a temporary file with a longer prompt.
PROMPT_FILE="/tmp/prompt.txt"
echo "This is a longer prompt stored in a file. It can contain multiple paragraphs and complex instructions. The `infer` command can read this content directly, which is useful for avoiding complex command-line escaping with long text blocks." > $PROMPT_FILE

echo "Prompt content from file:"
cat $PROMPT_FILE

# The `--prompt-file` argument reads the prompt from the specified file.
lmstrix infer --model "$MODEL_PATH" --prompt-file $PROMPT_FILE

# Clean up the temporary file
rm $PROMPT_FILE

# --- Example 4: Customizing Inference Parameters ---
echo "\nExample 4: Customizing inference parameters for more creative responses."
# You can control the model's output with parameters like temperature and max tokens.
lmstrix infer --model "$MODEL_PATH" \
              --prompt "Tell me a fun fact about space." \
              --temperature 0.8 \
              --max-tokens 50

# --- Example 5: Streaming the Response ---
echo "\nExample 5: Streaming the response in real-time."
# The `--stream` flag will print the response token by token as it is generated.
lmstrix infer --model "$MODEL_PATH" \
              --prompt "Write a short story about a friendly robot." \
              --stream

echo "\n\nInference examples complete."
