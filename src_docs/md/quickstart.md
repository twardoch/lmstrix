---
# this_file: src_docs/md/quickstart.md
title: Quick Start Guide
description: Get up and running with LMStrix in minutes - essential commands and workflows
---

# Quick Start Guide

Get up and running with LMStrix in just a few minutes! This guide walks you through the essential workflows and commands you'll use most frequently.

## 🏁 First Steps

### 1. Verify Installation

```bash
# Check that LMStrix is installed
lmstrix --version

# Get help on available commands
lmstrix --help
```

### 2. Check LM Studio Connection

```bash
# Test connection to LM Studio
lmstrix scan
```

**Expected output:**
```
🔍 Scanning for models...
✅ Found 3 models in LM Studio
📋 Updated model registry
```

!!! tip "LM Studio Not Running?"
    If you get a connection error, make sure LM Studio is running and the local server is enabled. The default URL is `http://localhost:1234`.

## 📋 Essential Workflows

### Workflow 1: Discover Your Models

```bash
# Scan for available models
lmstrix scan --verbose

# List all discovered models
lmstrix list
```

**Sample output:**
```
Model                           Size    Context    Status
llama-3.2-3b-instruct          3.2B    Unknown    Not tested
mistral-7b-instruct            7.1B    Unknown    Not tested
codellama-13b-python           13.0B   Unknown    Not tested
```

### Workflow 2: Test Context Limits

```bash
# Test a specific model's context limit
lmstrix test llama-3.2-3b-instruct

# Test all models with safety threshold
lmstrix test --all --threshold 32768
```

**Live progress display:**
```
Model                           Context      Status
llama-3.2-3b-instruct          16,384       Testing...
→
Model                           Context      Status  
llama-3.2-3b-instruct          32,768       ✓ Success
```

### Workflow 3: Run Inference

```bash
# Simple question with verbose output
lmstrix infer "What is the capital of Poland?" -m llama-3.2-3b-instruct --verbose

# Quick inference without verbose output
lmstrix infer "2+2=" -m llama-3.2-3b-instruct
```

## 🎯 Core Commands Deep Dive

### `scan` - Model Discovery

Discover and catalog models available in LM Studio:

```bash
# Basic scan
lmstrix scan

# Verbose scan with detailed output
lmstrix scan --verbose

# Force refresh (ignore cache)
lmstrix scan --refresh
```

!!! info "What does scan do?"
    - Connects to LM Studio's API
    - Discovers available models
    - Updates the local model registry
    - Preserves existing test results

### `list` - Model Registry

View and manage your model registry:

```bash
# List all models
lmstrix list

# Sort by different criteria
lmstrix list --sort size        # By model size
lmstrix list --sort ctx         # By tested context
lmstrix list --sort name        # By model name

# Different output formats
lmstrix list --show table       # Default table view
lmstrix list --show json        # JSON export
lmstrix list --show summary     # Brief summary
```

### `test` - Context Optimization

Find the optimal context window for your models:

```bash
# Test specific model
lmstrix test llama-3.2-3b-instruct

# Test with custom settings
lmstrix test llama-3.2-3b-instruct --threshold 65536

# Test all untested models
lmstrix test --all

# Reset and re-test a model
lmstrix test llama-3.2-3b-instruct --reset

# Test with custom prompt
lmstrix test llama-3.2-3b-instruct --prompt "Explain quantum computing"
```

!!! warning "Safety First"
    Always use the `--threshold` parameter to prevent system overload. Start with conservative values like 32768 tokens.

### `infer` - Text Generation

Generate text using your models:

```bash
# Basic inference
lmstrix infer "Your prompt here" -m model-name

# With verbose statistics
lmstrix infer "Explain AI" -m llama-3.2-3b-instruct --verbose

# Control output length (percentage of context)
lmstrix infer "Write a story" -m llama-3.2-3b-instruct --out_ctx "25%"

# Control output length (exact tokens)
lmstrix infer "Summarize this" -m llama-3.2-3b-instruct --out_ctx 100

# Adjust temperature for creativity
lmstrix infer "Be creative" -m llama-3.2-3b-instruct --temperature 0.9
```

## 📊 Understanding Verbose Output

When using `--verbose`, LMStrix provides detailed statistics:

