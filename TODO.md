# LMStrix TODO List

### Recently Completed ✅

- [x] Add --prompt parameter to test command for custom prompts
- [x] Add --file_prompt parameter to test command for loading prompts from files
- [x] Update ContextTester and InferenceEngine to support custom prompts
- [x] Update help documentation with custom prompt examples
- [x] Implement compact output for test command with live-updating tables
- [x] Add progress tracking for batch tests with --all flag
- [x] Maintain backward compatibility with verbose mode

### Issue #302: Inference Output Mismatch (PRIORITY)

- [ ] Compare output with LM Studio for identical prompts
- [ ] Ensure token counts match between lmstrix and LM Studio
- [ ] Verify translation quality matches expected output
- [ ] Create regression test for this issue
- [ ] Fix maxTokens calculation issue
- [ ] Investigate stop token configuration differences
- [ ] Fix context length handling (GUI uses 131072, CLI uses 65536)

### Model Loading Optimization (Medium Priority)

- [ ] Improve model reuse detection to avoid unnecessary loading messages
- [ ] Add context length display in enhanced logging when available
- [ ] Optimize model loading workflow for better performance
- [ ] Add better feedback when models are being reused vs loaded fresh

## Phase A: Core Simplification

### Configuration Unification

- [ ] Create utils/config.py for centralized configuration handling
- [ ] Consolidate path handling functions (get_lmstudio_path, etc.)
- [ ] Remove redundant configuration code
- [ ] Update all imports to use centralized config

### Error Handling Standardization

- [ ] Review and simplify custom exception hierarchy
- [ ] Standardize error messages across codebase
- [ ] Implement consistent logging patterns
- [ ] Update error handling to use standard exceptions where appropriate

### Code Quality Improvements

- [ ] Add comprehensive type hints to public APIs
- [ ] Ensure all functions have proper docstrings
- [ ] Remove deprecated TODO comments from code
- [ ] Run code quality checks and fix issues

## Phase B: CLI Enhancement

### Command Improvements

- [ ] Enhance `scan` command with better progress reporting
- [ ] Improve `list` command with filtering and sorting options
- [ ] Add `reset` command for clearing model test data
- [ ] Add `health` command for system diagnostics

### User Experience

- [ ] Better error messages with helpful suggestions
- [ ] Improved help text and documentation
- [ ] Enhanced progress indicators for long-running operations
- [ ] Add command aliases for common operations

## Phase C: Testing & Documentation

### Test Suite Completion

- [ ] Ensure >90% test coverage maintained
- [ ] Add integration tests for new features
- [ ] Performance benchmarking of improvements
- [ ] Add regression tests for fixed issues

### Documentation Updates

- [ ] Update README.md with latest features
- [ ] Create comprehensive CLI reference
- [ ] Update examples to demonstrate new capabilities
- [ ] Create migration guide for any breaking changes

## Technical Debt Reduction

### Code Architecture

- [ ] Review and simplify InferenceManager class structure
- [ ] Consolidate duplicate logic across modules
- [ ] Improve separation of concerns between CLI and core logic
- [ ] Refactor overly complex functions

### Performance Optimization

- [ ] Profile model loading and caching behavior
- [ ] Optimize JSON registry read/write operations
- [ ] Reduce memory usage in context testing
- [ ] Benchmark before/after performance improvements

### Dependency Management

- [ ] Review and minimize external dependencies
- [ ] Ensure compatibility with latest Python versions
- [ ] Update build and packaging configuration
- [ ] Test installation on clean environments

## Quality Assurance

### Testing

- [ ] Run full test suite on all changes
- [ ] Test CLI commands with various model types
- [ ] Verify backward compatibility
- [ ] Performance regression testing

### Documentation

- [ ] Update CHANGELOG.md with all changes
- [ ] Review and update docstrings
- [ ] Ensure examples work correctly
- [ ] Update any configuration documentation

### Release Preparation

- [ ] Version bump and release notes
- [ ] Tag release in git
- [ ] Test PyPI package build
- [ ] Verify clean installation works

