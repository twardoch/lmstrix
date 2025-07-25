# LMStrix: The Unofficial Toolkit for Mastering LM Studio

LMStrix is a professional, installable Python toolkit designed to supercharge your interaction with [LM Studio](https://lmstudio.ai/). It provides a powerful command-line interface (CLI) and a clean Python API for managing, testing, and running local language models, with a standout feature: the **Adaptive Context Optimizer**.

**For the full documentation, please visit the [LMStrix GitHub Pages site](https://twardoch.github.io/lmstrix/).**

## Key Features

- **Automatic Context Optimization**: Discover the true context limit of any model with the `optimize` command.
- **Full Model Management**: Programmatically `list` available models and `scan` for newly downloaded ones.
- **Flexible Inference Engine**: Run inference with a powerful two-phase prompt templating system that separates prompt structure from its content.
- **Rich CLI**: A beautiful and intuitive command-line interface built with `rich` and `fire`.
- **Modern Python API**: An `async`-first API designed for high-performance, concurrent applications.

## Installation

```bash
# Using pip
pip install lmstrix

# Using uv (recommended)
uv pip install lmstrix
```

**For more detailed installation instructions, see the [Installation page](https://twardoch.github.io/lmstrix/installation/).**

## Quick Start

### Command-Line Interface (CLI)

```bash
# First, scan for available models in LM Studio
lmstrix scan

# List all models with their test status
lmstrix list

# Test the context limit for a specific model
lmstrix test "model-id-here"

# Run inference on a model
lmstrix infer "Your prompt here" --model "model-id" --max-tokens 150
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
    print(models)
    
    # Test a specific model's context limits
    model_id = models[0].id if models else None
    if model_id:
        result = await lms.test_model(model_id)
        print(result)
    
    # Run inference
    if model_id:
        response = await lms.infer(
            prompt="What is the meaning of life?",
            model_id=model_id,
            max_tokens=100
        )
        print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
```

**For more detailed usage instructions and examples, see the [Usage page](https://twardoch.github.io/lmstrix/usage/) and the [API Reference](https://twardoch.github.io/lmstrix/api/).**

## Development

```bash
# Clone the repository
git clone https://github.com/twardoch/lmstrix
cd lmstrix

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run the test suite
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
