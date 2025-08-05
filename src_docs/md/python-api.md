---
# this_file: src_docs/md/python-api.md
title: Python API Reference
description: Comprehensive Python API documentation with code examples, class references, and integration patterns
---

# Python API Reference

The LMStrix Python API provides programmatic access to all functionality available in the CLI, with additional flexibility for integration into your Python applications, scripts, and workflows.

## 🚀 Quick Start

### Basic Usage

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
    print(f"Tokens: {result['tokens_used']}")
```

## 📚 Core Classes

### InferenceManager

The main interface for running inference operations.

```python
from lmstrix.core.inference_manager import InferenceManager

# Create manager with options
manager = InferenceManager(
    verbose=True,           # Enable detailed logging
    base_url="http://localhost:1234",  # LM Studio URL
    timeout=300,            # Request timeout
    max_retries=3           # Retry attempts
)
```

#### Methods

##### `infer()`

Run text generation inference.

```python
result = manager.infer(
    model_id: str,                    # Model identifier
    prompt: str,                      # Input prompt
    out_ctx: int | str = "auto",      # Output length
    temperature: float = 0.7,         # Creativity (0.0-2.0)
    top_p: float = 1.0,              # Nucleus sampling
    top_k: int = -1,                 # Top-k sampling
    max_tokens: int | None = None,    # Max output tokens
    system_prompt: str | None = None, # System prompt
    context_data: dict | None = None  # Additional context
) -> dict
```

**Return value:**
```python
{
    "succeeded": bool,           # Whether inference succeeded
    "response": str,             # Generated text
    "tokens_used": int,          # Total tokens consumed
    "prompt_tokens": int,        # Tokens in prompt
    "response_tokens": int,      # Tokens in response
    "inference_time": float,     # Generation time (seconds)
    "time_to_first_token": float,# Latency to first token
    "tokens_per_second": float,  # Generation speed
    "stop_reason": str,          # Why generation stopped
    "error": str | None,         # Error message if failed
    "model_info": dict           # Model metadata
}
```

##### `infer_with_template()`

Use prompt templates for inference.

```python
result = manager.infer_with_template(
    template_name: str,              # Template identifier
    model_id: str,                   # Model to use
    template_file: str,              # TOML template file
    variables: dict,                 # Template variables
    **kwargs                         # Additional infer() options
)
```

### ModelRegistry

Manage the model registry and metadata.

```python
from lmstrix.loaders.model_loader import load_model_registry

# Load registry
registry = load_model_registry()

# Alternative: create new registry
from lmstrix.core.models import ModelRegistry
registry = ModelRegistry()
```

#### Methods

##### Model Discovery

```python
# List all models
models = registry.list_models()

# Get specific model
model = registry.get_model("llama-3.2-3b-instruct")

# Check if model exists
exists = registry.has_model("model-name")

# Filter models
tested_models = registry.filter_models(status="tested")
large_models = registry.filter_models(size_range=(5000, 20000))  # 5GB-20GB
```

##### Model Information

```python
# Get model details
model_info = registry.get_model_info("llama-3.2-3b-instruct")
print(f"Size: {model_info['size_mb']} MB")
print(f"Context: {model_info['tested_context']}")
print(f"Status: {model_info['test_status']}")

# Get model statistics
stats = registry.get_statistics()
print(f"Total models: {stats['total']}")
print(f"Tested: {stats['tested']}")
print(f"Average context: {stats['avg_context']}")
```

##### Registry Management

```python
# Save registry
registry.save()

# Reload from disk
registry.reload()

# Add model manually
registry.add_model({
    "id": "custom-model",
    "name": "Custom Model",
    "size_mb": 3500,
    "parameters": "3.5B"
})

# Update model info
registry.update_model("model-id", {
    "tested_context": 32768,
    "test_status": "tested",
    "last_tested": "2024-01-15T10:30:00Z"
})

# Remove model
registry.remove_model("model-id")
```

### ContextTester

Binary search algorithm for finding optimal context limits.

```python
from lmstrix.core.context_tester import ContextTester

