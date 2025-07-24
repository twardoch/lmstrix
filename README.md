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
uv pip install --system lmstrix
```

## Quick Start

### Command-Line Interface (CLI)

```bash
# Discover the optimal context window for a model
lmstrix optimize "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# List all available models with their detected context limits
lmstrix models list

# Scan for any new models you've added to LM Studio
lmstrix models scan

# Run inference using a prompt template
lmstrix infer --model "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" --prompt "greeting"
```

### Python API

```python
import asyncio
from lmstrix import LMStrix

async def main():
    # Initialize the client
    client = LMStrix()

    # Optimize the context window for a specific model
    print("Optimizing context, this may take a moment...")
    optimization = await client.optimize_context("Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
    print(f"Optimal context found: {optimization.optimal_size} tokens")
    print("-" * 20)

    # List all models and their properties
    print("Available Models:")
    models = await client.list_models()
    for model in models:
        limit = model.context_limit or "Not yet optimized"
        print(f"- {model.id}: {limit} tokens")
    print("-" * 20)

    # Run inference with a template
    print("Running inference...")
    result = await client.infer(
        model_id="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        prompt_template="Summarize this text: {text}",
        context={"text": "Your long document goes here..."}
    )
    print("Inference Result:")
    print(result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

LMStrix is designed with a clean, modular architecture:

- **`api/`**: A dedicated client for communicating with the LM Studio local server API.
- **`core/`**: The heart of the application, containing the core business logic for models, inference, and the context optimization algorithm.
- **`loaders/`**: Handles loading and managing data for models, prompts, and context files.
- **`cli/`**: Implements the command-line interface.
- **`utils/`**: Shared utilities and helper functions.

## Development

```bash
# Install in editable mode for development
pip install -e .

# Run the test suite
pytest

# Format and lint the codebase
ruff format .
ruff check .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are highly welcome! Please feel free to submit pull requests or file issues on our GitHub repository.

## Support

For bugs, feature requests, or general questions, please [file an issue](https://github.com/yourusername/lmstrix/issues) on our GitHub repository.