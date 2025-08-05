---
# this_file: src_docs/md/model-management.md
title: Model Management Guide
description: Master model discovery, registry management, persistence, and organization for efficient workflows
---

# Model Management Guide

LMStrix provides comprehensive model management capabilities through its registry system, model discovery, state tracking, and organization features. This guide covers everything from basic model operations to advanced registry management.

## 🗂️ Model Registry Overview

### What is the Model Registry?

The model registry is LMStrix's central database that tracks:

- **Model metadata** - Names, sizes, parameters, types
- **Test results** - Context limits, test status, performance metrics
- **Usage statistics** - Inference counts, total tokens, average performance
- **State information** - Load status, last used, health checks

### Registry Structure

```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00Z",
  "models": {
    "llama-3.2-3b-instruct": {
      "id": "llama-3.2-3b-instruct",
      "name": "Llama 3.2 3B Instruct",
      "display_name": "Llama 3.2 3B Instruct",
      "size_mb": 3276,
      "parameters": "3.2B",
      "type": "chat",
      "architecture": "llama",
      "context_window": 128000,
      "tested_context": 29696,
      "test_status": "tested",
      "last_tested": "2024-01-15T10:30:00Z",
      "test_iterations": 8,
      "test_duration": 156.7,
      "performance_metrics": {
        "avg_tokens_per_second": 42.3,
        "peak_memory_mb": 3847,
        "load_time_seconds": 8.2
      },
      "usage_stats": {
        "inference_count": 127,
        "total_tokens_processed": 45832,
        "total_inference_time": 892.4,
        "last_used": "2024-01-15T09:45:00Z"
      },
      "metadata": {
        "added_date": "2024-01-10T14:20:00Z",
        "source": "lm_studio_scan",
        "tags": ["instruct", "chat", "3b"],
        "description": "Efficient instruction-following model"
      }
    }
  },
  "statistics": {
    "total_models": 8,
    "tested_models": 6,
    "untested_models": 2,
    "failed_tests": 0,
    "avg_context_limit": 34521,
    "total_inference_count": 856,
    "last_scan": "2024-01-15T08:00:00Z"
  }
}
```

## 🔍 Model Discovery

### Automatic Discovery

LMStrix automatically discovers models from LM Studio:

```bash
# Basic scan
lmstrix scan

# Verbose scan with detailed information
lmstrix scan --verbose

# Force refresh (ignore cache)
lmstrix scan --refresh

# Scan with custom server
lmstrix scan --server http://remote-lmstudio:1234
```

### Discovery Process

1. **Connect to LM Studio API** - Check server availability
2. **Query available models** - Get model list from API
3. **Extract metadata** - Parse model information
4. **Update registry** - Merge with existing data
5. **Preserve test results** - Keep existing context limits

### Discovery Output

```bash
$ lmstrix scan --verbose
🔍 Scanning LM Studio server at http://localhost:1234...
✅ Server connection successful (ping: 12ms)
📡 Discovering available models...

Found 4 models:
┌─────────────────────────────────┬──────────┬─────────────┬───────────┬─────────────┐
│ Model                           │ Size     │ Parameters  │ Type      │ Status      │
├─────────────────────────────────┼──────────┼─────────────┼───────────┼─────────────┤
│ llama-3.2-3b-instruct          │ 3.2 GB   │ 3.2B        │ Chat      │ ✅ Known    │
│ mistral-7b-instruct-v0.2       │ 7.1 GB   │ 7.1B        │ Chat      │ 🆕 New      │
│ codellama-13b-python           │ 13.0 GB  │ 13.0B       │ Code      │ ✅ Known    │
│ phi-3-mini-4k-instruct         │ 2.4 GB   │ 3.8B        │ Chat      │ 🆕 New      │
└─────────────────────────────────┴──────────┴─────────────┴───────────┴─────────────┘

📋 Registry Updates:
  • Added 2 new models
  • Updated 2 existing models
  • Preserved test results for 2 models

⏱️ Scan completed in 3.24 seconds
```

### Custom Model Addition

Add models manually when auto-discovery isn't available:

```python
from lmstrix.loaders.model_loader import load_model_registry

registry = load_model_registry()

# Add custom model
registry.add_model({
    "id": "custom-llama-7b",
    "name": "Custom Llama 7B",
    "size_mb": 7168,
    "parameters": "7B",
    "type": "chat",
    "architecture": "llama",
    "context_window": 4096,
    "source": "manual_addition",
    "tags": ["custom", "llama", "7b"]
})

registry.save()
```

## 📊 Registry Operations

### Listing and Filtering

#### Basic Listing

```bash
# List all models
lmstrix list

# Sort by different criteria
lmstrix list --sort name        # Alphabetical
lmstrix list --sort size        # By model size
lmstrix list --sort ctx         # By context limit
lmstrix list --sort date        # By last test date

# Reverse sort order
lmstrix list --sort size --reverse
```

