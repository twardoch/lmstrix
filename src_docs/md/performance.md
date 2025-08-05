---
# this_file: src_docs/md/performance.md
title: Performance & Optimization Guide
description: Performance tuning, monitoring, optimization strategies, and production deployment patterns
---

# Performance & Optimization Guide

This comprehensive guide covers performance optimization strategies, monitoring techniques, and production deployment patterns to help you get maximum performance from LMStrix and your language models.

## 📊 Performance Fundamentals

### Key Performance Metrics

Understanding these metrics is crucial for optimization:

**Latency Metrics:**
- **Time to First Token (TTFT)** - How quickly generation begins
- **Total Inference Time** - Complete generation duration
- **Token Generation Speed** - Tokens per second during generation

**Throughput Metrics:**
- **Requests per Second (RPS)** - Concurrent request handling capacity
- **Tokens per Second (TPS)** - Overall token processing rate
- **Context Utilization** - How efficiently context windows are used

**Resource Metrics:**
- **Memory Usage** - RAM consumption during inference
- **GPU Utilization** - Graphics processing efficiency
- **CPU Usage** - Processing overhead
- **Disk I/O** - Model loading and caching impact

### Performance Baseline

Establish baseline performance for optimization:

```python
from lmstrix.utils.performance import PerformanceBenchmark
from lmstrix.core.inference_manager import InferenceManager

# Create benchmark suite
benchmark = PerformanceBenchmark()

# Configure test parameters
test_config = {
    "models": ["llama-3.2-3b-instruct", "mistral-7b-instruct"],
    "prompts": [
        "Short question: What is AI?",
        "Medium analysis: Explain machine learning in 200 words",
        "Long generation: Write a detailed 500-word essay on neural networks"
    ],
    "iterations": 10,
    "warmup_iterations": 3
}

# Run baseline benchmark
baseline_results = benchmark.run_baseline(test_config)

# Display results
for model, metrics in baseline_results.items():
    print(f"Model: {model}")
    print(f"  TTFT: {metrics['avg_ttft']:.2f}s ± {metrics['ttft_std']:.2f}")
    print(f"  TPS: {metrics['avg_tps']:.1f} ± {metrics['tps_std']:.1f}")
    print(f"  Memory: {metrics['peak_memory_mb']:.0f} MB")
    print("---")
```

## ⚡ Context Optimization

### Smart Context Management

Optimize context usage for better performance:

```python
from lmstrix.core.context_optimizer import ContextOptimizer

optimizer = ContextOptimizer()

# Optimize context allocation
optimized_context = optimizer.optimize_context(
    prompt="Your prompt here",
    target_output_length=200,
    model_max_context=32768,
    strategy="balanced"  # "conservative", "balanced", "aggressive"
)

print(f"Recommended context allocation:")
print(f"  Prompt tokens: {optimized_context['prompt_tokens']}")
print(f"  Output tokens: {optimized_context['output_tokens']}")
print(f"  Safety buffer: {optimized_context['safety_buffer']}")
print(f"  Total context: {optimized_context['total_context']}")
```

### Dynamic Context Scaling

Automatically adjust context based on workload:

```python
class DynamicContextManager:
    def __init__(self):
        self.performance_history = []
        self.context_adjustments = {}
    
    def adjust_context(self, model_id, prompt_length, performance_target="balanced"):
        """Dynamically adjust context based on performance targets."""
        
        # Get model capabilities
        model_info = registry.get_model(model_id)
        max_context = model_info.get("tested_context", 16384)
        
        # Performance-based context scaling
        if performance_target == "speed":
            # Prioritize speed - use smaller contexts
            recommended_context = min(prompt_length * 1.5, max_context * 0.6)
        elif performance_target == "quality":
            # Prioritize quality - use larger contexts
            recommended_context = min(prompt_length * 3.0, max_context * 0.9)
        else:  # balanced
            recommended_context = min(prompt_length * 2.0, max_context * 0.8)
        
        return int(recommended_context)
    
    def monitor_performance(self, model_id, context_size, performance_metrics):
        """Track performance for future optimizations."""
        self.performance_history.append({
            "model_id": model_id,
            "context_size": context_size,
            "ttft": performance_metrics["time_to_first_token"],
            "tps": performance_metrics["tokens_per_second"],
            "memory_mb": performance_metrics["memory_usage_mb"],
            "timestamp": time.time()
        })
        
        # Auto-adjust if performance degrades
        if len(self.performance_history) > 10:
            recent_performance = self.performance_history[-5:]
            avg_tps = sum(p["tps"] for p in recent_performance) / 5
            
            if avg_tps < 20:  # Performance threshold
                self.context_adjustments[model_id] = {
                    "action": "reduce_context",
                    "factor": 0.8,
                    "reason": "low_throughput"
                }
```

