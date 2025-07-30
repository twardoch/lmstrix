# LMStrix

LMStrix is a professional Python toolkit designed to supercharge your interaction with [LM Studio](https://lmstudio.ai/). It provides a powerful command-line interface (CLI) and Python API for managing, testing, and running local language models, with a standout feature: **Adaptive Context Optimization**.

## Key Features

- **🔍 Automatic Context Discovery**: Binary search algorithm to find the true operational context limit of any model
- **📊 Beautiful Verbose Logging**: Enhanced stats display with emojis showing inference metrics, timing, and token usage
- **🚀 Smart Model Management**: Models persist between calls to reduce loading overhead
- **🎯 Flexible Inference Engine**: Run inference with powerful prompt templating and percentage-based output control
- **📋 Comprehensive Model Registry**: Track models, their context limits, and test results with JSON persistence
- **🛡️ Safety Controls**: Configurable thresholds and fail-safes to prevent system crashes
- **💻 Rich CLI Interface**: Beautiful terminal output with progress indicators and formatted tables

## Installation

```bash
# Using pip
pip install lmstrix

# Using uv (recommended)
uv pip install lmstrix
```

## Quick Start

### Command-Line Interface

```bash
# Scan for available models in LM Studio
lmstrix scan

# List all models with their context limits and test status
lmstrix list

# Test context limit for a specific model
lmstrix test llama-3.2-3b-instruct

# Test all untested models with safety threshold
lmstrix test --all --threshold 102400

# Run inference with enhanced verbose logging
lmstrix infer "What is the capital of Poland?" -m llama-3.2-3b-instruct --verbose

# Run inference with percentage-based output tokens
lmstrix infer "Explain quantum computing" -m llama-3.2-3b-instruct --out_ctx "25%"

# Use file-based prompts with templates
lmstrix infer summary -m llama-3.2-3b-instruct --file_prompt adam.toml --text_file document.txt

# Direct text input for prompts
lmstrix infer "Summarize: {{text}}" -m llama-3.2-3b-instruct --text "Your content here"
```

### Enhanced Verbose Output

When using `--verbose`, LMStrix provides comprehensive statistics:

```
════════════════════════════════════════════════════════════
🤖 MODEL: llama-3.2-3b-instruct
🔧 CONFIG: maxTokens=26214, temperature=0.7
📝 PROMPT (1 lines, 18 chars): Capital of Poland?
════════════════════════════════════════════════════════════
⠸ Running inference...
════════════════════════════════════════════════════════════
📊 INFERENCE STATS
⚡ Time to first token: 0.82s
⏱️  Total inference time: 11.66s
🔢 Predicted tokens: 338
📝 Prompt tokens: 5
🎯 Total tokens: 343
🚀 Tokens/second: 32.04
🛑 Stop reason: eosFound
════════════════════════════════════════════════════════════
```

### Python API

```python
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.core.inference_manager import InferenceManager

# Load model registry
registry = load_model_registry()

# List available models
models = registry.list_models()
print(f"Available models: {len(models)}")

# Run inference
manager = InferenceManager(verbose=True)
result = manager.infer(
    model_id="llama-3.2-3b-instruct",
    prompt="What is the meaning of life?",
    out_ctx=100,
    temperature=0.7
)

if result["succeeded"]:
    print(f"Response: {result['response']}")
    print(f"Tokens used: {result['tokens_used']}")
    print(f"Time: {result['inference_time']:.2f}s")
```

## Context Testing & Optimization

LMStrix uses a sophisticated binary search algorithm to discover true model context limits:

### Safety Features
- **Threshold Protection**: Configurable maximum context size to prevent system crashes
- **Progressive Testing**: Starts with small contexts and increases safely
- **Persistent Results**: Saves test results to avoid re-testing

### Testing Commands
```bash
# Test specific model
lmstrix test llama-3.2-3b-instruct

# Test all models with custom threshold
lmstrix test --all --threshold 65536

# Test at specific context size
lmstrix test --all --ctx 32768

# Reset and re-test a model
lmstrix test llama-3.2-3b-instruct --reset
```

## Model Management

### Registry Commands
```bash
# Scan for new models
lmstrix scan --verbose

# List models with different sorting
lmstrix list --sort size        # Sort by size
lmstrix list --sort ctx         # Sort by tested context
lmstrix list --show json        # Export as JSON

# Check system health
lmstrix health --verbose
```

### Model Persistence
Models stay loaded between inference calls for improved performance:
- When no explicit context is specified, models remain loaded
- Last-used model is remembered for subsequent calls
- Explicit context changes trigger model reloading

## Prompt Templating

LMStrix supports flexible prompt templating with TOML files:

```toml
# adam.toml
[aps]
prompt = """
You are an AI assistant skilled in Abstractive Proposition Segmentation.
Convert the following text: {{text}}
"""

[summary] 
prompt = "Create a comprehensive summary: {{text}}"
```

Use with CLI:
```bash
lmstrix infer aps --file_prompt adam.toml --text "Your text here"
lmstrix infer summary --file_prompt adam.toml --text_file document.txt
```

## Development

```bash
# Clone repository
git clone https://github.com/twardoch/lmstrix.git
cd lmstrix

# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
hatch run lint:all
```

## Project Structure

```
src/lmstrix/
├── cli/main.py              # CLI interface
├── core/
│   ├── inference_manager.py # Unified inference engine
│   ├── models.py            # Model registry
│   └── context_tester.py    # Context limit testing
├── api/client.py            # LM Studio API client
├── loaders/                 # Data loading utilities
└── utils/                   # Helper utilities
```

## Features in Detail

### Adaptive Context Optimizer
- Binary search algorithm for efficient context limit discovery
- Safety thresholds to prevent system crashes
- Automatic persistence of test results
- Resume capability for interrupted tests

### Enhanced Logging
- Beautiful emoji-rich output in verbose mode
- Comprehensive inference statistics
- Progress indicators for long operations
- Clear error messages with context

### Smart Model Management
- Automatic model discovery from LM Studio
- Persistent registry with JSON storage
- Model state tracking (loaded/unloaded)
- Batch operations for multiple models

## Requirements

- Python 3.11+
- LM Studio installed and configured
- Models downloaded in LM Studio

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests for any improvements.