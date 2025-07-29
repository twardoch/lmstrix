# TODO List for LMStrix


## Remaining Tasks for v1.1.0 Release

### Documentation
- [ ] Update documentation for new --threshold parameter and enhanced strategy
- [ ] Update README with new testing strategy explanation
- [ ] Document CLI enhancements (--sort, --ctx, --show options)
- [ ] Add examples for new CLI features

### Testing & Validation
- [ ] Review and optimize incremental testing algorithm performance
- [ ] Validate binary search edge cases with comprehensive testing
- [ ] Add performance benchmarking suite
- [ ] Final validation testing with real models

## Phase 5: Package & Release

### Next Release (v1.1.0)
- [ ] Create git tag v1.1.0 with release message
- [ ] Push tag to GitHub repository
- [ ] Build distribution packages with `python -m build`
- [ ] Verify wheel and sdist files
- [ ] Publish to PyPI using `twine upload dist/*`
- [ ] Test installation from PyPI: `pip install lmstrix`
- [ ] Verify all CLI commands work after PyPI install
- [ ] Create GitHub release from v1.1.0 tag
- [ ] Write comprehensive release notes for GitHub


## Immediate Improvements (Pre v1.1.0)

### Model State Detection (COMPLETED)
- [x] Add get_loaded_models() method to LMStudioClient
- [x] Check loaded models before reloading in InferenceEngine
- [x] Display status when reusing already loaded model
- [x] Add --force-reload flag to force model reload

### Inference Status Display (PARTIALLY COMPLETED)
- [x] Show loading context information in status messages
- [x] Display whether model was reloaded or reused
- [x] Show actual context size used for loading
- [ ] Add timing breakdown for load vs inference phases

### Error Message Improvements (PARTIALLY COMPLETED)
- [x] Detect when requested context exceeds model limits
- [ ] Suggest optimal context when load fails
- [ ] Add helpful hints for memory-related failures
- [ ] Include model's tested context in error messages

### CLI Usability (PARTIALLY COMPLETED)
- [ ] Add lmstrix infer --list-loaded command
- [x] Add context size validation before loading
- [x] Warn when --in_ctx differs from tested context
- [ ] Add --dry-run flag for testing commands

## Issue #104: Prompt File Support with TOML (COMPLETED)

### Implementation Tasks
- [x] Add --file_prompt parameter to infer command
- [x] Add --dict parameter for key=value pairs
- [x] Implement parameter parsing for --dict
- [x] Modify prompt handling when --file_prompt is present
- [x] Integrate with existing prompt loading system
- [x] Add validation for TOML file existence
- [x] Handle path expansion for file paths
- [x] Add error handling for missing prompts
- [x] Report unresolved placeholders clearly
- [x] Create example TOML prompt files
- [x] Update help text and documentation
- [x] Test with various parameter combinations

## Future Improvements

- [ ] Add support for custom test prompts via CLI argument
- [ ] Add option to test multiple prompts for more robust validation
- [ ] Consider adding GPU memory monitoring during tests
- [ ] Add visual progress bar for context testing
- [ ] Support for testing with specific document types (code, prose, etc.)