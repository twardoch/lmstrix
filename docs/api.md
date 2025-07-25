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

- `async scan_models()`: Scans for available models in LM Studio.
- `async list_models()`: Returns a list of `Model` objects.
- `async test_model(model_id: str)`: Tests the context limit of a specific model.
- `async infer(prompt: str, model_id: str, **kwargs)`: Runs inference on a model.

### The `Model` Class

Represents a model in LM Studio.

#### Attributes

- `id`: The model ID.
- `context_limit`: The declared context limit of the model.
- `tested_max_context`: The tested maximum context limit.
- `context_test_status`: The status of the context test.

### The `InferenceResponse` Class

Represents the response from an inference request.

#### Attributes

- `content`: The content of the response.
- `usage`: A dictionary containing token usage information.