# Create tester
tester = ContextTester(
    base_url="http://localhost:1234",
    timeout=300,
    max_iterations=20,
    safety_threshold=65536
)
```

#### Methods

##### `test_model_context()`

Test context limit for a specific model.

```python
result = tester.test_model_context(
    model_id: str,                    # Model to test
    threshold: int = 65536,           # Maximum context to test
    prompt: str | None = None,        # Custom test prompt
    reset: bool = False,              # Reset existing results
    verbose: bool = False             # Detailed progress
) -> dict
```

**Return value:**
```python
{
    "model_id": str,               # Model identifier
    "optimal_context": int,        # Maximum working context
    "test_successful": bool,       # Whether test completed
    "iterations": int,             # Number of test iterations
    "total_time": float,           # Total test time
    "error": str | None,           # Error if test failed
    "test_points": list,           # All tested context sizes
    "final_working_size": int,     # Last confirmed working size
    "failure_point": int | None    # First size that failed
}
```

##### `test_multiple_models()`

Test multiple models in sequence or parallel.

```python
results = tester.test_multiple_models(
    model_ids: list[str],            # Models to test
    threshold: int = 65536,          # Safety threshold
    parallel: bool = False,          # Run in parallel
    max_workers: int = 2             # Parallel worker count
) -> list[dict]
```

### Scanner

Discover models available in LM Studio.

```python
from lmstrix.core.scanner import Scanner

# Create scanner
scanner = Scanner(
    base_url="http://localhost:1234",
    timeout=30
)

# Scan for models
models = scanner.scan_models(refresh=True)

# Check server health
health = scanner.check_health()
```

## 🔧 Utility Classes

### PromptLoader

Load and manage prompt templates.

```python
from lmstrix.loaders.prompt_loader import PromptLoader

# Create loader
loader = PromptLoader()

# Load prompts from TOML file
prompts = loader.load_prompts("templates.toml")

# Get specific prompt
prompt = loader.get_prompt("summary", prompts)

# Render prompt with variables
rendered = loader.render_prompt(prompt, {"text": "Content to summarize"})
```

### ContextLoader

Load context data from files.

```python
from lmstrix.loaders.context_loader import ContextLoader

# Create loader
loader = ContextLoader()

# Load text file
content = loader.load_text_file("document.txt")

# Load with encoding detection
content = loader.load_text_file("document.txt", encoding="auto")

# Load multiple files
contents = loader.load_multiple_files(["file1.txt", "file2.txt"])
```

### Configuration

Manage LMStrix configuration programmatically.

```python
from lmstrix.utils.config import Config

# Load configuration
config = Config.load()

# Get configuration values
lm_studio_url = config.get("lmstudio.base_url", "http://localhost:1234")
safety_threshold = config.get("safety.max_context_threshold", 65536)

# Update configuration
config.set("output.verbose_by_default", True)
config.save()

# Create custom configuration
custom_config = Config({
    "lmstudio": {"base_url": "http://remote:1234"},
    "safety": {"max_context_threshold": 32768}
})
```

## 🎯 Advanced Usage Patterns

### Async Operations

LMStrix supports async/await for non-blocking operations:

```python
import asyncio
from lmstrix.core.inference_manager import AsyncInferenceManager

async def main():
    manager = AsyncInferenceManager()
    
    # Run multiple inferences concurrently
    tasks = [
        manager.infer("Question 1", "model1"),
        manager.infer("Question 2", "model2"),
        manager.infer("Question 3", "model3")
    ]
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"Result {i+1}: {result['response'][:100]}...")

# Run async function
asyncio.run(main())
```

### Context Management

Handle different context strategies:

```python
from lmstrix.core.context import ContextManager

# Create context manager
ctx_manager = ContextManager()

# Smart context allocation
context_size = ctx_manager.calculate_optimal_context(
    prompt_length=500,
    desired_output=200,
    model_max_context=32768,
    strategy="balanced"  # "conservative", "balanced", "aggressive"
)

# Context validation
is_valid = ctx_manager.validate_context_size(
    prompt="Your prompt here",
    output_tokens=100,
    model_context_limit=16384
)
```

### Error Handling

Robust error handling patterns:

```python
from lmstrix.api.exceptions import (
    LMStrixError,
    ModelNotFoundError,
    ContextLimitExceededError,
    InferenceTimeoutError,
    LMStudioConnectionError
)

try:
    result = manager.infer(
        model_id="nonexistent-model",
        prompt="Test prompt"
    )
