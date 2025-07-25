---
layout: default
title: API Reference
---

## Python API Reference

This section provides a detailed reference for the LMStrix Python API.

### The `LMStrix` Class

The main entry point for interacting with the API.

`LMStrix(base_uri: str = "http://localhost:1234/v1")`

- `base_uri`: The base URI of the LM Studio server.

#### Methods

- `async scan_models()`: Scans for available models in LM Studio and updates the local model registry.
- `async list_models()`: Returns a list of `Model` objects from the local registry.
- `async test_model(model_id: str)`: Tests the context limit of a specific model and updates the registry with the result.
- `async infer(prompt: str, model_id: str, **kwargs)`: Runs inference on a model. Any additional keyword arguments are passed to the `complete()` method of the `lmstudio` client.

### The `Model` Class

Represents a model in LM Studio.

#### Attributes

- `id`: The model ID (e.g., `lmstudio-community/gemma-2b-it-GGUF`).
- `context_limit`: The declared context limit of the model, as reported by LM Studio.
- `tested_max_context`: The empirically tested maximum context limit that the model can handle on your machine. `None` if the model has not been tested.
- `context_test_status`: The status of the context test. Can be one of `"passed"`, `"failed"`, or `"not_tested"`.

### The `InferenceResponse` Class

Represents the response from an inference request.

#### Attributes

- `content`: The text content of the model's response.
- `usage`: A dictionary containing token usage information, e.g., `{'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30}`.
