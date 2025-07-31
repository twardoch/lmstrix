# LMStrix TODO List

## CRITICAL: Issue #303 - Fix Loguru Output Interference (Priority 0) ✅ COMPLETED

### Remove Loguru from Prompt/Response Logging
- [x] Remove all `logger.debug()` calls that output prompts or model responses in api/client.py
- [x] Remove the "Raw response object" logging that causes ValueError
- [x] Remove prompt logging that passes through loguru formatting

### Implement Proper Output Separation
- [x] Use `print(prompt, file=sys.stderr)` for verbose prompt display
- [x] Use `print(response, file=sys.stdout)` for model output only
- [x] Keep loguru only for status messages like "Running inference...", "Time to first token", etc.
- [x] Ensure clean separation between diagnostic info and actual output

### Test the Fix
- [x] Run the translation example from issue #303
- [x] Verify no loguru errors appear
- [x] Confirm model output goes only to stdout
- [x] Confirm diagnostic info goes only to stderr

## CRITICAL: Issue #302 - Fix Inference Output Mismatch (Priority 0)

### Diagnostic Investigation
- [ ] Add detailed logging of exact prompt being sent to model
- [ ] Log all inference parameters before sending request
- [ ] Log stop tokens configuration
- [ ] Add comparison mode to show differences from LM Studio defaults
- [ ] Check if chat template is being applied incorrectly

### Parameter Alignment  
- [ ] Change default temperature from 0.7 to 0.8
- [ ] Add CLI flags for all inference parameters (--top_k, --top_p, --min_p)
- [ ] Add --repeat_penalty and --repeat_last_n flags
- [ ] Add --stop_tokens flag to override defaults
- [ ] Remove or make optional the maxTokens calculation (90% of context)

### Context Length Fix
- [ ] Fix context reduction from 131072 to 65536 issue
- [ ] Use full model context unless explicitly limited by user
- [ ] Add warning message when context is reduced
- [ ] Ensure --in_ctx parameter works correctly

### Stop Token Investigation
- [ ] Investigate why model stops at `</translate>` 
- [ ] Test with stop tokens disabled
- [ ] Compare stop token handling with LM Studio
- [ ] Add --no-stop-tokens flag for testing

### Testing and Validation
- [ ] Compare output with LM Studio for identical prompts
- [ ] Ensure token counts match between lmstrix and LM Studio
- [ ] Verify translation quality matches expected output
- [ ] Create regression test for this issue

## Immediate Priorities (AFTER Issue #303 and #302)

### Issue #105 - Adam.toml Simplification (High Priority)
- [ ] Simplify adam.toml structure to use flat format instead of nested groups
- [ ] Add --text and --text_file parameters to infer command for direct text input
- [ ] Update all prompt examples to use simplified approach
- [ ] Ensure backward compatibility with existing TOML files
- [ ] Test all prompt examples with new structure
- [ ] Update documentation for new TOML format

### Context Testing Streamlining (Medium Priority)
- [ ] Simplify ContextTester class by merging methods into single test_context() function
- [ ] Remove complex state management and resumption logic
- [ ] Streamline binary search algorithm
- [ ] Consolidate test result logging
- [ ] Update context testing tests to match new structure

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