except ModelNotFoundError as e:
    print(f"Model not found: {e}")
    # Handle missing model
    
except ContextLimitExceededError as e:
    print(f"Context too large: {e}")
    # Reduce context size or split prompt
    
except InferenceTimeoutError as e:
    print(f"Inference timeout: {e}")
    # Retry with longer timeout
    
except LMStudioConnectionError as e:
    print(f"LM Studio connection failed: {e}")
    # Check if LM Studio is running
    
except LMStrixError as e:
    print(f"General LMStrix error: {e}")
    # Handle other errors
```

### Batch Processing

Process multiple inputs efficiently:

```python
from lmstrix.core.batch_processor import BatchProcessor

# Create batch processor
processor = BatchProcessor(
    model_id="llama-3.2-3b-instruct",
    max_workers=3,
    batch_size=10
)

# Process multiple prompts
prompts = [
    "What is AI?",
    "Explain machine learning",
    "Define neural networks",
    # ... more prompts
]

results = processor.process_batch(prompts)

for prompt, result in zip(prompts, results):
    if result["succeeded"]:
        print(f"Q: {prompt}")
        print(f"A: {result['response']}")
    else:
        print(f"Failed: {prompt} - {result['error']}")
```

### Model Comparison

Compare different models on the same task:

```python
from lmstrix.utils.comparison import ModelComparator

# Create comparator
comparator = ModelComparator([
    "llama-3.2-3b-instruct",
    "mistral-7b-instruct",
    "codellama-13b-python"
])

# Compare models on a task
prompt = "Explain quantum computing"
comparison = comparator.compare_models(
    prompt=prompt,
    metrics=["response_time", "tokens_per_second", "response_length"]
)

# Results include performance metrics for each model
for model_result in comparison:
    print(f"Model: {model_result['model_id']}")
    print(f"Response time: {model_result['response_time']:.2f}s")
    print(f"Speed: {model_result['tokens_per_second']:.1f} tok/s")
    print("---")
```

## 🔌 Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
from lmstrix.core.inference_manager import InferenceManager

app = Flask(__name__)
inference_manager = InferenceManager()

@app.route('/api/infer', methods=['POST'])
def api_infer():
    data = request.json
    
    try:
        result = inference_manager.infer(
            model_id=data['model'],
            prompt=data['prompt'],
            out_ctx=data.get('max_tokens', 100),
            temperature=data.get('temperature', 0.7)
        )
        
        return jsonify({
            'success': result['succeeded'],
            'response': result['response'],
            'stats': {
                'tokens_used': result['tokens_used'],
                'response_time': result['inference_time']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Data Processing Pipeline

```python
import pandas as pd
from lmstrix.core.inference_manager import InferenceManager

# Load data
df = pd.read_csv('customer_feedback.csv')

# Initialize inference manager
manager = InferenceManager()

# Process each feedback entry
def analyze_sentiment(text):
    result = manager.infer(
        model_id="llama-3.2-3b-instruct",
        prompt=f"Analyze the sentiment of this feedback: {text}",
        out_ctx=50,
        temperature=0.3
    )
    return result['response'] if result['succeeded'] else "Error"

# Apply to dataframe
df['sentiment_analysis'] = df['feedback'].apply(analyze_sentiment)

# Save results
df.to_csv('analyzed_feedback.csv', index=False)
```

### Jupyter Notebook Integration

```python
# Cell 1: Setup
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.loaders.model_loader import load_model_registry
import matplotlib.pyplot as plt

manager = InferenceManager(verbose=True)
registry = load_model_registry()

# Cell 2: Model exploration
models = registry.list_models()
tested_models = [m for m in models if m['test_status'] == 'tested']

# Visualize model contexts
contexts = [m['tested_context'] for m in tested_models]
names = [m['name'] for m in tested_models]

plt.figure(figsize=(12, 6))
plt.bar(names, contexts)
plt.xticks(rotation=45)
plt.title('Model Context Limits')
plt.ylabel('Context Size (tokens)')
plt.tight_layout()
plt.show()

# Cell 3: Interactive inference
def ask_model(question, model_name="llama-3.2-3b-instruct"):
    result = manager.infer(
        model_id=model_name,
        prompt=question,
        out_ctx="auto",
        temperature=0.7
    )
    
    if result['succeeded']:
        print(f"🤖 {model_name}:")
        print(result['response'])
        print(f"\n📊 Stats: {result['tokens_used']} tokens, {result['inference_time']:.1f}s")
    else:
        print(f"❌ Error: {result['error']}")