### Context Caching Strategy

Implement intelligent context caching:

```python
from lmstrix.utils.context_cache import ContextCache

class SmartContextCache:
    def __init__(self, max_cache_size_mb=1024):
        self.cache = ContextCache(max_size_mb=max_cache_size_mb)
        self.access_patterns = {}
    
    def get_cached_context(self, prompt_hash, model_id):
        """Retrieve cached context if available."""
        cache_key = f"{model_id}:{prompt_hash}"
        
        # Track access patterns
        if cache_key not in self.access_patterns:
            self.access_patterns[cache_key] = {
                "access_count": 0,
                "last_access": time.time()
            }
        
        self.access_patterns[cache_key]["access_count"] += 1
        self.access_patterns[cache_key]["last_access"] = time.time()
        
        return self.cache.get(cache_key)
    
    def cache_context(self, prompt_hash, model_id, context_data):
        """Cache context with intelligent eviction."""
        cache_key = f"{model_id}:{prompt_hash}"
        
        # Calculate cache priority based on access patterns
        priority = self.calculate_cache_priority(cache_key)
        
        self.cache.set(cache_key, context_data, priority=priority)
    
    def calculate_cache_priority(self, cache_key):
        """Calculate cache priority based on access patterns."""
        if cache_key not in self.access_patterns:
            return 1.0
        
        pattern = self.access_patterns[cache_key]
        
        # Factors: access frequency, recency, context size
        frequency_score = min(pattern["access_count"] / 10, 1.0)
        recency_score = max(0, 1.0 - (time.time() - pattern["last_access"]) / 3600)
        
        return (frequency_score * 0.6) + (recency_score * 0.4)
```

## 🚀 Model Performance Tuning

### Model Selection Optimization

Choose optimal models based on requirements:

```python
from lmstrix.utils.model_selector import IntelligentModelSelector

class ModelSelector:
    def __init__(self):
        self.performance_db = {}
        self.load_performance_data()
    
    def select_optimal_model(self, requirements):
        """Select best model based on performance requirements."""
        
        candidates = self.filter_models_by_requirements(requirements)
        
        # Score models based on requirements
        scored_models = []
        for model in candidates:
            score = self.calculate_model_score(model, requirements)
            scored_models.append((model, score))
        
        # Return best model
        best_model = max(scored_models, key=lambda x: x[1])
        return best_model[0]
    
    def calculate_model_score(self, model, requirements):
        """Calculate model fitness score."""
        performance = self.performance_db.get(model["id"], {})
        
        # Scoring factors
        speed_score = self.score_speed(performance, requirements.get("speed_priority", 0.5))
        quality_score = self.score_quality(performance, requirements.get("quality_priority", 0.5))
        memory_score = self.score_memory(performance, requirements.get("memory_limit_mb"))
        context_score = self.score_context(model, requirements.get("min_context", 0))
        
        # Weighted average
        weights = {
            "speed": requirements.get("speed_weight", 0.3),
            "quality": requirements.get("quality_weight", 0.3),
            "memory": requirements.get("memory_weight", 0.2),
            "context": requirements.get("context_weight", 0.2)
        }
        
        total_score = (
            speed_score * weights["speed"] +
            quality_score * weights["quality"] +
            memory_score * weights["memory"] +
            context_score * weights["context"]
        )
        
        return total_score

# Usage example
selector = ModelSelector()

# Define requirements
requirements = {
    "speed_priority": 0.8,      # High speed priority
    "quality_priority": 0.6,    # Moderate quality needs
    "memory_limit_mb": 8192,    # 8GB memory limit
    "min_context": 16384,       # Minimum context needed
    "speed_weight": 0.4,        # Weight preferences
    "quality_weight": 0.3,
    "memory_weight": 0.2,
    "context_weight": 0.1
}

best_model = selector.select_optimal_model(requirements)
print(f"Recommended model: {best_model['name']}")
```

