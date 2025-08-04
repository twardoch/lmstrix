# LMStrix TODO List

## Current Active Work

### Priority 1: Issue #302 - Inference Output Mismatch (Final Phase)

**Major diagnostic work completed in v1.0.66. Remaining items:**

- [ ] Fix context length handling (GUI uses full 131072, CLI reduces to 65536)
- [ ] Investigate stop token configuration differences between GUI and CLI
- [ ] Compare maxTokens calculation: GUI uses -1 (unlimited), CLI calculates specific values
- [ ] Run side-by-side comparison with identical parameters
- [ ] Create regression test to prevent future recurrence

### Priority 2: Issue #105 - Adam.toml Simplification

- [ ] Update prompt loader to handle flat TOML structure (no nested groups)
- [ ] Add --text and --text_file parameters to infer command for direct text input
- [ ] Add backward compatibility for existing nested TOML files
- [ ] Update examples to use simplified flat format
- [ ] Create migration guide for existing users

## Future Development (Lower Priority)

### Code Quality Improvements

- [ ] Ruff linting improvements (143 errors identified)
  - [ ] Fix BLE001 blind exception catching (46 occurrences)
  - [ ] Fix A002 builtin shadowing (3 occurrences)
  - [ ] Address TRY300 statement placement issues (8 occurrences)
  - [ ] Remove commented-out code (ERA001)
- [ ] Add comprehensive type hints to public APIs
- [ ] Ensure all functions have proper docstrings
- [ ] Standardize error handling patterns

### Configuration and Utilities

- [ ] Create utils/config.py for centralized configuration handling
- [ ] Consolidate path handling functions
- [ ] Improve model loading optimization and reuse detection

### CLI Enhancement

- [ ] Add `reset` command for clearing model test data
- [ ] Add `health` command for system diagnostics
- [ ] Enhance `scan` and `list` commands with better filtering

### Testing and Documentation

- [ ] Ensure >90% test coverage maintained
- [ ] Update README.md with latest features
- [ ] Create comprehensive CLI reference
- [ ] Add integration tests for new features

