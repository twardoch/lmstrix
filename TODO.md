# TODO List for LMStrix v1.0 Release

## Phase 2: Testing & Quality Assurance

### Functional Tests & Usage Examples (HIGH PRIORITY)
- [ ] Create `examples` directory structure with subdirectories for CLI, Python, prompts, and data.
- [ ] Write CLI usage examples:
  - [ ] `examples/cli/basic_workflow.sh` - Complete workflow demonstration
  - [ ] `examples/cli/model_testing.sh` - Context testing focused examples
  - [ ] `examples/cli/inference_examples.sh` - Various inference scenarios
- [ ] Write Python package usage examples:
  - [ ] `examples/python/basic_usage.py` - Simple API usage
  - [ ] `examples/python/advanced_testing.py` - Advanced context testing
  - [ ] `examples/python/custom_inference.py` - Custom inference workflows
  - [ ] `examples/python/batch_processing.py` - Processing multiple models
- [ ] Create sample prompt files:
  - [ ] `examples/prompts/analysis.toml` - Analysis templates
  - [ ] `examples/prompts/creative.toml` - Creative writing prompts
  - [ ] `examples/prompts/coding.toml` - Code generation prompts
  - [ ] `examples/prompts/qa.toml` - Question-answering prompts
- [ ] Create sample data files:
  - [ ] `examples/data/sample_context.txt` - Large text for context testing
  - [ ] `examples/data/test_questions.json` - Test questions for QA
- [ ] Create `examples/run_all_examples.sh` to test all examples
- [ ] Write `examples/README.md` documenting all examples

### Unit & Integration Tests
- [ ] Create `tests/core` directory.
- [ ] Create `tests/core/test_context_tester.py`.
- [ ] Implement `test_binary_search_logic` with a mocked `lmstudio` client.
- [ ] Test edge cases (model never loads, inference always fails, etc.).
- [ ] Create `tests/loaders` directory.
- [ ] Create `tests/loaders/test_model_loader.py`.
- [ ] Implement tests for `scan_and_update_registry` (add, update, remove models).
- [ ] Create `tests/utils` directory.
- [ ] Create `tests/utils/test_paths.py`.
- [ ] Implement tests for `get_lmstudio_path` and `get_default_models_file`.

### Code Quality
- [ ] Run `mypy` and fix any reported type errors.
- [ ] Run `ruff` and fix any reported linting issues.

## Phase 3: Documentation

### User Documentation
- [ ] Update `README.md` with the new CLI commands and examples.
- [ ] Add a section to the `README.md` explaining the context testing methodology.

### API Documentation
- [ ] Add comprehensive docstrings to all public functions and classes.

## Phase 4: Package & Release

### Package Preparation
- [ ] Verify all metadata in `pyproject.toml` is accurate.
- [ ] Perform a local test build and installation (`pip install .`).

### Release
- [ ] Tag the release as `v1.0.0` in git.
- [ ] Build the distribution packages (`python -m build`).
- [ ] Publish the package to PyPI.