### Inference Parameter Optimization

Optimize model parameters for specific use cases:

```python
from lmstrix.utils.parameter_optimizer import ParameterOptimizer

class InferenceOptimizer:
    def __init__(self):
        self.optimizer = ParameterOptimizer()
        self.optimization_history = {}
    
    def optimize_parameters(self, model_id, use_case, sample_prompts):
        """Optimize inference parameters for specific use case."""
        
        # Define parameter search space
        param_space = {
            "temperature": [0.1, 0.3, 0.5, 0.7, 0.9, 1.1],
            "top_p": [0.1, 0.3, 0.5, 0.8, 0.9, 0.95],
            "top_k": [10, 20, 40, 50, 100, -1],
            "context_ratio": [0.6, 0.7, 0.8, 0.9]  # Ratio of max context to use
        }
        
        best_params = {}
        best_score = 0
        
        # Grid search optimization
        for temp in param_space["temperature"]:
            for top_p in param_space["top_p"]:
                for top_k in param_space["top_k"]:
                    for ctx_ratio in param_space["context_ratio"]:
                        
                        params = {
                            "temperature": temp,
                            "top_p": top_p,
                            "top_k": top_k,
                            "context_ratio": ctx_ratio
                        }
                        
                        score = self.evaluate_parameters(
                            model_id, params, sample_prompts, use_case
                        )
                        
                        if score > best_score:
                            best_score = score
                            best_params = params.copy()
        
        return best_params, best_score
    
    def evaluate_parameters(self, model_id, params, prompts, use_case):
        """Evaluate parameter combination."""
        scores = []
        
        for prompt in prompts:
            # Run inference with parameters
            result = manager.infer(
                model_id=model_id,
                prompt=prompt,
                temperature=params["temperature"],
                top_p=params["top_p"],
                top_k=params["top_k"],
                out_ctx=int(32768 * params["context_ratio"])
            )
            
            if result["succeeded"]:
                # Calculate use-case specific score
                score = self.calculate_use_case_score(result, use_case)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def calculate_use_case_score(self, result, use_case):
        """Calculate score based on use case requirements."""
        if use_case == "speed":
            # Prioritize speed over quality
            speed_score = min(result["tokens_per_second"] / 50, 1.0)
            return speed_score * 0.8 + 0.2  # Base quality score
        
        elif use_case == "quality":
            # Prioritize quality over speed
            # This would need quality evaluation (BLEU, human eval, etc.)
            quality_score = 0.8  # Placeholder
            speed_penalty = max(0, (30 - result["tokens_per_second"]) / 30 * 0.2)
            return quality_score - speed_penalty
        
        else:  # balanced
            speed_score = min(result["tokens_per_second"] / 40, 1.0)
            quality_score = 0.7  # Placeholder
            return (speed_score + quality_score) / 2

# Usage
optimizer = InferenceOptimizer()

sample_prompts = [
    "Explain quantum computing briefly",
    "Summarize the main points of artificial intelligence",
    "What are the benefits of renewable energy?"
]

best_params, score = optimizer.optimize_parameters(
    model_id="llama-3.2-3b-instruct",
    use_case="speed",
    sample_prompts=sample_prompts
)

print(f"Optimal parameters for speed use case:")
print(f"  Temperature: {best_params['temperature']}")
print(f"  Top-p: {best_params['top_p']}")
print(f"  Top-k: {best_params['top_k']}")
print(f"  Context ratio: {best_params['context_ratio']}")
print(f"  Score: {score:.3f}")
```

## 🏗️ Architectural Optimization

### Connection Pooling

Optimize LM Studio connections:

