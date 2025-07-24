# LMStrix Test Suite

## Overview

The LMStrix test suite provides comprehensive coverage for all modules using pytest. The tests are organized into unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── run_tests.py             # Simple test runner script
├── test_api/                # API layer tests
│   ├── test_client.py       # LMStudioClient tests
│   └── test_exceptions.py   # Custom exception tests
├── test_core/               # Core module tests
│   ├── test_context_tester.py  # Context optimization tests
│   ├── test_inference.py    # Inference engine tests
│   ├── test_models.py       # Model and registry tests
│   ├── test_prompts.py      # Prompt resolution tests
│   └── test_scanner.py      # Model scanner tests
├── test_loaders/            # Loader tests
│   ├── test_context_loader.py   # Context file loading tests
│   ├── test_model_loader.py     # Model loader tests
│   └── test_prompt_loader.py    # Prompt loader tests
├── test_utils/              # Utility tests
│   └── test_paths.py        # Path utility tests
├── test_integration/        # Integration tests
│   └── test_cli_integration.py  # CLI integration tests
└── test_e2e/                # End-to-end tests (to be added)
```

## Running Tests

### Install Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_api/test_exceptions.py
```

### Run with Coverage
```bash
pytest --cov=src/lmstrix --cov-report=html
```

### Run Only Unit Tests
```bash
pytest -m "not integration"
```

## Key Test Features

### 1. Comprehensive Mocking
- All external dependencies (LM Studio API, file system) are mocked
- Tests run independently without requiring LM Studio installation

### 2. Async Test Support
- Uses pytest-asyncio for testing async methods
- Proper async fixtures and test decorators

### 3. Fixture Organization
- Common fixtures in conftest.py
- Mock data for models, prompts, and contexts
- Temporary directories for file operations

### 4. Test Categories

#### Unit Tests
- Test individual classes and functions in isolation
- Mock all external dependencies
- Fast execution
- High code coverage

#### Integration Tests
- Test interaction between modules
- Mock only external services (LM Studio API)
- Verify end-to-end workflows

#### End-to-End Tests (Planned)
- Test complete user scenarios
- May require actual LM Studio instance
- Focus on context optimization workflow

## Coverage Goals

- Target: >80% code coverage
- Critical paths: 100% coverage
  - Context optimization algorithm
  - Model registry operations
  - API client error handling

## Test Examples

### Testing Context Optimization
```python
@pytest.mark.asyncio
async def test_find_optimal_context_simple(mock_client, mock_llm):
    """Test finding optimal context with simple scenario."""
    # Mock responses: succeed up to 4096, fail above
    async def mock_completion(llm, prompt, **kwargs):
        if len(prompt) <= 4096:
            return Mock(content="4")
        else:
            raise InferenceError("test-model", "Too long")
    
    mock_client.acompletion = AsyncMock(side_effect=mock_completion)
    
    tester = ContextTester(mock_client)
    model = Model(id="test-model", path="/path/to/model.gguf", 
                  size_bytes=1000000, ctx_in=8192)
    
    optimal_size, loadable_size, test_log = await tester.find_optimal_context(model)
    
    assert 3000 < optimal_size <= 4096
    assert loadable_size > optimal_size
```

### Testing Model Registry
```python
def test_registry_save_and_load(tmp_path, sample_model_data):
    """Test saving and loading models."""
    registry = ModelRegistry(tmp_path / "models.json")
    
    model = Model(**sample_model_data)
    registry.update_model("test-model", model)
    
    # Load in new registry instance
    new_registry = ModelRegistry(tmp_path / "models.json")
    
    loaded_model = new_registry.get_model("test-model")
    assert loaded_model.id == "test-model"
```

## CI/CD Integration

The test suite is designed to run in CI/CD pipelines:

1. No external dependencies required
2. All tests use mocking
3. Deterministic results
4. Fast execution (<1 minute)

## Future Enhancements

1. Add performance benchmarks
2. Add mutation testing
3. Create test data generators
4. Add property-based tests for complex algorithms
5. Integration with actual LM Studio test instance