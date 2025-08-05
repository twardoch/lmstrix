---
# this_file: src_docs/md/context-testing.md
title: Context Testing Deep Dive
description: Master LMStrix's Adaptive Context Optimization - algorithms, configuration, and best practices
---

# Context Testing Deep Dive

LMStrix's signature feature is **Adaptive Context Optimization** - a sophisticated binary search algorithm that automatically discovers the true operational context limits of language models. This chapter explores how it works, how to configure it, and best practices for optimization.

## 🧠 Understanding Context Limits

### What Are Context Limits?

Context limits determine how much text (measured in tokens) a language model can process in a single inference. This includes:

- **Input prompt tokens** - Your question or instruction
- **Output generation tokens** - The model's response
- **System/conversation tokens** - Chat history and system prompts

### Why Context Optimization Matters

1. **Maximize Utilization** - Use full model capability
2. **Prevent Failures** - Avoid context overflow errors
3. **Optimize Performance** - Find the sweet spot for speed vs capacity
4. **Resource Management** - Balance memory usage and throughput

### The Context Discovery Problem

Models often report theoretical limits that differ from practical operational limits:

```bash
# Theoretical limit vs. practical limit
Model: llama-3.2-3b-instruct
Advertised context: 128,000 tokens
Actual working limit: 29,696 tokens (discovered by LMStrix)
```

## ⚡ Binary Search Algorithm

### How It Works

LMStrix uses a sophisticated binary search to efficiently find the maximum working context:

```
Initial range: [512, threshold]
│
├─ Test midpoint: 32,768
│  ├─ Success → Search upper half: [32,768, 65,536]
│  └─ Failure → Search lower half: [512, 32,768]
│
├─ Test midpoint: 49,152
│  ├─ Success → Search upper half: [49,152, 65,536]
│  └─ Failure → Search lower half: [32,768, 49,152]
│
└─ Continue until optimal found: 47,104 tokens
```

### Algorithm Parameters

```python
{
    "min_context": 512,           # Minimum test size
    "max_context": 65536,         # Safety threshold
    "max_iterations": 20,         # Maximum search steps
    "convergence_threshold": 256, # Stop when range < threshold
    "safety_margin": 1024,        # Buffer below failure point
    "timeout_per_test": 300       # Seconds per test attempt
}
```

### Convergence Criteria

The algorithm stops when:

1. **Range convergence** - Search range becomes smaller than threshold
2. **Maximum iterations** - Safety limit reached
3. **Consistent failure** - Multiple consecutive failures at different sizes
4. **Timeout** - Test takes too long to complete

## 🛠️ Test Configuration

### Safety Thresholds

Configure maximum test limits to protect your system:

```bash
# Conservative (recommended for first run)
lmstrix test --all --threshold 16384

# Moderate (good for most systems)
lmstrix test --all --threshold 32768

# Aggressive (high-end systems only)
lmstrix test --all --threshold 131072

# Custom threshold per model
lmstrix test large-model --threshold 65536
lmstrix test small-model --threshold 32768
```

### Test Prompts

#### Default Test Prompt

LMStrix uses a carefully crafted default prompt that:

- Scales linearly with context size
- Maintains consistent complexity
- Exercises model capabilities realistically

```python
def generate_test_prompt(target_tokens: int) -> str:
    """Generate a prompt that will consume approximately target_tokens."""
    base_instruction = "Analyze and respond to the following repeated text: "
    
    # Calculate repetition needed for target size
    repeat_text = "The quick brown fox jumps over the lazy dog. "
    tokens_per_repeat = estimate_tokens(repeat_text)
    repetitions = (target_tokens - estimate_tokens(base_instruction)) // tokens_per_repeat
    
    return base_instruction + (repeat_text * repetitions)
```

#### Custom Test Prompts

Use domain-specific prompts for more accurate testing:

```bash
# Simple custom prompt
lmstrix test model-name --prompt "What is 2+2?"

# Load prompt from file
lmstrix test model-name --file-prompt test-prompt.txt

# Use template with variable scaling
lmstrix test model-name --file-prompt prompts.toml --template scale_test
```

**Example scaling template** (`prompts.toml`):

```toml
[scale_test]
prompt = """
Analyze the following data and provide insights:
{{repeated_data}}

Please provide:
1. Summary statistics
2. Key patterns
3. Recommendations
"""

[scale_data]
data = "Sample data point with relevant information. "
repeats = "{{context_size // 50}}"  # Scale with context size
```