```python
from lmstrix.utils.connection_pool import ConnectionPool
import asyncio
from contextlib import asynccontextmanager

class OptimizedLMStudioClient:
    def __init__(self, max_connections=10, connection_timeout=30):
        self.connection_pool = ConnectionPool(
            base_url="http://localhost:1234",
            max_connections=max_connections,
            connection_timeout=connection_timeout,
            keepalive_timeout=300
        )
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection from pool with automatic cleanup."""
        connection = await self.connection_pool.acquire()
        try:
            yield connection
        finally:
            await self.connection_pool.release(connection)
    
    async def parallel_inference(self, requests):
        """Process multiple inference requests in parallel."""
        async def process_request(request):
            async with self.get_connection() as conn:
                return await conn.infer(**request)
        
        # Process requests concurrently
        tasks = [process_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results

# Usage
client = OptimizedLMStudioClient(max_connections=5)

# Process multiple requests efficiently
requests = [
    {"model_id": "llama-3.2-3b-instruct", "prompt": "Question 1"},
    {"model_id": "llama-3.2-3b-instruct", "prompt": "Question 2"},
    {"model_id": "mistral-7b-instruct", "prompt": "Question 3"}
]

results = await client.parallel_inference(requests)
```

### Request Batching

Implement intelligent request batching:

```python
from lmstrix.utils.batch_processor import BatchProcessor
import asyncio
from collections import defaultdict

class IntelligentBatcher:
    def __init__(self, batch_size=5, batch_timeout=1.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = defaultdict(list)
        self.batch_timers = {}
    
    async def add_request(self, model_id, request):
        """Add request to batch queue."""
        request_id = self.generate_request_id()
        future = asyncio.Future()
        
        # Add to pending batch
        self.pending_requests[model_id].append({
            "request_id": request_id,
            "request": request,
            "future": future
        })
        
        # Start batch timer if first request for this model
        if len(self.pending_requests[model_id]) == 1:
            self.batch_timers[model_id] = asyncio.create_task(
                self.batch_timeout_handler(model_id)
            )
        
        # Process batch if size limit reached
        if len(self.pending_requests[model_id]) >= self.batch_size:
            await self.process_batch(model_id)
        
        return await future
    
    async def batch_timeout_handler(self, model_id):
        """Handle batch timeout."""
        await asyncio.sleep(self.batch_timeout)
        if model_id in self.pending_requests and self.pending_requests[model_id]:
            await self.process_batch(model_id)
    
    async def process_batch(self, model_id):
        """Process accumulated batch for model."""
        if model_id not in self.pending_requests:
            return
        
        batch = self.pending_requests[model_id]
        if not batch:
            return
        
        # Clear pending requests
        self.pending_requests[model_id] = []
        
        # Cancel timeout timer
        if model_id in self.batch_timers:
            self.batch_timers[model_id].cancel()
            del self.batch_timers[model_id]
        
        # Process batch
        try:
            results = await self.execute_batch(model_id, batch)
            
            # Resolve futures with results
            for item, result in zip(batch, results):
                item["future"].set_result(result)
                
        except Exception as e:
            # Resolve futures with exception
            for item in batch:
                item["future"].set_exception(e)
    
    async def execute_batch(self, model_id, batch):
        """Execute batch of requests."""
        # Combine prompts for batch processing
        combined_requests = [item["request"] for item in batch]
        
        # Process using connection pool
        async with self.get_connection() as conn:
            results = await conn.batch_infer(model_id, combined_requests)
        
        return results
```

### Caching Strategy

Implement multi-level caching:

