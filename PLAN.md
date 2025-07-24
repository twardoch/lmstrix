# LMStrix Development Plan - v1.0 Pivot to Native `lmstudio`

## 1. Project Pivot: From `litellm` to `lmstudio`

**Vision**: LMStrix v1.0 will be a minimal viable product focused on solving the critical problem with LM Studio: many models falsely declare higher maximum context lengths than they can actually handle.

**Core Problem**: LM Studio models often declare context limits (e.g., 128k tokens) that fail in practice. Models may fail to load, produce gibberish, or only work correctly below a certain "real" max context.

**Strategic Change**: The initial v0.1.0 implementation relied on `litellm` for API interaction. Based on performance and reliability issues (see `issues/101.txt`), this plan outlines a pivot to using the native `lmstudio` Python package directly for all model interactions. This provides a more robust and direct integration with LM Studio.

## 2. Core Technical Approach: Native Integration

All core functionality will be built directly on top of the `lmstudio` Python package. This completely removes the `litellm` dependency.

- **Model Discovery**: `lmstudio.list_downloaded_models()`
- **Model Loading/Unloading**: `lmstudio.llm()` and `llm.unload()`
- **Model Information**: `llm.get_info()`
- **Inference**: `llm.complete()`
- **Configuration**: Model loading will be configured with `config={"context_length": size}`.

## 3. Phase 1: Refactoring and MVP Feature Implementation

This phase focuses on replacing the existing `litellm`-based implementation and completing the core features for the MVP.

### 3.1. Foundational Refactoring
**Goal**: Replace all `litellm` functionality with the `lmstudio` package.

- **Dependency Management**: Remove `litellm` from `pyproject.toml`.
- **API Client**: Rewrite `src/lmstrix/api/client.py` to be a thin wrapper around the `lmstudio` package's functions.
- **Inference Engine**: Update `src/lmstrix/core/inference.py` to use the new client and `llm.complete()`.
- **Context Testing**: Update `src/lmstrix/core/context_tester.py` to use `lmstudio.llm()` for loading models with specific context sizes and `llm.unload()` for cleanup.

### 3.2. Model Discovery & Registry
**Goal**: Reliable model discovery and metadata storage.

- **Scanner**: Use `lmstudio.list_downloaded_models()` to discover all models.
- **Metadata**: Use `llm.get_info()` to extract detailed and accurate model metadata.
- **Registry**: Create/update a `models.json` registry file.
- **Storage**: Store all data (`models.json`, logs) in a dedicated `lmstrix` folder within the LM Studio application data directory to avoid cluttering the project.

### 3.3. Context Validation System
**Goal**: Automatically discover the true operational context limit for each model.

- **Test Procedure**:
    1. For a given model, use a binary search algorithm between a minimum (e.g., 2048) and the model's declared maximum context length.
    2. In each step, attempt to load the model using `lmstudio.llm(model_id, config={"context_length": current_size})`.
    3. If loading succeeds, perform a simple "needle in a haystack" test: run inference with a prompt that requires recalling a specific piece of information. A simple "2+2=" -> "4" check is a good start.
    4. If the test passes, this context size is considered valid. The search continues for a higher valid size.
    5. The highest context size that both loads and passes the inference test is recorded as the `tested_max_context`.
    6. The model is unloaded using `llm.unload()` after each test to free up system resources.
- **Logging**: Log the entire test procedure for each model to `{model_id}_context_test.log`, recording context size, load success, and inference success/failure.
- **Results**: Store the final `tested_max_context` and a `context_test_status` (e.g., `untested`, `passed`, `failed`) in the `models.json` registry.

### 3.4. CLI and Python API
**Goal**: Provide simple and effective interfaces for users.

- **CLI Commands**:
    - `lmstrix scan`: Scan for models and update the registry.
    - `lmstrix list`: List all models, showing their declared vs. tested context limits and test status.
    - `lmstrix test <model_id|--all>`: Run the context validation test on a specific model or all untested models.
    - `lmstrix status`: Show a summary of testing progress.
- **Python API**:
    - `lmstrix.list_models()`: Returns a list of `Model` objects.
    - `lmstrix.test_context(model_id)`: Runs the validation test for a model.
    - `lmstrix.get_model(model_id)`: Retrieves a model with its tested metadata.

## 4. Phase 2: Testing, Documentation, and Release

### 4.1. Testing
- **Unit Tests**: Cover the core logic for the binary search algorithm, response validation, and registry management.
- **Integration Tests**: Write tests that use a mock of the `lmstudio` package to simulate end-to-end workflows without requiring a live LM Studio instance.

### 4.2. Documentation
- Update `README.md` to reflect the new `lmstudio`-based approach and remove mentions of `litellm`.
- Create a clear guide on the context testing methodology.
- Document the CLI commands and Python API.

### 4.3. Release
- Ensure `pyproject.toml` is complete and accurate.
- Publish v1.0.0 to PyPI.

## 5. Out of Scope for v1.0

- Advanced context optimization algorithms (beyond the binary search validation).
- Streaming support, multi-model workflows, GUI/web interface.
