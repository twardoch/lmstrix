---
layout: default
title: Usage
---

## Command-Line Interface (CLI)

LMStrix provides a powerful and intuitive CLI for interacting with your local models.

### Scanning for Models

Before you can use LMStrix, you need to scan for available models in LM Studio. This command discovers all models that you have downloaded.

```bash
lmstrix scan
```

### Listing Models

To see a list of all discovered models, their context length, and test status, use the `list` command.

```bash
lmstrix list
```

### Testing Context Limits

This is the core feature of LMStrix. The `test` command automatically determines the maximum context window a model can handle on your machine.

```bash
# Test a specific model by its ID
lmstrix test "model-id-here"

# Test all models that haven't been tested yet
lmstrix test --all
```

For more details on how this works, see the [How It Works](./how-it-works.md) page.

### Running Inference

You can run inference directly from the command line.

```bash
# Run a simple prompt
lmstrix infer "Your prompt here" --model "model-id" --max-tokens 150

# Use a prompt from a file
lmstrix infer "@prompts.toml:greeting" --model "model-id"
```

### Verbose Mode

For more detailed output and debugging, you can use the `--verbose` flag with any command.

```bash
lmstrix scan --verbose
```

## Python API

The Python API provides a clean, `async`-first interface for programmatic access to LMStrix features.

```python
import asyncio
from lmstrix import LMStrix

async def main():
    # Initialize the client
    lms = LMStrix()
    
    # Scan for available models
    await lms.scan_models()
    
    # List all models
    models = await lms.list_models()
    for model in models:
        print(f"Model: {model.id}")
        print(f"  Context limit: {model.context_limit:,} tokens")
        print(f"  Tested limit: {model.tested_max_context or 'Not tested'}")
        print(f"  Status: {model.context_test_status}")
    
    # Test a specific model's context limits
    model_id = models[0].id if models else None
    if model_id:
        print(f"\nTesting context limits for {model_id}...")
        result = await lms.test_model(model_id)
        print(f"Optimal context: {result.tested_max_context} tokens")
        print(f"Test status: {result.context_test_status}")
    
    # Run inference
    if model_id:
        response = await lms.infer(
            prompt="What is the meaning of life?",
            model_id=model_id,
            max_tokens=100
        )
        print(f"\nInference result:\n{response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```