```python
from lmstrix.utils.cache import MultiLevelCache
import hashlib
import json

class InferenceCache:
    def __init__(self):
        self.l1_cache = {}  # In-memory cache
        self.l2_cache = MultiLevelCache(
            redis_url="redis://localhost:6379",
            disk_cache_dir="~/.lmstrix/cache",
            max_memory_size_mb=512,
            max_disk_size_gb=5
        )
    
    def generate_cache_key(self, model_id, prompt, params):
        """Generate deterministic cache key."""
        cache_data = {
            "model_id": model_id,
            "prompt": prompt,
            "params": sorted(params.items())
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    async def get_cached_result(self, model_id, prompt, params):
        """Try to get result from cache."""
        cache_key = self.generate_cache_key(model_id, prompt, params)
        
        # Try L1 cache first (fastest)
        if cache_key in self.l1_cache:
            return self.l1_cache[cache_key]
        
        # Try L2 cache (Redis/Disk)
        result = await self.l2_cache.get(cache_key)
        if result:
            # Populate L1 cache
            self.l1_cache[cache_key] = result
            return result
        
        return None
    
    async def cache_result(self, model_id, prompt, params, result):
        """Cache inference result."""
        cache_key = self.generate_cache_key(model_id, prompt, params)
        
        # Cache in both levels
        self.l1_cache[cache_key] = result
        await self.l2_cache.set(cache_key, result, ttl=3600)  # 1 hour TTL
        
        # Implement LRU eviction for L1 cache
        if len(self.l1_cache) > 1000:
            # Remove oldest 20% of entries
            oldest_keys = list(self.l1_cache.keys())[:200]
            for key in oldest_keys:
                del self.l1_cache[key]

# Integration with inference manager
class CachedInferenceManager(InferenceManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = InferenceCache()
    
    async def infer(self, **kwargs):
        """Inference with caching."""
        # Extract cache-relevant parameters
        cache_params = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "top_k": kwargs.get("top_k", -1),
            "out_ctx": kwargs.get("out_ctx", "auto")
        }
        
        # Try cache first
        cached_result = await self.cache.get_cached_result(
            kwargs["model_id"],
            kwargs["prompt"],
            cache_params
        )
        
        if cached_result:
            return cached_result
        
        # Cache miss - perform inference
        result = await super().infer(**kwargs)
        
        # Cache successful results
        if result["succeeded"]:
            await self.cache.cache_result(
                kwargs["model_id"],
                kwargs["prompt"],
                cache_params,
                result
            )
        
        return result
```

## 📈 Monitoring and Observability

### Performance Monitoring

Comprehensive performance tracking:

```python
from lmstrix.utils.monitoring import PerformanceMonitor
import time
import psutil
import GPUtil

class ComprehensiveMonitor:
    def __init__(self):
        self.metrics = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_inference_time": 0,
            "response_times": [],
            "memory_usage": [],
            "gpu_usage": []
        }
        
        self.start_time = time.time()
    
    def record_inference(self, request, result):
        """Record inference metrics."""
        self.metrics["requests"] += 1
        
        if result["succeeded"]:
            self.metrics["successful_requests"] += 1
            self.metrics["total_tokens"] += result["tokens_used"]
            self.metrics["total_inference_time"] += result["inference_time"]
            self.metrics["response_times"].append(result["inference_time"])
        else:
            self.metrics["failed_requests"] += 1
        
        # Record system metrics
        self.record_system_metrics()
    
    def record_system_metrics(self):
        """Record system resource usage."""
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics["memory_usage"].append({
            "timestamp": time.time(),
            "used_mb": memory.used / 1024 / 1024,
            "available_mb": memory.available / 1024 / 1024,
            "percent": memory.percent
        })
        
        # GPU usage (if available)
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpu_data = {
                    "gpu_id": i,
                    "timestamp": time.time(),
                    "utilization": gpu.load * 100,
                    "memory_used_mb": gpu.memoryUsed,
                    "memory_total_mb": gpu.memoryTotal,
                    "temperature": gpu.temperature
                }
                self.metrics["gpu_usage"].append(gpu_data)
        except:
            pass  # No GPU monitoring if not available
    
    def get_performance_summary(self):
        """Generate performance summary."""
        uptime = time.time() - self.start_time
        
        # Calculate averages
        avg_response_time = (
            sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            if self.metrics["response_times"] else 0
        )
        
        success_rate = (
            self.metrics["successful_requests"] / self.metrics["requests"]
            if self.metrics["requests"] > 0 else 0
        )
        
        requests_per_second = self.metrics["requests"] / uptime
        tokens_per_second = self.metrics["total_tokens"] / uptime
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.metrics["requests"],
            "success_rate": success_rate,
            "requests_per_second": requests_per_second,
            "tokens_per_second": tokens_per_second,
            "avg_response_time": avg_response_time,
            "total_tokens_processed": self.metrics["total_tokens"],
            "current_memory_usage": self.get_current_memory_usage(),
            "current_gpu_usage": self.get_current_gpu_usage()
        }
    
    def get_current_memory_usage(self):
        """Get current memory usage."""
        memory = psutil.virtual_memory()
        return {
            "used_mb": memory.used / 1024 / 1024,
            "available_mb": memory.available / 1024 / 1024,
            "percent": memory.percent
        }
    
    def get_current_gpu_usage(self):
        """Get current GPU usage."""
        try:
            gpus = GPUtil.getGPUs()
            return [{
                "gpu_id": i,
                "utilization": gpu.load * 100,
                "memory_used_mb": gpu.memoryUsed,
                "memory_total_mb": gpu.memoryTotal,
                "temperature": gpu.temperature
            } for i, gpu in enumerate(gpus)]
        except:
            return []

# Usage
monitor = ComprehensiveMonitor()

# Record inference
request = {"model_id": "llama-3.2-3b-instruct", "prompt": "Test"}
result = manager.infer(**request)
monitor.record_inference(request, result)

# Get performance summary
summary = monitor.get_performance_summary()
print(f"RPS: {summary['requests_per_second']:.2f}")
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Avg response time: {summary['avg_response_time']:.2f}s")
```

