# LMStrix

A professional, installable PyPI package for managing and utilizing models with LM Studio.

## Overview

LMStrix is a robust toolkit that provides seamless integration with LM Studio's local server, enabling efficient model management and inference. The standout feature is the **Adaptive Context Optimizer**, which automatically determines the maximum operational context length for any given model, eliminating the need for manual tuning.

## Key Features

- **Model Management**: Easily discover, list, and manage LM Studio models
- **Adaptive Context Optimization**: Automatically find the optimal context window for each model using binary search
- **Flexible Inference Engine**: Run inference with customizable prompts and context management
- **Two-Phase Prompt Resolution**: Advanced templating system with placeholder resolution
- **Rich CLI**: Beautiful command-line interface with formatted tables and progress indicators
- **Async-First Design**: Built on modern async/await patterns for optimal performance
- **Robust Error Handling**: Comprehensive exception hierarchy and retry logic

## Installation

```bash
pip install lmstrix
```

## Quick Start

### Command Line Interface

```bash
# List available models
lmstrix models list

# Scan for new models
lmstrix models scan

# Run inference
lmstrix infer --model "llama-3.1" --prompt "greeting"

# Optimize a model's context window
lmstrix optimize llama-3.1
```

### Python API

```python
from lmstrix import LMStrix

# Initialize client
client = LMStrix()

# List models
models = await client.list_models()
for model in models:
    print(f"{model.id}: {model.context_limit} tokens")

# Run inference
result = await client.infer(
    model_id="llama-3.1",
    prompt_template="Summarize this text: {text}",
    context={"text": "Your long document here..."}
)
print(result.content)

# Optimize context window
optimization = await client.optimize_context("llama-3.1")
print(f"Optimal context: {optimization.optimal_size} tokens")
```

## Architecture

LMStrix is organized into modular components:

- **`api/`**: LM Studio API client with retry logic
- **`core/`**: Core business logic (models, inference, optimization)
- **`loaders/`**: Data loaders for models, prompts, and contexts
- **`cli/`**: Command-line interface using Fire and Rich
- **`utils/`**: Shared utilities

## Dependencies

- `pydantic`: Data validation and settings management
- `litellm`: Unified LLM API interface
- `rich`: Terminal formatting and progress bars
- `fire`: CLI framework
- `tenacity`: Retry logic
- `loguru`: Advanced logging
- `tiktoken`: Token counting

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest

# Format code
python -m ruff format src/

# Check linting
python -m ruff check src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to our repository.

## Support

For issues, feature requests, or questions, please file an issue on our GitHub repository.