#!/bin/bash
# inference_examples.sh - Various inference scenarios for lmstrix CLI
# This example demonstrates different ways to run inference with models

echo "=== LMStrix Inference Examples ==="
echo "This example shows various inference scenarios"
echo

# Example 1: Basic inference
echo "Example 1: Basic inference with default parameters"
echo "Command: python -m lmstrix infer 'What is the capital of France?' --model_id='your-model-id'"
# python -m lmstrix infer "What is the capital of France?" --model_id="llama-3.2-1b-instruct"
echo

# Example 2: Inference with temperature control
echo "Example 2: Creative writing with high temperature"
echo "Command: python -m lmstrix infer 'Write a short story about a robot' --model_id='your-model-id' --temperature=0.9"
# python -m lmstrix infer "Write a short story about a robot learning to paint" --model_id="llama-3.2-1b-instruct" --temperature=0.9
echo

echo "Example 3: Factual responses with low temperature"
echo "Command: python -m lmstrix infer 'List the planets in our solar system' --model_id='your-model-id' --temperature=0.1"
# python -m lmstrix infer "List the planets in our solar system in order from the sun" --model_id="llama-3.2-1b-instruct" --temperature=0.1
echo

# Example 3: Controlling output length
echo "Example 4: Controlling output length with max_tokens"
echo "Command: python -m lmstrix infer 'Explain machine learning' --model_id='your-model-id' --max_tokens=50"
# python -m lmstrix infer "Explain machine learning" --model_id="llama-3.2-1b-instruct" --max_tokens=50
echo

echo "Example 5: Unlimited output length"
echo "Command: python -m lmstrix infer 'Write a detailed guide' --model_id='your-model-id' --max_tokens=-1"
# python -m lmstrix infer "Write a detailed guide on making coffee" --model_id="llama-3.2-1b-instruct" --max_tokens=-1
echo

# Example 4: Code generation
echo "Example 6: Code generation example"
echo "Command: python -m lmstrix infer 'Write a Python function to calculate factorial' --model_id='your-model-id' --temperature=0.2"
# python -m lmstrix infer "Write a Python function to calculate the factorial of a number" --model_id="llama-3.2-1b-instruct" --temperature=0.2
echo

# Example 5: Multi-line prompts
echo "Example 7: Using multi-line prompts"
echo "Command: python -m lmstrix infer \$'Line 1\\nLine 2\\nLine 3' --model_id='your-model-id'"
# python -m lmstrix infer $'Context: You are a helpful assistant.\nTask: Summarize the benefits of exercise.\nFormat: Bullet points' --model_id="llama-3.2-1b-instruct"
echo

# Example 6: Verbose mode for debugging
echo "Example 8: Running inference in verbose mode"
echo "Command: python -m lmstrix infer 'Hello' --model_id='your-model-id' --verbose"
echo "Verbose mode shows:"
echo "- Model loading progress"
echo "- Token usage"
echo "- Inference time"
echo "- Any errors or warnings"
# python -m lmstrix infer "Hello" --model_id="llama-3.2-1b-instruct" --verbose
echo

# Example 7: Testing context limits with inference
echo "Example 9: Testing large context with inference"
echo "First, check the model's tested context limit:"
echo "Command: python -m lmstrix list"
echo
echo "Then create a prompt near that limit:"
echo "Command: python -m lmstrix infer 'Please analyze this text: [very long text]' --model_id='your-model-id'"
echo

# Example 8: Comparing models
echo "Example 10: Comparing responses from different models"
echo "Run the same prompt with different models to compare:"
echo "python -m lmstrix infer 'Explain quantum computing' --model_id='model-1'"
echo "python -m lmstrix infer 'Explain quantum computing' --model_id='model-2'"
echo

echo "=== Inference Tips ==="
echo "- Use low temperature (0.1-0.3) for factual, consistent responses"
echo "- Use high temperature (0.7-0.9) for creative, varied responses"
echo "- Set max_tokens=-1 for unlimited length (until model stops)"
echo "- Check tested context limits before using large prompts"
echo "- Use verbose mode to debug issues or see performance metrics"