#### Advanced Filtering

```bash
# Filter by test status
lmstrix list --filter "status:tested"
lmstrix list --filter "status:untested"
lmstrix list --filter "status:failed"

# Filter by size ranges
lmstrix list --filter "size:>5GB"
lmstrix list --filter "size:1GB-10GB"

# Filter by context limits
lmstrix list --filter "ctx:>30000"
lmstrix list --filter "ctx:16384-65536"

# Filter by model type
lmstrix list --filter "type:chat"
lmstrix list --filter "type:code"

# Filter by tags
lmstrix list --filter "tag:instruct"
lmstrix list --filter "tag:llama,chat"

# Combined filters
lmstrix list --filter "status:tested,size:>5GB,type:chat"
```

#### Output Formats

```bash
# Table format (default)
lmstrix list --show table

# JSON for automation
lmstrix list --show json

# CSV for analysis
lmstrix list --show csv

# YAML format
lmstrix list --show yaml

# Brief summary
lmstrix list --show summary
```

### Model Information

#### Detailed Model Info

```python
from lmstrix.loaders.model_loader import load_model_registry

registry = load_model_registry()

# Get detailed model information
model_info = registry.get_model_info("llama-3.2-3b-instruct")

print(f"Model: {model_info['name']}")
print(f"Size: {model_info['size_mb']:,} MB")
print(f"Context: {model_info.get('tested_context', 'Unknown')}")
print(f"Performance: {model_info.get('avg_tokens_per_second', 'N/A')} tok/s")
print(f"Usage: {model_info.get('inference_count', 0)} inferences")
```

#### Usage Statistics

```python
# Get usage statistics for a model
stats = registry.get_model_usage_stats("llama-3.2-3b-instruct")

print(f"Total inferences: {stats['inference_count']}")
print(f"Total tokens: {stats['total_tokens_processed']:,}")
print(f"Average tokens per inference: {stats['avg_tokens_per_inference']:.1f}")
print(f"Total time: {stats['total_inference_time']:.1f} seconds")
print(f"Last used: {stats['last_used']}")
```

#### Performance Metrics

```python
# Get performance metrics
metrics = registry.get_model_performance("llama-3.2-3b-instruct")

print(f"Average speed: {metrics['avg_tokens_per_second']:.1f} tok/s")
print(f"Peak memory: {metrics['peak_memory_mb']:,} MB")
print(f"Load time: {metrics['load_time_seconds']:.1f} seconds")
print(f"Test duration: {metrics['test_duration']:.1f} seconds")
```

## 🏷️ Model Organization

### Tagging System

#### Automatic Tags

LMStrix automatically assigns tags based on model characteristics:

```python
{
    "architecture_tags": ["llama", "mistral", "phi", "codellama"],
    "size_tags": ["small", "medium", "large", "xl"],  # Based on parameter count
    "type_tags": ["chat", "instruct", "code", "completion"],
    "capability_tags": ["multilingual", "reasoning", "creative"],
    "performance_tags": ["fast", "balanced", "thorough"]  # Based on speed/quality
}
```

#### Custom Tags

Add your own tags for organization:

```python
# Add custom tags
registry.add_tags("llama-3.2-3b-instruct", ["production", "favorite", "qa"])

# Remove tags
registry.remove_tags("llama-3.2-3b-instruct", ["qa"])

# Get models by tag
production_models = registry.get_models_by_tag("production")
```

### Model Groups

#### Create Model Groups

Organize related models into groups:

```python
# Create model groups
registry.create_group("chat_models", [
    "llama-3.2-3b-instruct",
    "mistral-7b-instruct",
    "phi-3-mini-4k-instruct"
])

registry.create_group("code_models", [
    "codellama-13b-python",
    "codellama-7b-instruct"
])

# Add models to existing group
registry.add_to_group("chat_models", "new-chat-model")
```

#### Group Operations

```python
# List groups
groups = registry.list_groups()

# Get models in group
chat_models = registry.get_group("chat_models")

# Test all models in group
for model_id in chat_models:
    result = tester.test_model_context(model_id, threshold=32768)
```

### Model Profiles

#### Create Usage Profiles

Define different usage patterns for models:

```python
# Create profiles for different use cases
registry.create_profile("quick_answers", {
    "preferred_models": ["llama-3.2-3b-instruct", "phi-3-mini-4k-instruct"],
    "max_context": 1024,
    "temperature": 0.3,
    "description": "Fast responses for simple questions"
})

registry.create_profile("detailed_analysis", {
    "preferred_models": ["codellama-13b-python", "mistral-7b-instruct"],
    "max_context": 16384,
    "temperature": 0.7,
    "description": "Comprehensive analysis tasks"
})

# Use profile for inference
profile = registry.get_profile("quick_answers")
best_model = profile["preferred_models"][0]
```