### Advanced Test Options

```bash
# Test specific context size (no binary search)
lmstrix test model-name --ctx 16384

# Extended timeout for large models
lmstrix test model-name --timeout 600

# Reset existing results and re-test
lmstrix test model-name --reset

# Verbose output with detailed progress
lmstrix test model-name --verbose

# Dry run to see test plan
lmstrix test model-name --dry-run
```

## 📊 Test Results and Interpretation

### Result Data Structure

Each test produces comprehensive results:

```python
{
    "model_id": "llama-3.2-3b-instruct",
    "test_timestamp": "2024-01-15T10:30:00Z",
    "optimal_context": 29696,
    "test_successful": True,
    "total_iterations": 8,
    "total_test_time": 156.7,
    "safety_threshold": 32768,
    "test_points": [
        {"context": 16384, "success": True, "time": 12.3},
        {"context": 24576, "success": True, "time": 18.7},
        {"context": 28672, "success": True, "time": 24.1},
        {"context": 30720, "success": False, "error": "context_overflow"},
        {"context": 29696, "success": True, "time": 22.8}
    ],
    "failure_analysis": {
        "first_failure_at": 30720,
        "failure_type": "context_overflow",
        "consistent_failure_above": 30000
    },
    "performance_metrics": {
        "avg_tokens_per_second": 42.3,
        "peak_memory_usage_mb": 3847,
        "model_load_time": 8.2
    }
}
```

### Success/Failure Patterns

#### Successful Test

```
Model                           Context      Status
llama-3.2-3b-instruct          8,192        ✅ Success
llama-3.2-3b-instruct          16,384       ✅ Success  
llama-3.2-3b-instruct          24,576       ✅ Success
llama-3.2-3b-instruct          28,672       ✅ Success
llama-3.2-3b-instruct          30,720       ❌ Failed
llama-3.2-3b-instruct          29,696       ✅ Success
                                
🎉 OPTIMAL CONTEXT: 29,696 tokens
```

#### Common Failure Patterns

```bash
# Memory exhaustion
Context: 65536 → ❌ Failed (out_of_memory)

# Timeout (model too slow)
Context: 32768 → ❌ Failed (timeout)

# Model capacity limit
Context: 16384 → ❌ Failed (context_overflow)

# API/Connection issues
Context: 8192 → ❌ Failed (connection_error)
```

### Result Interpretation

#### Optimal Context Found

```python
if result["test_successful"] and result["optimal_context"] > 0:
    print(f"✅ Found optimal context: {result['optimal_context']:,} tokens")
    print(f"📊 Test efficiency: {result['total_iterations']} iterations")
    print(f"⏱️ Test duration: {result['total_test_time']:.1f} seconds")
```

#### Test Failed

```python
if not result["test_successful"]:
    print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
    
    # Analyze failure reasons
    if "timeout" in result.get("error", "").lower():
        print("💡 Try: Increase timeout or reduce threshold")
    elif "memory" in result.get("error", "").lower():
        print("💡 Try: Lower threshold or free up system memory")
    elif "connection" in result.get("error", "").lower():
        print("💡 Try: Check LM Studio is running and accessible")
```

## ⚙️ Advanced Configuration

### Fine-Tuning Algorithm Parameters

#### Binary Search Precision

```json
{
  "context_testing": {
    "binary_search": {
      "convergence_threshold": 256,     # Stop when range < 256 tokens
      "max_iterations": 25,             # Allow more iterations for precision
      "safety_margin": 512,             # Larger buffer for safety
      "overshoot_protection": true,     # Prevent testing beyond failures
      "adaptive_step_size": true        # Adjust step size based on failures
    }
  }
}
```

#### Performance Optimization

```json
{
  "context_testing": {
    "performance": {
      "parallel_testing": false,        # Test models sequentially
      "model_preload": true,            # Keep models loaded between tests
      "cache_failures": true,           # Remember failure points
      "early_termination": true,        # Stop on consistent failures
      "memory_monitoring": true         # Track memory usage
    }
  }
}
```

#### Failure Handling

```json
{
  "context_testing": {
    "failure_handling": {
      "max_consecutive_failures": 3,   # Stop after 3 failures
      "failure_backoff_factor": 0.7,   # Reduce next test by 30%
      "retry_failed_tests": true,      # Retry on transient errors
      "retry_delay_seconds": 5,        # Wait between retries
      "auto_adjust_threshold": true    # Lower threshold on failures
    }
  }
}
```

