# LMStrix TODO List

### Issue #307: Streaming Inference Support 

- [ ] Write unit tests for streaming functionality
- [ ] Write integration tests with real models
- [ ] Update documentation with streaming examples
- [ ] Performance testing: streaming vs sync comparison

### Testing and Validation

- [ ] Compare output with LM Studio for identical prompts
- [ ] Ensure token counts match between lmstrix and LM Studio
- [ ] Verify translation quality matches expected output
- [ ] Create regression test for this issue

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

## NEW DEVELOPMENT PRIORITIES

### Issue #307 - LM Studio Streaming Inference (High Priority)
- [ ] Research LM Studio SDK streaming API (`complete_stream()`, callbacks)
- [ ] Replace `llm.complete()` with `llm.complete_stream()` in `LMStudioClient.completion()`
- [ ] Implement progress callbacks: `on_prediction_fragment`, `on_first_token`
- [ ] Add no-progress timeout watchdog to abort stalled generations
- [ ] Add CLI flags: `--stream-timeout` (default 120s), `--show-progress`
- [ ] Update inference logging to show streaming status
- [ ] Implement token-by-token display in verbose mode
- [ ] Add streaming statistics (tokens/second, time to first token)
- [ ] Enable streaming cancellation via Ctrl+C
- [ ] Maintain backward compatibility with existing response format

### Issue #306 - Batch Inference Tool (Medium Priority)
- [ ] Create `_keep_this/adam/adamall.py` using lmstrix API
- [ ] Implement smart model state detection and caching
- [ ] Add pathvalidate for safe filename generation (`safe_model_id`, `safe_prompt_name`)
- [ ] Configure batch prompts: `think,aps`, `think,humanize`, `think,tldr`, `think,tts_optimize`, `translate`, `tldr`
- [ ] Implement file existence checking to skip completed inference
- [ ] Generate output paths: `f"_keep_this/adam/out/{safe_prompt_name}--{safe_model_id}.txt"`
- [ ] Add error message capture to output files on failure
- [ ] Sort models by "smart" method (as in `lmstrix list`)
- [ ] Load models with 50% input context, inference with 90% max context
- [ ] Minimize model loading/unloading through intelligent scheduling
- [ ] Use logger from `lmstrix.utils.logging`
- [ ] Process text from `_keep_this/adam/fontlab8.md`