### Alerting System

Implement performance alerting:

```python
from lmstrix.utils.alerts import AlertManager
import smtplib
from email.mime.text import MIMEText

class PerformanceAlerts:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.thresholds = {
            "max_response_time": 30.0,      # seconds
            "min_success_rate": 0.95,       # 95%
            "max_memory_usage": 0.85,       # 85%
            "min_tokens_per_second": 20.0,  # TPS
            "max_gpu_temperature": 80.0     # Celsius
        }
        
        self.alert_cooldown = 300  # 5 minutes between same alerts
        self.last_alerts = {}
    
    def check_performance_thresholds(self, metrics):
        """Check if any performance thresholds are exceeded."""
        alerts = []
        
        # Response time alert
        if metrics.get("avg_response_time", 0) > self.thresholds["max_response_time"]:
            alerts.append({
                "type": "high_response_time",
                "severity": "warning",
                "message": f"Average response time {metrics['avg_response_time']:.2f}s exceeds threshold {self.thresholds['max_response_time']}s",
                "value": metrics["avg_response_time"],
                "threshold": self.thresholds["max_response_time"]
            })
        
        # Success rate alert
        if metrics.get("success_rate", 1.0) < self.thresholds["min_success_rate"]:
            alerts.append({
                "type": "low_success_rate",
                "severity": "critical",
                "message": f"Success rate {metrics['success_rate']:.1%} below threshold {self.thresholds['min_success_rate']:.1%}",
                "value": metrics["success_rate"],
                "threshold": self.thresholds["min_success_rate"]
            })
        
        # Memory usage alert
        memory_usage = metrics.get("current_memory_usage", {}).get("percent", 0) / 100
        if memory_usage > self.thresholds["max_memory_usage"]:
            alerts.append({
                "type": "high_memory_usage",
                "severity": "warning",
                "message": f"Memory usage {memory_usage:.1%} exceeds threshold {self.thresholds['max_memory_usage']:.1%}",
                "value": memory_usage,
                "threshold": self.thresholds["max_memory_usage"]
            })
        
        # Throughput alert
        if metrics.get("tokens_per_second", 0) < self.thresholds["min_tokens_per_second"]:
            alerts.append({
                "type": "low_throughput",
                "severity": "warning",
                "message": f"Throughput {metrics['tokens_per_second']:.1f} TPS below threshold {self.thresholds['min_tokens_per_second']} TPS",
                "value": metrics["tokens_per_second"],
                "threshold": self.thresholds["min_tokens_per_second"]
            })
        
        # GPU temperature alerts
        for gpu in metrics.get("current_gpu_usage", []):
            if gpu["temperature"] > self.thresholds["max_gpu_temperature"]:
                alerts.append({
                    "type": "high_gpu_temperature",
                    "severity": "critical",
                    "message": f"GPU {gpu['gpu_id']} temperature {gpu['temperature']}°C exceeds threshold {self.thresholds['max_gpu_temperature']}°C",
                    "value": gpu["temperature"],
                    "threshold": self.thresholds["max_gpu_temperature"]
                })
        
        # Send alerts (with cooldown)
        for alert in alerts:
            self.send_alert_if_needed(alert)
        
        return alerts
    
    def send_alert_if_needed(self, alert):
        """Send alert if cooldown period has passed."""
        current_time = time.time()
        alert_key = f"{alert['type']}_{alert.get('gpu_id', '')}"
        
        # Check cooldown
        if alert_key in self.last_alerts:
            if current_time - self.last_alerts[alert_key] < self.alert_cooldown:
                return  # Still in cooldown
        
        # Send alert
        self.send_alert(alert)
        self.last_alerts[alert_key] = current_time
    
    def send_alert(self, alert):
        """Send alert notification."""
        # Email notification
        self.send_email_alert(alert)
        
        # Log alert
        self.log_alert(alert)
        
        # Webhook notification (if configured)
        self.send_webhook_alert(alert)
    
    def send_email_alert(self, alert):
        """Send email alert."""
        # Email configuration would be loaded from config
        email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@yourcompany.com",
            "password": "your-password",
            "recipients": ["admin@yourcompany.com"]
        }
        
        subject = f"LMStrix Alert: {alert['type'].replace('_', ' ').title()}"
        body = f"""
        Alert: {alert['message']}
        
        Severity: {alert['severity']}
        Current Value: {alert['value']}
        Threshold: {alert['threshold']}
        Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send email (simplified)
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['recipients'])
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
```