### Environment-Specific Tuning

#### High-Memory Systems

```bash
# Configuration for systems with 32GB+ RAM
export LMSTRIX_SAFETY_THRESHOLD=262144
export LMSTRIX_MAX_TEST_ITERATIONS=30
export LMSTRIX_MEMORY_MONITORING=true

lmstrix test --all --threshold 262144 --timeout 900
```

#### Low-Memory Systems

```bash
# Configuration for systems with 8GB RAM
export LMSTRIX_SAFETY_THRESHOLD=8192
export LMSTRIX_MAX_TEST_ITERATIONS=15
export LMSTRIX_AGGRESSIVE_GC=true

lmstrix test --all --threshold 8192 --timeout 300
```

#### Production Environments

```bash
# Conservative settings for production
export LMSTRIX_SAFETY_THRESHOLD=32768
export LMSTRIX_TEST_TIMEOUT=600
export LMSTRIX_ENABLE_MONITORING=true

lmstrix test --all --threshold 32768 --verbose
```

## 🔬 Advanced Testing Strategies

### Comprehensive Model Analysis

#### Full Context Mapping

Test multiple context ranges to understand model behavior:

```bash
# Test at multiple thresholds to map behavior
lmstrix test model-name --ctx 8192
lmstrix test model-name --ctx 16384
lmstrix test model-name --ctx 32768
lmstrix test model-name --ctx 65536

# Compare results
lmstrix list --filter "name:model-name" --show json
```

#### Stress Testing

Push models to their absolute limits:

```bash
# Gradual stress testing
for threshold in 16384 32768 65536 131072; do
    echo "Testing threshold: $threshold"
    lmstrix test model-name --threshold $threshold --reset
    sleep 10  # Cool-down period
done
```

#### Performance Profiling

Measure performance characteristics at different context sizes:

```python
from lmstrix.core.context_tester import ContextTester
import matplotlib.pyplot as plt

tester = ContextTester(verbose=True)

# Test multiple context sizes
contexts = [1024, 2048, 4096, 8192, 16384, 32768]
performance_data = []

for ctx in contexts:
    result = tester.test_specific_context("model-name", ctx)
    if result["success"]:
        performance_data.append({
            "context": ctx,
            "time": result["inference_time"],
            "tokens_per_second": result["tokens_per_second"]
        })

# Plot performance curve
contexts = [d["context"] for d in performance_data]
times = [d["time"] for d in performance_data]
speeds = [d["tokens_per_second"] for d in performance_data]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(contexts, times, 'b-o')
ax1.set_xlabel('Context Size (tokens)')
ax1.set_ylabel('Inference Time (seconds)')
ax1.set_title('Context Size vs Inference Time')

ax2.plot(contexts, speeds, 'r-o')
ax2.set_xlabel('Context Size (tokens)')
ax2.set_ylabel('Tokens per Second')
ax2.set_title('Context Size vs Generation Speed')

plt.tight_layout()
plt.show()
```

### Batch Testing Workflows

#### Model Fleet Testing

Test all models systematically:

```bash
#!/bin/bash
# comprehensive_test.sh

# Configuration
THRESHOLD=32768
LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"

echo "Starting comprehensive model testing..." | tee $LOG_FILE

# Get all untested models
MODELS=$(lmstrix list --filter "status:untested" --show json | jq -r '.[].name')

for model in $MODELS; do
    echo "Testing model: $model" | tee -a $LOG_FILE
    
    # Test with retry logic
    for attempt in 1 2 3; do
        if lmstrix test "$model" --threshold $THRESHOLD --timeout 600; then
            echo "✅ $model test successful on attempt $attempt" | tee -a $LOG_FILE
            break
        else
            echo "❌ $model test failed on attempt $attempt" | tee -a $LOG_FILE
            if [ $attempt -eq 3 ]; then
                echo "🚫 $model failed all attempts" | tee -a $LOG_FILE
            fi
            sleep 30  # Cool-down between attempts
        fi
    done
    
    # Generate intermediate report
    lmstrix list --show summary | tee -a $LOG_FILE
    echo "---" | tee -a $LOG_FILE
done

echo "Testing complete. Final report:" | tee -a $LOG_FILE
lmstrix list --sort ctx --reverse | tee -a $LOG_FILE
```

#### Continuous Integration Testing

