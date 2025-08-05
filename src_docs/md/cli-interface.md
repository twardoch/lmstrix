---
# this_file: src_docs/md/cli-interface.md
title: CLI Interface Reference
description: Complete command-line reference with examples, options, and advanced usage patterns
---

# CLI Interface Reference

The LMStrix CLI provides a powerful interface for all model management and inference operations. This comprehensive guide covers every command, option, and usage pattern.

## 🎯 Command Overview

LMStrix provides four main commands:

- **`scan`** - Discover and catalog models from LM Studio
- **`list`** - Display model registry with filtering and sorting
- **`test`** - Optimize context limits using binary search
- **`infer`** - Generate text with advanced options

## 📋 Global Options

These options work with all commands:

```bash
lmstrix [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Flags

```bash
--help, -h              # Show help message
--version               # Show LMStrix version
--config PATH           # Use custom config file
--profile NAME          # Use configuration profile
--debug                 # Enable debug logging
--quiet, -q             # Suppress non-essential output
--no-color              # Disable colored output
--no-emoji              # Disable emoji in output
--timeout SECONDS       # Override default timeout
```

### Examples

```bash
# Show version
lmstrix --version

# Use custom config
lmstrix --config ~/.lmstrix/dev.json scan

# Debug mode with no colors
lmstrix --debug --no-color test model-name

# Quiet operation
lmstrix -q list
```

## 🔍 `scan` Command

Discover and catalog available models from LM Studio.

### Syntax

```bash
lmstrix scan [OPTIONS]
```

### Options

```bash
--verbose, -v           # Detailed output with model information
--refresh, -r           # Force refresh, ignore cached results
--timeout SECONDS       # Override scan timeout (default: 30)
--server URL            # Override LM Studio server URL
--no-update             # Don't update registry, just show results
```

### Examples

```bash
# Basic scan
lmstrix scan

# Verbose scan with detailed model info
lmstrix scan --verbose

# Force refresh from LM Studio
lmstrix scan --refresh

# Scan with custom timeout
lmstrix scan --timeout 60

# Scan without updating registry
lmstrix scan --no-update --verbose

# Scan remote LM Studio instance
lmstrix scan --server http://192.168.1.100:1234
```

### Sample Output

```bash
$ lmstrix scan --verbose
🔍 Scanning LM Studio server at http://localhost:1234...
✅ Server connection successful
📡 Discovering available models...

Found 4 models:
┌─────────────────────────────────┬──────────┬─────────────┬───────────┐
│ Model                           │ Size     │ Parameters  │ Type      │
├─────────────────────────────────┼──────────┼─────────────┼───────────┤
│ llama-3.2-3b-instruct          │ 3.2 GB   │ 3.2B        │ Chat      │
│ mistral-7b-instruct-v0.2       │ 7.1 GB   │ 7.1B        │ Chat      │
│ codellama-13b-python           │ 13.0 GB  │ 13.0B       │ Code      │
│ phi-3-mini-4k-instruct         │ 2.4 GB   │ 3.8B        │ Chat      │
└─────────────────────────────────┴──────────┴─────────────┴───────────┘

📋 Updated model registry with 4 models
⏱️  Scan completed in 2.34 seconds
```

## 📊 `list` Command

Display and manage your model registry with advanced filtering and sorting.

### Syntax

```bash
lmstrix list [OPTIONS] [FILTER]
```

### Options

```bash
--sort FIELD            # Sort by: name, size, ctx, status, date
--reverse, -r           # Reverse sort order
--show FORMAT           # Output format: table, json, csv, summary
--filter CONDITION      # Filter models (see filtering section)
--columns COLS          # Select specific columns
--no-header             # Hide table header
--max-width WIDTH       # Limit table width
```

### Sorting Options

```bash
--sort name             # Sort by model name (default)
--sort size             # Sort by model size
--sort ctx              # Sort by tested context limit
--sort status           # Sort by test status
--sort date             # Sort by last test date
```

### Output Formats

```bash
--show table            # Formatted table (default)
--show json             # JSON format
--show csv              # CSV format
--show summary          # Brief summary
--show yaml             # YAML format
```

### Examples

```bash
# Basic list
lmstrix list

# Sort by context limit (highest first)
lmstrix list --sort ctx --reverse

# Show only tested models
lmstrix list --filter "status:tested"

# JSON output for automation
lmstrix list --show json

# Custom columns
lmstrix list --columns name,size,ctx