## 🔄 Model State Management

### Model States

LMStrix tracks model states through the inference lifecycle:

```python
{
    "unloaded": "Model not currently in memory",
    "loading": "Model being loaded into memory",
    "loaded": "Model ready for inference",
    "active": "Model currently processing inference",
    "error": "Model in error state",
    "unloading": "Model being removed from memory"
}
```

### State Tracking

```python
from lmstrix.core.models import ModelStateManager

state_manager = ModelStateManager()

# Check model state
state = state_manager.get_model_state("llama-3.2-3b-instruct")
print(f"Model state: {state}")

# Get all loaded models
loaded_models = state_manager.get_loaded_models()
print(f"Loaded models: {loaded_models}")

# Monitor state changes
def on_state_change(model_id, old_state, new_state):
    print(f"{model_id}: {old_state} → {new_state}")

state_manager.add_state_listener(on_state_change)
```

### Memory Management

#### Automatic Memory Management

```python
# Configure automatic memory management
registry.configure_memory_management({
    "auto_unload_inactive": True,
    "inactive_timeout_minutes": 30,
    "memory_threshold_percent": 80,
    "max_loaded_models": 2
})
```

#### Manual Memory Control

```python
# Load model explicitly
state_manager.load_model("llama-3.2-3b-instruct")

# Unload model to free memory
state_manager.unload_model("llama-3.2-3b-instruct")

# Unload all models
state_manager.unload_all_models()

# Get memory usage
memory_info = state_manager.get_memory_usage()
print(f"Total memory: {memory_info['total_mb']:,} MB")
print(f"Used memory: {memory_info['used_mb']:,} MB")
print(f"Available: {memory_info['available_mb']:,} MB")
```

## 📈 Performance Tracking

### Usage Analytics

#### Track Model Usage

```python
# Record inference usage
registry.record_inference("llama-3.2-3b-instruct", {
    "tokens_processed": 245,
    "inference_time": 5.7,
    "timestamp": "2024-01-15T10:30:00Z",
    "success": True
})

# Get usage trends
trends = registry.get_usage_trends("llama-3.2-3b-instruct", days=30)
print(f"Daily average inferences: {trends['daily_avg']:.1f}")
print(f"Peak usage day: {trends['peak_day']}")
print(f"Total tokens this month: {trends['monthly_tokens']:,}")
```

#### Performance Monitoring

```python
# Monitor performance metrics
metrics = registry.get_performance_metrics("llama-3.2-3b-instruct")

print(f"Average response time: {metrics['avg_response_time']:.2f}s")
print(f"P95 response time: {metrics['p95_response_time']:.2f}s")
print(f"Throughput: {metrics['tokens_per_second']:.1f} tok/s")
print(f"Success rate: {metrics['success_rate']:.1%}")
```

#### Generate Reports

```python
# Generate performance report
report = registry.generate_performance_report(
    start_date="2024-01-01",
    end_date="2024-01-31",
    models=["llama-3.2-3b-instruct", "mistral-7b-instruct"]
)

print(f"Report period: {report['period']}")
print(f"Total inferences: {report['total_inferences']:,}")
print(f"Average latency: {report['avg_latency']:.2f}s")
print(f"Most used model: {report['most_used_model']}")
```

### Benchmarking

#### Model Comparison

```python
from lmstrix.utils.benchmarking import ModelBenchmark

benchmark = ModelBenchmark()

# Compare models on standard tasks
results = benchmark.compare_models([
    "llama-3.2-3b-instruct",
    "mistral-7b-instruct",
    "phi-3-mini-4k-instruct"
], tasks=["qa", "summarization", "creative_writing"])

# Display results
for model_result in results:
    print(f"Model: {model_result['model_id']}")
    print(f"QA Score: {model_result['qa_score']:.2f}")
    print(f"Speed: {model_result['avg_speed']:.1f} tok/s")
    print(f"Memory: {model_result['peak_memory']:,} MB")
    print("---")
```

#### Custom Benchmarks

```python
# Create custom benchmark
benchmark.create_custom_benchmark("coding_tasks", {
    "prompts": [
        "Write a Python function to sort a list",
        "Explain recursion with examples",
        "Debug this code: [code snippet]"
    ],
    "evaluation_criteria": ["correctness", "clarity", "efficiency"],
    "timeout_seconds": 60
})

# Run custom benchmark
results = benchmark.run_benchmark("coding_tasks", "codellama-13b-python")
```

## 🔧 Advanced Registry Management

### Registry Maintenance

#### Cleanup Operations

