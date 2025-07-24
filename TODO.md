# TODO List for LMStrix v1.0 Release

## Phase 2: Testing & Quality Assurance

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