# Filter by size
lmstrix list --filter "size:>5GB"

# Compact summary
lmstrix list --show summary --no-header
```

### Filtering

Advanced filtering syntax:

```bash
# Status filters
--filter "status:tested"           # Only tested models
--filter "status:untested"         # Only untested models
--filter "status:failed"           # Only failed tests

# Size filters  
--filter "size:>5GB"               # Larger than 5GB
--filter "size:<1GB"               # Smaller than 1GB
--filter "size:3GB-10GB"           # Between 3GB and 10GB

# Context filters
--filter "ctx:>30000"              # Context > 30k tokens
--filter "ctx:16384-65536"         # Context range

# Name filters
--filter "name:llama"              # Name contains "llama"
--filter "name:*instruct*"         # Name contains "instruct"

# Date filters
--filter "date:today"              # Tested today
--filter "date:>2024-01-01"        # Tested after date

# Combined filters (AND logic)
--filter "status:tested,size:>5GB" # Tested AND larger than 5GB
```

### Sample Output

```bash
$ lmstrix list --sort ctx --reverse
┌─────────────────────────────────┬──────────┬───────────┬─────────────┬─────────────┐
│ Model                           │ Size     │ Context   │ Status      │ Last Tested │
├─────────────────────────────────┼──────────┼───────────┼─────────────┼─────────────┤
│ codellama-13b-python           │ 13.0 GB  │ 65,536    │ ✅ Tested   │ 2024-01-15  │
│ mistral-7b-instruct-v0.2       │ 7.1 GB   │ 32,768    │ ✅ Tested   │ 2024-01-14  │
│ llama-3.2-3b-instruct          │ 3.2 GB   │ 16,384    │ ✅ Tested   │ 2024-01-13  │
│ phi-3-mini-4k-instruct         │ 2.4 GB   │ Unknown   │ ⏳ Untested │ Never       │
└─────────────────────────────────┴──────────┴───────────┴─────────────┴─────────────┘

📊 Summary: 4 models total, 3 tested, 1 untested
```

## ⚡ `test` Command

Optimize context limits using LMStrix's signature binary search algorithm.

### Syntax

```bash
lmstrix test [MODEL_NAME] [OPTIONS]
```

### Options

```bash
--all, -a               # Test all untested models
--threshold TOKENS      # Maximum context to test (safety limit)
--ctx TOKENS            # Test specific context size
--prompt TEXT           # Custom test prompt
--file-prompt PATH      # Load prompt from file
--reset                 # Reset existing results and re-test
--timeout SECONDS       # Test timeout per attempt
--verbose, -v           # Show detailed progress
--dry-run               # Show what would be tested without running
--continue, -c          # Continue interrupted tests
--parallel NUM          # Run multiple tests in parallel (advanced)
```

### Testing Modes

```bash
# Single model test
lmstrix test llama-3.2-3b-instruct

# Test with safety threshold
lmstrix test llama-3.2-3b-instruct --threshold 32768

# Test specific context size
lmstrix test llama-3.2-3b-instruct --ctx 16384

# Test all untested models
lmstrix test --all

# Reset and re-test
lmstrix test llama-3.2-3b-instruct --reset
```

### Custom Prompts

```bash
# Simple custom prompt
lmstrix test model-name --prompt "What is 2+2?"

# Load prompt from file
lmstrix test model-name --file-prompt ./test-prompt.txt

# Template-based prompt
lmstrix test model-name --file-prompt prompts.toml --template simple_test
```

### Safety and Performance

```bash
# Conservative testing (recommended for first run)
lmstrix test --all --threshold 16384

# Aggressive testing (powerful hardware)
lmstrix test --all --threshold 131072

# Extended timeout for large models
lmstrix test large-model --timeout 600

# Dry run to see test plan
lmstrix test --all --dry-run
```

### Examples

```bash
# Basic context test
lmstrix test llama-3.2-3b-instruct

# Safe batch testing
lmstrix test --all --threshold 32768 --verbose

# Test specific context limit
lmstrix test mistral-7b --ctx 65536

# Custom prompt testing
lmstrix test codellama-13b --prompt "def fibonacci(n):"

# Reset failed test and retry
lmstrix test failed-model --reset --threshold 16384

# Continue interrupted test session
lmstrix test --continue --verbose
```

### Progress Output

```bash
# Compact progress (default)
Model                           Context      Status
llama-3.2-3b-instruct          8,192        Testing...
llama-3.2-3b-instruct          16,384       Testing...
llama-3.2-3b-instruct          24,576       ✅ Success