## 🏭 Production Deployment

### Production Configuration

Optimize for production environments:

```python
# production_config.py
PRODUCTION_CONFIG = {
    "lmstudio": {
        "base_url": "http://lmstudio-server:1234",
        "timeout": 300,
        "connect_timeout": 30,
        "max_retries": 5,
        "retry_delay": 2.0,
        "connection_pool_size": 20
    },
    
    "performance": {
        "enable_caching": True,
        "cache_ttl": 3600,
        "batch_size": 10,
        "batch_timeout": 1.0,
        "max_concurrent_requests": 50,
        "request_queue_size": 1000
    },
    
    "monitoring": {
        "enable_metrics": True,
        "metrics_interval": 60,
        "enable_alerts": True,
        "alert_cooldown": 300,
        "log_level": "INFO"
    },
    
    "safety": {
        "max_context_threshold": 65536,
        "memory_usage_limit": 0.8,
        "enable_graceful_degradation": True,
        "fallback_models": ["llama-3.2-3b-instruct"],
        "circuit_breaker_threshold": 0.5
    }
}
```

### Load Balancing

Implement load balancing across multiple LM Studio instances:

```python
from lmstrix.utils.load_balancer import LoadBalancer
import random
import asyncio

class LMStudioLoadBalancer:
    def __init__(self, servers):
        self.servers = servers
        self.server_health = {server: True for server in servers}
        self.server_metrics = {server: {"requests": 0, "avg_response_time": 0} for server in servers}
        self.health_check_interval = 30  # seconds
        
        # Start health checking
        asyncio.create_task(self.health_check_loop())
    
    async def select_server(self, request):
        """Select optimal server for request."""
        healthy_servers = [s for s in self.servers if self.server_health[s]]
        
        if not healthy_servers:
            raise Exception("No healthy servers available")
        
        # Load balancing strategy: least connections
        selected_server = min(
            healthy_servers,
            key=lambda s: self.server_metrics[s]["requests"]
        )
        
        return selected_server
    
    async def execute_request(self, request):
        """Execute request with load balancing."""
        server = await self.select_server(request)
        
        # Track request
        self.server_metrics[server]["requests"] += 1
        
        try:
            # Execute request
            start_time = time.time()
            result = await self.send_request_to_server(server, request)
            response_time = time.time() - start_time
            
            # Update metrics
            self.update_server_metrics(server, response_time, success=True)
            return result
            
        except Exception as e:
            # Update metrics
            self.update_server_metrics(server, 0, success=False)
            
            # Try another server if available
            healthy_servers = [s for s in self.servers if self.server_health[s] and s != server]
            if healthy_servers:
                return await self.execute_request(request)
            
            raise e
        finally:
            # Decrement request count
            self.server_metrics[server]["requests"] -= 1
    
    def update_server_metrics(self, server, response_time, success):
        """Update server performance metrics."""
        metrics = self.server_metrics[server]
        
        if success:
            # Update rolling average response time
            current_avg = metrics["avg_response_time"]
            metrics["avg_response_time"] = (current_avg * 0.9) + (response_time * 0.1)
        else:
            # Mark server as potentially unhealthy after failures
            # (health check will verify)
            pass
    
    async def health_check_loop(self):
        """Continuously check server health."""
        while True:
            await asyncio.sleep(self.health_check_interval)
            await self.check_all_servers_health()
    
    async def check_all_servers_health(self):
        """Check health of all servers."""
        for server in self.servers:
            try:
                # Simple health check
                response = await self.send_health_check(server)
                self.server_health[server] = response.get("healthy", False)
            except:
                self.server_health[server] = False
```

