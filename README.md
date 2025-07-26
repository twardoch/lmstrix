LMStrix is a professional, installable Python toolkit designed to supercharge your interaction with [LM Studio](https://lmstudio.ai/). It provides a powerful command-line interface (CLI) and a clean Python API for managing, testing, and running local language models, with a standout feature: the **Adaptive Context Optimizer**.

**For the full documentation, please visit the [LMStrix GitHub Pages site](https://twardoch.github.io/lmstrix/).**

## Key Features

- **Automatic Context Optimization**: Discover the true context limit of any model with the `test` command.
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

# Test all untested models with enhanced safety controls
lmstrix test --all --threshold 102400

# Test all models at a specific context size
lmstrix test --all --ctx 32768

# Sort and filter model listings
lmstrix list --sort dtx  # Sort by declared context size descending
lmstrix list --show json --sort size  # Export as JSON sorted by model size

# Run inference on a model
lmstrix infer "Your prompt here" --model "model-id" --max-tokens 150
```

### Python API

```python
from lmstrix import LMStrix

def main():
    # Initialize the client
    lms = LMStrix()
    
    # Scan for available models
    lms.scan_models()
    
    # List all models
    models = lms.list_models()
    print(models)
    
    # Test a specific model's context limits
    model_id = models[0].id if models else None
    if model_id:
        result = lms.test_model(model_id)
        print(result)
    
    # Run inference
    if model_id:
        response = lms.infer(
            prompt="What is the meaning of life?",
            model_id=model_id,
            max_tokens=100
        )
        print(response.content)

if __name__ == "__main__":
    main()
```

**For more detailed usage instructions and examples, see the [Usage page](https://twardoch.github.io/lmstrix/usage/) and the [API Reference](https://twardoch.github.io/lmstrix/api/).**

## Enhanced Testing Strategy

LMStrix uses a sophisticated testing algorithm to safely and efficiently discover true model context limits:

### Safety Features
- **Threshold Protection**: Default 102,400 token limit prevents system crashes from oversized contexts
- **Smart Validation**: Checks against previously known bad context sizes to avoid repeated failures
- **Progressive Testing**: Incremental approach minimizes resource usage while maximizing accuracy

### Testing Algorithm
1. **Initial Verification**: Tests at small context (1024) to verify model loads
2. **Threshold Test**: Tests at `min(threshold, declared_limit)` for safe initial assessment  
3. **Incremental Search**: If threshold succeeds, incrementally increases by 10,240 tokens
4. **Binary Search**: On failure, performs efficient binary search to find exact limit
5. **Progress Persistence**: Saves results after each test for resumable operations

### Multi-Model Optimization
- **Batch Processing**: `--all` flag efficiently tests multiple models with minimal loading/unloading
- **Smart Sorting**: Tests models in optimal order to reduce resource cycling
- **Flexible Filtering**: Target specific context sizes or model subsets
- **Rich Output**: Beautiful tables showing results, efficiency, and progress

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

## Changelog

All notable changes to this project are documented in the [CHANGELOG.md](https://twardoch.github.io/lmstrix/changelog) file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