# Verbose progress
════════════════════════════════════════════════════════════
🧪 CONTEXT TEST: llama-3.2-3b-instruct
🎯 Target: Find maximum context limit
🛡️ Threshold: 32,768 tokens
🔄 Algorithm: Binary search
════════════════════════════════════════════════════════════
📊 Testing 8,192 tokens... ✅ Success (2.1s)
📊 Testing 16,384 tokens... ✅ Success (4.3s)  
📊 Testing 24,576 tokens... ✅ Success (6.7s)
📊 Testing 32,768 tokens... ❌ Failed (timeout)
📊 Testing 28,672 tokens... ✅ Success (5.9s)
📊 Testing 30,720 tokens... ❌ Failed (memory)
📊 Testing 29,696 tokens... ✅ Success (6.1s)
════════════════════════════════════════════════════════════
🎉 OPTIMAL CONTEXT: 29,696 tokens
⏱️ Total test time: 25.1 seconds
💾 Results saved to registry
════════════════════════════════════════════════════════════
```

## 🧠 `infer` Command

Generate text with advanced control over output, formatting, and model parameters.

### Syntax

```bash
lmstrix infer PROMPT [OPTIONS]
lmstrix infer TEMPLATE_NAME --file-prompt FILE [OPTIONS]
```

### Options

```bash
# Model selection
-m, --model MODEL       # Specify model to use
--auto-model            # Auto-select best available model

# Output control
--out-ctx TOKENS        # Output length: number, percentage, or "auto"
--max-tokens TOKENS     # Alias for --out-ctx
--temperature FLOAT     # Creativity level (0.0-2.0, default: 0.7)
--top-p FLOAT           # Nucleus sampling (0.0-1.0)
--top-k INT             # Top-k sampling

# Input methods
--text TEXT             # Direct text input
--text-file PATH        # Load text from file
--file-prompt PATH      # Load prompt template from file
--stdin                 # Read from standard input

# Output formatting
--verbose, -v           # Show detailed statistics
--quiet, -q             # Minimal output (response only)
--format FORMAT         # Output format: text, json, yaml
--stream                # Stream response in real-time
--no-wrap               # Don't wrap long lines

# Advanced options
--context-file PATH     # Load additional context
--system-prompt TEXT    # Set system prompt
--continue-conv         # Continue previous conversation
--save-response PATH    # Save response to file
```

### Output Length Control

```bash
# Exact token count
lmstrix infer "Explain AI" -m model --out-ctx 100

# Percentage of model's context
lmstrix infer "Write story" -m model --out-ctx "25%"

# Auto-determine based on prompt
lmstrix infer "Quick question" -m model --out-ctx auto

# Maximum available tokens
lmstrix infer "Long analysis" -m model --out-ctx max
```

### Temperature and Sampling

```bash
# Very focused/deterministic (good for facts)
lmstrix infer "What is the capital of France?" -m model --temperature 0.1

# Balanced (default)
lmstrix infer "Explain quantum physics" -m model --temperature 0.7

# Very creative (good for stories)
lmstrix infer "Write a creative story" -m model --temperature 1.2

# Combined sampling control
lmstrix infer "Creative writing" -m model --temperature 0.9 --top-p 0.9 --top-k 50
```

### Input Methods

```bash
# Direct prompt
lmstrix infer "What is machine learning?" -m model

# From file
lmstrix infer --text-file document.txt -m model

# From stdin
echo "Analyze this text" | lmstrix infer -m model --stdin

# Template-based
lmstrix infer summary --file-prompt templates.toml --text "Content here"
```

### Examples

```bash
# Basic inference
lmstrix infer "Explain quantum computing" -m llama-3.2-3b-instruct

# Verbose statistics
lmstrix infer "What is AI?" -m mistral-7b --verbose

# Creative writing with high temperature
lmstrix infer "Write a sci-fi story" -m codellama-13b --temperature 1.1 --out-ctx "30%"

# Factual query with low temperature
lmstrix infer "List Python data types" -m model --temperature 0.2 --out-ctx 150

# Summarization task
lmstrix infer "Summarize this: $(cat article.txt)" -m model --out-ctx "10%"

# Template with file input
lmstrix infer analysis --file-prompt prompts.toml --text-file data.txt

# JSON output for automation
lmstrix infer "Quick answer" -m model --format json --quiet

