# LMStrix Usage Examples

This directory contains comprehensive examples demonstrating all features of the LMStrix CLI and Python API, including the latest context control, prompt templates, and model state management features.

## Prerequisites

1. **LMStrix Installed**: Ensure you have installed LMStrix (`pip install lmstrix`)
2. **LM Studio Running**: Most examples require LM Studio running with at least one model downloaded
3. **Model Downloaded**: Download models in LM Studio (e.g., Llama, Mistral, Phi, Qwen)

**Note**: Examples use "llama" as a placeholder model ID. Update this to match your downloaded models. Run `lmstrix list` to see available models.

## Quick Start

Run all examples at once:
```bash
bash run_all_examples.sh
```

Or run individual examples as shown below.

---

## CLI Examples (`cli/`)

### Core Workflow Examples

#### `basic_workflow.sh`
Complete end-to-end workflow demonstrating:
- Model scanning with verbose output
- Listing models with `--sort` and `--show` options
- Context testing with new fixed strategy
- Inference with `--in_ctx` and `--out_ctx` parameters
- Model state reuse demonstration

```bash
bash cli/basic_workflow.sh
```

#### `model_testing.sh`
Advanced context testing features:
- Fixed context testing strategy (30k, 40k, 60k, etc.)
- `--threshold` parameter for safety limits
- `--fast` mode for quick validation
- `--ctx` for specific context testing
- Batch testing with `--all`
- Test resumption capabilities

```bash
bash cli/model_testing.sh
```

#### `inference_examples.sh`
Comprehensive inference scenarios:
- Context control with `--in_ctx` and `--out_ctx`
- Load without context specification (`--in_ctx 0`)
- Model state detection and reuse
- `--force-reload` demonstration
- TOML prompt templates with `--file_prompt` and `--dict`
- Temperature control for creativity

```bash
bash cli/inference_examples.sh
```

### New Feature Examples

#### `context_control_examples.sh` *(NEW)*
Deep dive into context management:
- Understanding `--in_ctx` vs `--out_ctx`
- Memory-conscious loading strategies
- Context size performance impact
- Long document processing
- Optimal context selection

```bash
bash cli/context_control_examples.sh
```

#### `model_state_demo.sh` *(NEW)*
Model state detection and management:
- How model reuse works
- Performance comparison (load vs reuse)
- Force reload scenarios
- Model switching strategies
- Context change behavior

```bash
bash cli/model_state_demo.sh
```

---

## Python API Examples (`python/`)

### Core API Usage

#### `basic_usage.py`
Fundamentals of the LMStrix Python API:
- Initializing `LMStrix` client
- Scanning and listing models
- Basic inference with `out_ctx`
- Advanced inference with `in_ctx`
- Model state detection
- Error handling

```bash
python3 python/basic_usage.py
```

#### `advanced_testing.py`
Context testing programmatically:
- Fixed context testing strategy
- Fast mode testing
- Custom threshold limits
- Specific context testing
- Batch testing multiple models
- Test result analysis

```bash
python3 python/advanced_testing.py
```

#### `custom_inference.py`
Advanced inference techniques:
- Context control (`in_ctx` and `out_ctx`)
- Temperature adjustment
- TOML prompt template loading
- Structured JSON output
- Model state reuse
- Force reload scenarios

```bash
python3 python/custom_inference.py
```

#### `batch_processing.py`
Working with multiple models:
- Batch testing strategies
- Model response comparison
- Performance benchmarking
- Efficiency analysis
- Smart testing order

```bash
python3 python/batch_processing.py
```

### New Python Examples

#### `prompt_templates_demo.py` *(NEW)*
Advanced prompt template features:
- Creating prompts programmatically
- Nested placeholder resolution
- Loading from TOML files
- Batch prompt resolution
- Missing placeholder handling
- Context injection with truncation

```bash
python3 python/prompt_templates_demo.py
```

---

## Prompt Templates (`prompts/`)

### Main Template File

#### `prompts.toml`
Comprehensive prompt template examples:
- Greetings (formal, casual, professional)
- Templates with internal references
- Code review and explanation prompts
- Research summarization templates
- Math and science prompts
- Creative writing templates
- Q&A formats
- System prompts

### Domain-Specific Templates

- `prompts/analysis.toml` - Data analysis prompts
- `prompts/coding.toml` - Programming assistance
- `prompts/creative.toml` - Creative writing
- `prompts/qa.toml` - Question answering

---

## Data Files (`data/`)

- `sample_context.txt` - Large text for context testing
- `test_questions.json` - Sample Q&A scenarios

---

## Key Features Demonstrated

### Context Management
- **`--in_ctx`**: Control model loading context size
- **`--out_ctx`**: Control maximum generation tokens
- **Model reuse**: Automatic reuse of loaded models
- **Force reload**: Refresh models with `--force-reload`

### Testing Enhancements
- **Fixed contexts**: Tests at 30k, 40k, 60k, 80k, 100k, 120k
- **Threshold safety**: Limit initial test size
- **Fast mode**: Skip semantic verification
- **Test resumption**: Continue interrupted tests

### Prompt Templates
- **TOML loading**: Load prompts from `.toml` files
- **Placeholders**: Dynamic value substitution
- **Nested references**: Templates can reference other templates
- **Batch resolution**: Process multiple prompts at once

### Performance Features
- **Smart sorting**: Optimal model testing order
- **Model state tracking**: Know when models are loaded
- **Efficiency metrics**: Track tested vs declared ratios
- **Batch operations**: Test or query multiple models

---

## Running Examples

### Individual Examples
```bash
# CLI examples
bash cli/basic_workflow.sh
bash cli/model_testing.sh
bash cli/inference_examples.sh
bash cli/context_control_examples.sh
bash cli/model_state_demo.sh

# Python examples
python3 python/basic_usage.py
python3 python/advanced_testing.py
python3 python/custom_inference.py
python3 python/batch_processing.py
python3 python/prompt_templates_demo.py
```

### All Examples
```bash
bash run_all_examples.sh
```

---

## Tips for Success

1. **Update Model IDs**: Change "llama" to match your downloaded models
2. **Check Model List**: Run `lmstrix list` to see available models
3. **Start Small**: Begin with `basic_workflow.sh` or `basic_usage.py`
4. **Test First**: Run `lmstrix test` to find optimal context for your models
5. **Use Verbose Mode**: Add `--verbose` for detailed output
6. **Monitor Memory**: Larger contexts use more GPU/RAM

---

## Troubleshooting

If examples fail:
1. Ensure LM Studio is running
2. Check you have models downloaded
3. Update model IDs in scripts
4. Verify LMStrix installation: `lmstrix --version`
5. Check available models: `lmstrix list`

For more help, see the main [LMStrix documentation](https://github.com/AdamAdli/lmstrix).