```python
# Remove orphaned models (not in LM Studio)
removed = registry.cleanup_orphaned_models()
print(f"Removed {len(removed)} orphaned models")

# Remove old test results
registry.cleanup_old_test_results(days=90)

# Compact registry (remove unused data)
registry.compact()
```

#### Registry Validation

```python
# Validate registry integrity
validation_result = registry.validate()

if validation_result["valid"]:
    print("✅ Registry is valid")
else:
    print("❌ Registry issues found:")
    for issue in validation_result["issues"]:
        print(f"  • {issue}")

# Fix common issues automatically
registry.auto_fix_issues()
```

### Backup and Restore

#### Backup Registry

```python
# Create backup
backup_path = registry.create_backup()
print(f"Registry backed up to: {backup_path}")

# Create backup with custom name
backup_path = registry.create_backup("pre_update_backup")

# List available backups
backups = registry.list_backups()
for backup in backups:
    print(f"Backup: {backup['name']} ({backup['date']})")
```

#### Restore Registry

```python
# Restore from backup
registry.restore_from_backup("pre_update_backup")

# Restore from file
registry.restore_from_file("/path/to/backup.json")

# Merge registry data
registry.merge_from_backup("another_backup", strategy="prefer_newer")
```

### Import/Export

#### Export Registry Data

```bash
# Export to JSON
lmstrix list --show json > models_export.json

# Export specific models
lmstrix list --filter "status:tested" --show json > tested_models.json

# Export with full metadata
lmstrix registry export --full-metadata models_full.json
```

#### Import Registry Data

```python
# Import models from file
registry.import_from_file("models_export.json", merge_strategy="update")

# Import with validation
try:
    imported_count = registry.import_models(
        "external_models.json",
        validate=True,
        skip_duplicates=True
    )
    print(f"Imported {imported_count} models")
except ValidationError as e:
    print(f"Import failed: {e}")
```

### Multi-Registry Management

#### Multiple Registries

```python
# Work with multiple registries
prod_registry = load_model_registry("~/.lmstrix/prod_models.json")
dev_registry = load_model_registry("~/.lmstrix/dev_models.json")

# Sync registries
sync_result = prod_registry.sync_with(dev_registry)
print(f"Synced {sync_result['models_updated']} models")

# Compare registries
diff = prod_registry.compare_with(dev_registry)
print(f"Different models: {len(diff['different'])}")
print(f"Missing in prod: {len(diff['missing_in_first'])}")
```

## 🚀 Automation and Integration

### Automated Workflows

#### Model Health Monitoring

```python
#!/usr/bin/env python3
# model_health_monitor.py

import schedule
import time
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.core.context_tester import ContextTester

def health_check():
    registry = load_model_registry()
    tester = ContextTester()
    
    # Check all models
    for model in registry.list_models():
        if model['test_status'] == 'tested':
            # Quick health check
            result = tester.quick_health_check(model['id'])
            if not result['healthy']:
                print(f"⚠️ Health issue detected: {model['id']}")
                # Send alert, log issue, etc.

# Schedule health checks
schedule.every(6).hours.do(health_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

#### Auto-Testing New Models

```python
def auto_test_new_models():
    registry = load_model_registry()
    tester = ContextTester()
    
    # Scan for new models
    new_models = registry.scan_for_new_models()
    
    for model_id in new_models:
        print(f"Auto-testing new model: {model_id}")
        result = tester.test_model_context(
            model_id,
            threshold=32768,
            verbose=False
        )
        
        if result['test_successful']:
            print(f"✅ {model_id}: {result['optimal_context']:,} tokens")
        else:
            print(f"❌ {model_id}: Test failed")

# Run daily
schedule.every().day.at("02:00").do(auto_test_new_models)
```

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/model-registry.yml
name: Model Registry Maintenance

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  maintain-registry:
    runs-on: self-hosted  # Requires LM Studio access
    
    steps:
      - name: Scan for new models
        run: lmstrix scan --refresh
      
      - name: Test untested models
        run: lmstrix test --all --threshold 32768
      
      - name: Generate report
        run: |
          lmstrix list --show json > registry-report.json
          lmstrix registry stats > registry-stats.txt
      
      - name: Backup registry
        run: |
          cp ~/.lmstrix/models.json ./backup/models-$(date +%Y%m%d).json
      
      - name: Commit changes
        run: |
          git add .
          git commit -m "Update model registry - $(date)"
          git push
```

## 🚀 Next Steps

Master model management, then explore:

- **[Prompt Templating](prompt-templating.md)** - Advanced prompt engineering
- **[Performance & Optimization](performance.md)** - Production optimization techniques
- **[Python API](python-api.md)** - Programmatic model management
- **[CLI Interface](cli-interface.md)** - Command-line power user techniques

---

*Model management mastered! Organize and optimize your model fleet! 🗂️*