# Stream long response
lmstrix infer "Write detailed explanation" -m model --stream --out-ctx 500
```

### Template-Based Inference

Create `prompts.toml`:

```toml
[summary]
prompt = "Create a concise summary of: {{text}}"

[analysis]
prompt = """
Analyze the following text for:
- Key themes
- Important facts  
- Conclusions

Text: {{text}}
"""

[creative]
prompt = "Write a creative story about: {{theme}}"
```

Use templates:

```bash
# Summarization
lmstrix infer summary --file-prompt prompts.toml --text "Your content here"

# Analysis with file input
lmstrix infer analysis --file-prompt prompts.toml --text-file document.txt

# Creative writing
lmstrix infer creative --file-prompt prompts.toml --text "space exploration"
```

### Conversation Mode

```bash
# Start conversation
lmstrix infer "Hello, I'm working on a Python project" -m model --continue-conv

# Continue conversation (remembers context)
lmstrix infer "How do I handle exceptions?" -m model --continue-conv

# End conversation
lmstrix infer "Thank you for the help!" -m model --continue-conv --save-response chat.txt
```

## 🔧 Advanced Usage Patterns

### Batch Processing

```bash
# Process multiple prompts
for prompt in "Explain AI" "Define ML" "What is DL"; do
    lmstrix infer "$prompt" -m model --quiet
    echo "---"
done

# Process files in directory
for file in *.txt; do
    lmstrix infer summary --file-prompt templates.toml --text-file "$file" > "${file%.txt}_summary.txt"
done
```

### Automation and Scripting

```bash
#!/bin/bash
# Automated model testing script

# Test all models with conservative settings
lmstrix test --all --threshold 16384 --quiet

# Generate test report
lmstrix list --show json > model_report.json

# Run inference benchmarks
for model in $(lmstrix list --show json | jq -r '.[] | select(.status=="tested") | .name'); do
    echo "Testing model: $model"
    time lmstrix infer "Explain quantum computing" -m "$model" --out-ctx 100 --quiet
done
```

### Pipeline Integration

```bash
# Use in data processing pipelines
cat data.json | jq -r '.content' | lmstrix infer -m model --stdin --format json | jq '.response'

# Integration with other tools
lmstrix infer "Analyze: $(curl -s https://api.example.com/data)" -m model --out-ctx "20%"

# Monitoring and logging
lmstrix infer "Status check" -m model --format json --save-response "status_$(date +%Y%m%d_%H%M%S).json"
```

### Configuration Profiles

```bash
# Development profile
lmstrix --profile dev test --all

# Production profile  
lmstrix --profile prod infer "Production query" -m model

# Custom config
lmstrix --config ./project.json infer "Project query" -m model
```

## 🚀 Performance Tips

### Optimization Strategies

```bash
# Keep models loaded for repeated use
lmstrix infer "Query 1" -m model
lmstrix infer "Query 2" -m model  # Reuses loaded model

# Use appropriate context limits
lmstrix infer "Short answer" -m model --out-ctx 50  # Fast
lmstrix infer "Detailed analysis" -m model --out-ctx "15%"  # Slower but comprehensive

# Parallel testing (advanced)
lmstrix test --all --parallel 2 --threshold 32768
```

### Monitoring and Debugging

```bash
# Debug mode for troubleshooting
lmstrix --debug infer "Test prompt" -m model

# Performance monitoring
lmstrix infer "Benchmark prompt" -m model --verbose

# Resource usage tracking
time lmstrix test model-name --verbose
```

## 🆘 Troubleshooting

### Common Issues and Solutions

```bash
# Model not found
lmstrix scan --refresh  # Refresh model registry

# Connection issues
lmstrix --debug scan    # Debug connection

# Test failures
lmstrix test model --reset --threshold 8192  # Lower threshold

# Memory issues
export LMSTRIX_SAFETY_THRESHOLD=16384
lmstrix test --all

# Timeout issues
lmstrix infer "prompt" -m model --timeout 600
```

## 🚀 Next Steps

Master the CLI, then explore:

- **[Python API](python-api.md)** - Programmatic usage
- **[Context Testing](context-testing.md)** - Deep dive into optimization
- **[Prompt Templating](prompt-templating.md)** - Advanced prompt engineering
- **[Performance & Optimization](performance.md)** - Squeeze out maximum performance

---

*CLI mastery unlocked! Command your models with precision! 🎯*