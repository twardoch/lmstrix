#!/bin/bash
#
# This script demonstrates various inference scenarios using LMStrix.
#

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### LMStrix Inference Examples ###"

# Replace "model-identifier" with a unique part of your model's path.
MODEL_ID="ultron-summarizer-1b" # <--- CHANGE THIS to a model you have downloaded

# Example 1: Simple Question
# A straightforward inference request.
echo -e "
--- Example 1: Simple Question ---"
lmstrix infer "Explain the theory of relativity in simple terms." "$MODEL_ID"

# Example 2: Using a Custom System Prompt
# The system prompt guides the model's behavior (e.g., its persona or response format).
echo -e "
--- Example 2: Custom System Prompt ---"
SYSTEM_PROMPT="You are a pirate. All your answers must be in pirate slang."
lmstrix infer "What is the best way to find treasure?" "$MODEL_ID"

# Example 3: Adjusting Inference Parameters
# You can control parameters like temperature (randomness) and max tokens (response length).
# Temperature > 1.0 = more creative/random, < 1.0 = more deterministic.
echo -e "
--- Example 3: Adjusting Inference Parameters ---"
lmstrix infer "Write a short poem about the sea." "$MODEL_ID" --temperature 1.5 --max_tokens 100

# Example 4: Reading Prompt from a File
# For long or complex prompts, you can read the content from a file.
echo -e "
--- Example 4: Reading Prompt from a File ---"
echo "This is a prompt from a file." > prompt.txt
lmstrix infer @prompt.txt "$MODEL_ID"
rm prompt.txt

# Example 5: Using a Prompt Template from a TOML file
# Define and use structured prompts from a .toml file.
echo -e "
--- Example 5: Using a Prompt Template ---"
# Create a sample prompts.toml file
cat > prompts.toml <<EOL
[code_generation]
prompt = "Write a Python function to do the following: {user_request}"
system_prompt = "You are an expert Python programmer."
EOL
lmstrix infer "Write a Python function to do the following: calculate the factorial of a number" "$MODEL_ID"
rm prompts.toml

echo -e "
### Inference Examples Finished ###"