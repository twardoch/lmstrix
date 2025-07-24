# TODO List for LMStrix v1.0 MVP

## Phase 1: Core Functionality

### Model Discovery & Registry

- [x] Create system path detection for LM Studio data directory
- [x] Implement model scanner that finds all downloaded models
- [x] Add compatibility layer for existing lmsm.json format
- [x] Create data directory structure in LM Studio path
- [x] Implement model registry save/load with proper paths
- [x] Add model metadata extraction (size, declared context, capabilities)
- [x] Create model registry update mechanism
- [x] Add model removal detection and cleanup
- [x] Update model discovery to use lmstudio.list_downloaded_models()
- [x] Extract real model metadata using model.get_info()

### Context Validation System

- [x] Replace litellm with native lmstudio package
- [x] Update LMStudioClient to use lmstudio.llm() for model loading
- [x] Implement model loading with specific context size using config parameter
- [x] Update inference to use model.complete() instead of litellm
- [x] Add model.unload() after each test to free resources
- [x] Create context testing engine base class
- [x] Add simple prompt testing ("2+2=" -> "4")
- [x] Implement binary search for maximum loadable context
- [x] Create progressive context testing from min to max
- [x] Add response validation logic
- [ ] Implement per-model logging system
- [ ] Create log file format and structure
- [ ] Add context test status tracking
- [ ] Implement test resumption for interrupted tests
- [ ] Add tested_max_context field to model registry
- [ ] Create context test results storage

### CLI Updates

- [x] Update CLI to use new model discovery
- [x] Implement `lmstrix scan` command
- [x] Update `lmstrix list` to show context test status
- [x] Create `lmstrix test <model_id>` command
- [x] Add `lmstrix test --all` for batch testing
- [x] Create `lmstrix status` to show testing progress
- [x] Add progress bars for long operations
- [x] Implement proper error messages
- [x] Add CLI help documentation

### Python API Updates

- [x] Update LMStrix class with context testing methods
- [x] Add test_context_limits method
- [x] Create get_tested_context_limit method
- [x] Add context test status query methods
- [x] Implement async context testing support
- [x] Add batch testing capabilities
- [x] Create context test result models
- [x] Add proper exception handling

## Phase 2: Testing & Quality

### Unit Tests

- [ ] Write tests for model discovery
- [ ] Write tests for path detection logic
- [ ] Write tests for context binary search
- [ ] Write tests for response validation
- [ ] Write tests for log file handling
- [ ] Write tests for registry updates
- [ ] Write tests for CLI commands
- [ ] Write tests for error conditions

### Integration Tests

- [ ] Create mock LM Studio server
- [ ] Write end-to-end context testing tests
- [ ] Test interrupted test resumption
- [ ] Test batch model testing
- [ ] Test error recovery scenarios

### Code Quality

- [ ] Run mypy and fix type errors
- [ ] Run ruff and fix linting issues
- [ ] Add missing type hints
- [ ] Add comprehensive docstrings
- [ ] Review error handling

## Phase 3: Documentation

### User Documentation

- [ ] Update README.md with context testing features
- [ ] Write context testing methodology guide
- [ ] Create troubleshooting section
- [ ] Add common issues and solutions
- [ ] Write quick start guide

### API Documentation

- [ ] Document all CLI commands
- [ ] Document Python API methods
- [ ] Add code examples
- [ ] Create configuration guide
- [ ] Document log file format

### Examples

- [ ] Create example: Test single model
- [ ] Create example: Batch test all models
- [ ] Create example: Query test results
- [ ] Create example: Custom test prompts

## Phase 4: Package & Release

### Package Preparation

- [ ] Update pyproject.toml with all dependencies
- [ ] Add package metadata
- [ ] Include data files in package
- [ ] Test package build
- [ ] Test local installation

### Pre-release Testing

- [ ] Test on fresh Python environment
- [ ] Test on different OS platforms
- [ ] Verify all CLI commands work
- [ ] Test with real LM Studio instance
- [ ] Verify data storage locations

### Release Process

- [ ] Update version to 1.0.0
- [ ] Create git tag v1.0.0
- [ ] Build distribution packages
- [ ] Test on Test PyPI
- [ ] Publish to PyPI
- [ ] Create GitHub release
- [ ] Update documentation

## Critical Path Items

These must be completed for MVP:

1. [x] Model discovery with proper paths
2. [x] Context testing engine
3. [ ] Result logging and storage
4. [x] Basic CLI commands
5. [ ] Minimal documentation
6. [ ] Package configuration