# Interactive usage
ask_model("What is machine learning?")
```

### Monitoring and Logging

```python
import logging
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.utils.logging import setup_logging

# Setup structured logging
setup_logging(
    level=logging.INFO,
    file_path="lmstrix_app.log",
    include_performance_metrics=True
)

logger = logging.getLogger(__name__)

class MonitoredInferenceManager:
    def __init__(self):
        self.manager = InferenceManager()
        self.request_count = 0
        self.total_tokens = 0
    
    def infer(self, **kwargs):
        self.request_count += 1
        
        logger.info(f"Starting inference request #{self.request_count}")
        logger.info(f"Model: {kwargs.get('model_id')}")
        logger.info(f"Prompt length: {len(kwargs.get('prompt', ''))}")
        
        result = self.manager.infer(**kwargs)
        
        if result['succeeded']:
            self.total_tokens += result['tokens_used']
            logger.info(f"Inference successful: {result['tokens_used']} tokens, {result['inference_time']:.2f}s")
        else:
            logger.error(f"Inference failed: {result['error']}")
        
        logger.info(f"Total requests: {self.request_count}, Total tokens: {self.total_tokens}")
        
        return result

# Usage
monitored_manager = MonitoredInferenceManager()
result = monitored_manager.infer(
    model_id="llama-3.2-3b-instruct",
    prompt="Explain neural networks"
)
```

## 🧪 Testing and Development

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
from lmstrix.core.inference_manager import InferenceManager

class TestInferenceManager(unittest.TestCase):
    def setUp(self):
        self.manager = InferenceManager()
    
    @patch('lmstrix.api.client.LMStudioClient')
    def test_successful_inference(self, mock_client):
        # Mock the API response
        mock_client.return_value.chat_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'total_tokens': 25, 'prompt_tokens': 10, 'completion_tokens': 15}
        }
        
        result = self.manager.infer(
            model_id="test-model",
            prompt="Test prompt"
        )
        
        self.assertTrue(result['succeeded'])
        self.assertEqual(result['response'], 'Test response')
        self.assertEqual(result['tokens_used'], 25)
    
    def test_invalid_model_id(self):
        with self.assertRaises(ModelNotFoundError):
            self.manager.infer(
                model_id="nonexistent-model",
                prompt="Test prompt"
            )

if __name__ == '__main__':
    unittest.main()
```

### Performance Testing

```python
import time
import statistics
from lmstrix.core.inference_manager import InferenceManager

def benchmark_model(model_id, prompts, iterations=5):
    manager = InferenceManager()
    results = []
    
    for prompt in prompts:
        times = []
        token_rates = []
        
        for _ in range(iterations):
            start_time = time.time()
            result = manager.infer(
                model_id=model_id,
                prompt=prompt,
                out_ctx=100
            )
            
            if result['succeeded']:
                times.append(result['inference_time'])
                token_rates.append(result['tokens_per_second'])
        
        results.append({
            'prompt': prompt,
            'avg_time': statistics.mean(times),
            'avg_token_rate': statistics.mean(token_rates),
            'time_std': statistics.stdev(times) if len(times) > 1 else 0
        })
    
    return results

# Run benchmark
test_prompts = [
    "What is AI?",
    "Explain machine learning in detail",
    "Write a short story about space"
]

benchmark_results = benchmark_model("llama-3.2-3b-instruct", test_prompts)

for result in benchmark_results:
    print(f"Prompt: {result['prompt'][:30]}...")
    print(f"Avg time: {result['avg_time']:.2f}s ± {result['time_std']:.2f}")
    print(f"Avg rate: {result['avg_token_rate']:.1f} tokens/sec")
    print("---")
```

## 🚀 Next Steps

With the Python API mastered:

- **[Context Testing](context-testing.md)** - Deep dive into optimization algorithms
- **[Prompt Templating](prompt-templating.md)** - Advanced prompt engineering
- **[Model Management](model-management.md)** - Registry and model operations
- **[Performance & Optimization](performance.md)** - Production-ready optimization

---

*Python API mastery achieved! Build powerful LM Studio integrations! 🐍*