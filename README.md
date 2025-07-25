# LMStrix: The Unofficial Toolkit for Mastering LM Studio

LMStrix is a professional, installable Python toolkit designed to supercharge your interaction with [LM Studio](https://lmstudio.ai/). It provides a powerful command-line interface (CLI) and a clean Python API for managing, testing, and running local language models, with a standout feature: the **Adaptive Context Optimizer**.

## Why LMStrix? The Problem it Solves

Working with local LLMs via LM Studio is powerful, but it comes with challenges:

1.  **The Context Window Mystery**: What's the *true* maximum context a model can handle on your machine? Advertised context lengths are often theoretical. The practical limit depends on your hardware, the model's architecture, and LM Studio's own overhead. Finding this limit manually is a tedious, frustrating process of trial and error.
2.  **Repetitive Workflows**: Managing models, crafting prompts, and running inference often involves repetitive boilerplate code or manual steps in the LM Studio UI.
3.  **Lack of Programmatic Control**: The UI is great for exploration, but developers building applications on top of local LLMs need a robust, scriptable interface for automation and integration.

LMStrix solves these problems by providing a seamless, developer-friendly toolkit that automates the tedious parts and lets you focus on building.

## How It Works: The Adaptive Context Optimizer

The core innovation in LMStrix is its ability to **automatically discover the maximum operational context length** for any model loaded in LM Studio.

It uses a sophisticated **binary search algorithm**:
1.  It starts with a wide range for the possible context size.
2.  It sends a specially crafted prompt to the model, progressively increasing the amount of "filler" text.
3.  It analyzes the model's response (or lack thereof) to see if it successfully processed the context.
4.  By repeatedly narrowing the search range, it quickly pinpoints the precise token count where the model's performance degrades or fails.

This gives you a reliable, empirical measurement of the model's true capabilities on your specific hardware, eliminating guesswork and ensuring your applications run with optimal performance.

## Key Features

- **Automatic Context Optimization**: Discover the true context limit of any model with the `optimize` command.
- **Full Model Management**: Programmatically `list` available models and `scan` for newly downloaded ones.
- **Flexible Inference Engine**: Run inference with a powerful two-phase prompt templating system that separates prompt structure from its content.
- **Rich CLI**: A beautiful and intuitive command-line interface built with `rich` and `fire`, providing formatted tables, progress indicators, and clear feedback.
- **Modern Python API**: An `async`-first API designed for high-performance, concurrent applications.
- **Robust and Resilient**: Features automatic retries with exponential backoff for network requests and a comprehensive exception hierarchy.
- **Lightweight and Focused**: Built with a minimal set of modern, high-quality dependencies.

## Installation

```bash
# Using pip
pip install lmstrix

# Using uv (recommended)
uv pip install lmstrix

# For development
git clone https://github.com/twardoch/lmstrix
cd lmstrix
pip install -e .
```

## Quick Start

### Command-Line Interface (CLI)

```bash
# First, scan for available models in LM Studio
lmstrix scan

# List all models with their test status
lmstrix list

# Test the context limit for a specific model
lmstrix test "model-id-here"

# Test all untested models
lmstrix test --all

# Run inference on a model
lmstrix infer "Your prompt here" --model "model-id" --max-tokens 150

# Run inference with a prompt file
lmstrix infer "@prompts.toml:greeting" --model "model-id"

# Enable verbose output for debugging
lmstrix scan --verbose
lmstrix test "model-id" --verbose
```

### Python API

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

### Batch Processing Example

```python
from lmstrix.api.client import LMStudioClient
from lmstrix.core.scanner import ModelScanner

# Process multiple models
client = LMStudioClient()
scanner = ModelScanner(client)

# Scan and test all models
for model in scanner.scan():
    if not model.tested_max_context:
        print(f"Testing {model.id}...")
        # Testing happens automatically via CLI or API
```

## Architecture

LMStrix is designed with a clean, modular architecture:

- **`api/`**: A dedicated client for communicating with the LM Studio local server API.
- **`core/`**: The heart of the application, containing the core business logic for models, inference, and the context optimization algorithm.
- **`loaders/`**: Handles loading and managing data for models, prompts, and context files.
- **`cli/`**: Implements the command-line interface.
- **`utils/`**: Shared utilities and helper functions.

## How Context Testing Works

LMStrix uses an innovative binary search algorithm to find the true operational context limit of each model:

1. **Initial Range**: Starts with the model's declared context size as the upper bound
2. **Binary Search**: Tests the model with progressively refined context sizes
3. **Validation**: Each test sends a simple prompt ("2+2=") padded with filler text to reach the target context size
4. **Result Verification**: Only marks a context size as "working" if the model returns the correct answer ("4")
5. **Optimization**: Finds the maximum context size that reliably works on your hardware

This process typically takes 30-60 seconds per model and saves the results for future use.

## Development

```bash
# Clone the repository
git clone https://github.com/twardoch/lmstrix
cd lmstrix

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run the test suite
pytest

# Run with coverage
pytest --cov=src/lmstrix --cov-report=html

# Format code
black .
ruff format .

# Lint code
ruff check .
mypy src/lmstrix

# Build the package
python -m build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are highly welcome! Please feel free to submit pull requests or file issues on our GitHub repository.

## Requirements

- Python 3.10 or higher
- LM Studio installed and running locally
- At least one model downloaded in LM Studio

## Support

For bugs, feature requests, or general questions, please [file an issue](https://github.com/twardoch/lmstrix/issues) on our GitHub repository.