Automate testing in CI/CD pipelines:

```yaml
# .github/workflows/model-testing.yml
name: Model Context Testing

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  test-models:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install LMStrix
        run: pip install lmstrix
      
      - name: Start LM Studio (if available)
        run: |
          # Your LM Studio setup commands
          docker run -d --name lmstudio lmstudio/server:latest
      
      - name: Test Models
        run: |
          lmstrix scan
          lmstrix test --all --threshold 16384 --timeout 300
      
      - name: Generate Report
        run: |
          lmstrix list --show json > model-test-results.json
          lmstrix list --show summary > model-summary.txt
      
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: model-test-results
          path: |
            model-test-results.json
            model-summary.txt
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Test Timeouts

**Problem:** Tests timeout before completion

**Solutions:**
```bash
# Increase timeout
lmstrix test model-name --timeout 900

# Lower threshold
lmstrix test model-name --threshold 16384

# Use simpler prompt
lmstrix test model-name --prompt "Hello world"
```

#### Memory Exhaustion

**Problem:** System runs out of memory during testing

**Solutions:**
```bash
# Lower safety threshold
export LMSTRIX_SAFETY_THRESHOLD=16384

# Enable memory monitoring
export LMSTRIX_MEMORY_MONITORING=true

# Test models individually
lmstrix test model-name --threshold 8192
```

#### Inconsistent Results

**Problem:** Different results across test runs

**Solutions:**
```bash
# Reset and re-test
lmstrix test model-name --reset

# Use deterministic prompt
lmstrix test model-name --prompt "Count to 10"

# Increase convergence threshold
export LMSTRIX_CONVERGENCE_THRESHOLD=512
```

#### Connection Failures

**Problem:** Cannot connect to LM Studio

**Solutions:**
```bash
# Check LM Studio status
curl http://localhost:1234/v1/models

# Test with different URL
lmstrix test model-name --server http://localhost:1234

# Increase connection timeout
export LMSTRIX_CONNECT_TIMEOUT=60
```

### Debugging Test Failures

#### Enable Debug Logging

```bash
# Full debug output
lmstrix --debug test model-name --verbose

# Debug specific components
export LMSTRIX_LOG_LEVEL=DEBUG
export LMSTRIX_DEBUG_COMPONENTS="context_tester,api_client"
```

#### Analyze Test Points

```python
from lmstrix.loaders.model_loader import load_model_registry

registry = load_model_registry()
model = registry.get_model("problematic-model")

# Examine test history
test_points = model.get("test_points", [])
for point in test_points:
    print(f"Context: {point['context']:,} - "
          f"Success: {point['success']} - "
          f"Time: {point.get('time', 'N/A')}s")
    if not point['success']:
        print(f"  Error: {point.get('error', 'Unknown')}")
```

#### Manual Validation

```bash
# Test specific context size manually
lmstrix infer "Test prompt" -m model-name --out-ctx 16384

# Compare with direct LM Studio API call
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model-name",
    "messages": [{"role": "user", "content": "Test prompt"}],
    "max_tokens": 16384
  }'
```

## 🎯 Best Practices

### Testing Strategy

1. **Start Conservative** - Begin with low thresholds (16384)
2. **Test Systematically** - Test all models before production use
3. **Monitor Resources** - Watch memory and CPU usage
4. **Document Results** - Keep records of optimal contexts
5. **Regular Re-testing** - Contexts may change with model updates

### Performance Optimization

1. **Batch Testing** - Test multiple models in sequence
2. **Cache Results** - Avoid re-testing unchanged models
3. **Use Appropriate Hardware** - More RAM = higher thresholds
4. **Cool-down Periods** - Allow system recovery between tests
5. **Monitor Trends** - Track performance over time

### Production Deployment

1. **Conservative Limits** - Use 80% of discovered limit in production
2. **Fallback Strategies** - Have smaller context alternatives
3. **Monitoring** - Track context usage and failures
4. **Regular Updates** - Re-test when models or hardware change
5. **Documentation** - Document optimal contexts for each use case

## 🚀 Next Steps

Master context testing, then explore:

- **[Model Management](model-management.md)** - Advanced registry operations
- **[Performance & Optimization](performance.md)** - Production optimization
- **[Prompt Templating](prompt-templating.md)** - Advanced prompt engineering
- **[CLI Interface](cli-interface.md)** - Command-line mastery

---

*Context optimization mastered! Unlock your models' full potential! 🎯*