### Auto-Scaling

Implement auto-scaling based on load:

```python
from lmstrix.utils.autoscaler import AutoScaler

class LMStrixAutoScaler:
    def __init__(self):
        self.min_instances = 1
        self.max_instances = 10
        self.current_instances = 1
        self.scale_up_threshold = 0.8    # CPU usage
        self.scale_down_threshold = 0.3
        self.scale_cooldown = 300        # 5 minutes
        self.last_scale_action = 0
    
    async def monitor_and_scale(self):
        """Monitor metrics and scale as needed."""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_scale_action < self.scale_cooldown:
            return
        
        # Get current metrics
        metrics = await self.get_current_metrics()
        
        # Scaling decisions
        if metrics["cpu_usage"] > self.scale_up_threshold and metrics["queue_length"] > 10:
            if self.current_instances < self.max_instances:
                await self.scale_up()
                self.last_scale_action = current_time
        
        elif metrics["cpu_usage"] < self.scale_down_threshold and metrics["queue_length"] == 0:
            if self.current_instances > self.min_instances:
                await self.scale_down()
                self.last_scale_action = current_time
    
    async def scale_up(self):
        """Add new instance."""
        print(f"Scaling up from {self.current_instances} to {self.current_instances + 1} instances")
        
        # Start new LM Studio instance (implementation depends on deployment)
        new_instance = await self.start_new_instance()
        
        if new_instance:
            self.current_instances += 1
            # Add to load balancer
            load_balancer.add_server(new_instance)
    
    async def scale_down(self):
        """Remove instance."""
        print(f"Scaling down from {self.current_instances} to {self.current_instances - 1} instances")
        
        # Remove least used instance
        instance_to_remove = await self.select_instance_to_remove()
        
        if instance_to_remove:
            # Gracefully drain requests
            await self.drain_instance(instance_to_remove)
            
            # Remove from load balancer
            load_balancer.remove_server(instance_to_remove)
            
            # Stop instance
            await self.stop_instance(instance_to_remove)
            
            self.current_instances -= 1
```

## 🔍 Performance Optimization Checklist

### Pre-Production Checklist

- [ ] **Model Selection Optimized**
  - [ ] Tested all available models for use case
  - [ ] Selected optimal model for performance/quality trade-off
  - [ ] Documented model performance characteristics

- [ ] **Context Limits Tested**
  - [ ] Ran comprehensive context testing
  - [ ] Set appropriate safety thresholds
  - [ ] Documented optimal context sizes

- [ ] **Parameters Optimized**
  - [ ] Tuned temperature, top_p, top_k for use case
  - [ ] Optimized output token allocation
  - [ ] Tested parameter combinations

- [ ] **Infrastructure Optimized**
  - [ ] Configured connection pooling
  - [ ] Implemented request batching
  - [ ] Set up multi-level caching
  - [ ] Configured load balancing

- [ ] **Monitoring Implemented**
  - [ ] Performance metrics collection
  - [ ] Alert thresholds configured
  - [ ] Health check endpoints
  - [ ] Resource usage monitoring

- [ ] **Fallback Strategies**
  - [ ] Circuit breaker implemented
  - [ ] Graceful degradation configured
  - [ ] Fallback models identified
  - [ ] Error handling optimized

### Production Monitoring

```bash
# Key metrics to monitor
curl http://lmstrix-api/metrics | jq '{
  "requests_per_second": .requests_per_second,
  "average_response_time": .avg_response_time,
  "success_rate": .success_rate,
  "tokens_per_second": .tokens_per_second,
  "memory_usage_percent": .memory_usage_percent,
  "active_models": .active_models,
  "queue_length": .queue_length
}'
```

## 🚀 Next Steps

With performance optimization mastered:

- **Monitor Production** - Continuously track performance metrics
- **Iterate and Improve** - Regular optimization based on real usage
- **Scale Strategically** - Plan for growth and increased load
- **Stay Updated** - Keep up with LMStrix and model improvements

---

*Performance optimization mastered! Deploy with confidence! 🏭*