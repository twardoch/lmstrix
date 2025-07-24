# LMStrix Development Plan - v1.0 Next Steps

## 1. Project Vision & Status

**Vision**: Deliver a reliable, installable tool that solves the critical problem of models in LM Studio declaring false context limits. The tool provides automated discovery of true operational context limits.

**Current Status**: The core functionality is complete. The project has been successfully refactored to use the native `lmstudio` package for all model interactions, and all data is stored in the correct, centralized location. The CLI and Python API are functional.

The immediate next steps are to build a comprehensive test suite to ensure reliability and to prepare the package for its initial public release.

## 2. Phase 2: Testing & Quality Assurance

This phase focuses on ensuring the existing codebase is robust, reliable, and free of bugs.

### 2.1. Unit & Integration Testing
**Goal**: Achieve comprehensive test coverage for all critical components.

- **Testing Framework**: Tests will be implemented using `pytest`.
- **Mocking**: The `pytest-mock` library will be used to create a mock of the `lmstudio` package. This allows for testing the application's logic without needing a live LM Studio instance, ensuring that tests are fast, repeatable, and can run in any environment (like a CI/CD pipeline).

- **Test Implementation Plan**:

  - **`tests/core/test_context_tester.py`**: 
    - Create a `test_binary_search_logic` function that uses a mocked `lmstudio` client.
    - The mock will simulate different scenarios: a model that loads and passes inference at certain context sizes but fails at others.
    - Assert that the `find_max_working_context` method correctly identifies the highest passing context size.
    - Test edge cases: a model that never loads, a model that loads but always fails inference, and a model that works at all tested sizes.

  - **`tests/loaders/test_model_loader.py`**:
    - Mock the `lmstudio.list_downloaded_models` function to return a predefined list of model dictionaries.
    - Test the `scan_and_update_registry` function.
    - Assert that new models are added, existing models are updated (without overwriting test results), and deleted models are removed from the registry.

  - **`tests/utils/test_paths.py`**:
    - Mock the `Path.home()` and `Path.exists()` methods.
    - Test the `get_lmstudio_path` function to ensure it correctly finds the path from the `.lmstudio-home-pointer` file.
    - Test the fallback logic to common directories if the pointer file does not exist.
    - Assert that `get_default_models_file` returns the correct `lmstrix.json` path.

## 3. Phase 3: Documentation & Release

**Goal**: Prepare the project for a successful v1.0.0 release on PyPI.

### 3.1. Documentation
- **`README.md`**: Update the README to include a clear, concise quick-start guide, installation instructions, and examples for the new CLI commands (`scan`, `test`, `list`).
- **API Documentation**: Add comprehensive docstrings to all public functions and classes, explaining their purpose, arguments, and return values.

### 3.2. Packaging & Release
- **`pyproject.toml`**: Verify that all dependencies, project metadata (version, author, license), and entry points are correct.
- **PyPI Release**: Once testing and documentation are complete, the project will be built and published to PyPI, making it installable via `pip install lmstrix`.