```
════════════════════════════════════════════════════════════
🤖 MODEL: llama-3.2-3b-instruct
🔧 CONFIG: maxTokens=26214, temperature=0.7
📝 PROMPT (1 lines, 29 chars): What is the capital of Poland?
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

The capital of Poland is Warsaw (Polish: Warszawa)...
```

### Key Metrics Explained

- **Time to first token**: Latency before generation starts
- **Total inference time**: Complete generation duration
- **Tokens/second**: Generation speed
- **Stop reason**: Why generation ended (`eosFound`, `lengthLimit`, etc.)

## 🎨 Advanced Quick Examples

### Template-Based Prompts

Create reusable prompt templates:

```bash
# Create a prompt file
cat > my_prompts.toml << 'EOF'
[summary]
prompt = "Create a comprehensive summary of the following text: {{text}}"

[explain]
prompt = "Explain {{concept}} in simple terms for a beginner"
EOF

# Use template with text input
lmstrix infer summary --file_prompt my_prompts.toml --text "Your text here"

# Use template with variable substitution
lmstrix infer explain --file_prompt my_prompts.toml --text "quantum computing"

# Use template with file input
lmstrix infer summary --file_prompt my_prompts.toml --text_file document.txt
```

### Batch Processing

Process multiple inputs efficiently:

```bash
# Test multiple models
for model in llama-3.2-3b-instruct mistral-7b-instruct; do
    lmstrix test "$model" --threshold 32768
done

# Generate responses for multiple prompts
echo "What is AI?" | lmstrix infer - -m llama-3.2-3b-instruct
echo "Explain Python" | lmstrix infer - -m llama-3.2-3b-instruct
```

### Performance Monitoring

Track model performance over time:

```bash
# Generate inference with timing
time lmstrix infer "Complex question" -m llama-3.2-3b-instruct --verbose

# Test context limits with different thresholds
lmstrix test llama-3.2-3b-instruct --ctx 16384
lmstrix test llama-3.2-3b-instruct --ctx 32768
lmstrix test llama-3.2-3b-instruct --ctx 65536
```

## 🚀 Your First Complete Workflow

Here's a complete workflow from setup to inference:

```bash
# 1. Discover available models
lmstrix scan --verbose

# 2. List models to see what's available
lmstrix list

# 3. Test context limit for your preferred model
lmstrix test llama-3.2-3b-instruct --threshold 32768

# 4. Run your first inference with stats
lmstrix infer "Explain machine learning in simple terms" \
    -m llama-3.2-3b-instruct \
    --verbose \
    --temperature 0.7 \
    --out_ctx "20%"

# 5. Check your updated model registry
lmstrix list --sort ctx
```

## 🛠️ Troubleshooting Quick Fixes

### Model Not Found
```bash
# Refresh model discovery
lmstrix scan --refresh

# Check LM Studio has the model loaded
lmstrix list --show json | grep "your-model-name"
```

### Context Test Fails
```bash
# Try lower threshold
lmstrix test model-name --threshold 16384

# Use custom prompt (simpler)
lmstrix test model-name --prompt "Hello world"

# Reset and retry
lmstrix test model-name --reset
```

### Inference Timeout
```bash
# Reduce output tokens
lmstrix infer "prompt" -m model --out_ctx 50

# Increase timeout (if needed)
export LMSTRIX_TIMEOUT=600
lmstrix infer "prompt" -m model
```

## 🎯 Next Steps

Now that you're familiar with the basics:

1. **[Configuration](configuration.md)** - Customize LMStrix settings
2. **[CLI Interface](cli-interface.md)** - Master all command options
3. **[Context Testing](context-testing.md)** - Deep dive into optimization
4. **[Python API](python-api.md)** - Programmatic usage
5. **[Prompt Templating](prompt-templating.md)** - Advanced prompt engineering

## 💡 Pro Tips

!!! tip "Efficiency Tips"
    - Use `--verbose` only when you need detailed stats
    - Set reasonable `--threshold` values to avoid system overload
    - Test models once, then rely on cached context limits
    - Use templates for repeated prompt patterns
    - Monitor token usage to optimize costs and performance

!!! example "Common Patterns"
    ```bash
    # Quick model comparison
    for model in model1 model2 model3; do
        echo "Testing $model:"
        lmstrix infer "Explain AI" -m "$model" --out_ctx 100
        echo "---"
    done
    
    # Find best performing model
    lmstrix list --sort ctx --show table
    ```

---

*Ready to dive deeper? Choose your next chapter based on your needs! 🚀*