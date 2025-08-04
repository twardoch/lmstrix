# LMStrix Current Development Plan

## Ruff Linting Improvements Plan

### Overview
This plan addresses the 143 Ruff linting errors identified in the codebase. The improvements will enhance code quality, maintainability, and robustness while ensuring backward compatibility.

### Error Analysis Summary

#### Critical Issues (High Priority)
1. **BLE001 - Blind Exception Catching (46 occurrences)**
   - Most prevalent issue affecting error handling quality
   - Reduces debuggability and can hide serious errors
   
2. **E722 - Bare Except (2 occurrences)**
   - Similar to BLE001 but even more dangerous
   - Must be fixed for proper error handling

#### Code Quality Issues (Medium Priority)
3. **A002 - Shadowing Python Builtins (3 occurrences)**
   - Variables named `all`, `dict`, `id` shadow builtins
   - Can cause unexpected behavior
   
4. **TRY300 - Statement Placement (8 occurrences)**
   - Logic that should be in else blocks
   - Affects code clarity and exception handling flow
   
5. **PLC0415 - Non-Top-Level Imports (8 occurrences)**
   - Dynamic imports within functions
   - Can impact performance and code clarity

#### Complexity Issues (Low Priority - May Exclude)
6. **PLR0912 - Too Many Branches (12 occurrences)**
7. **PLR0915 - Too Many Statements (11 occurrences)**
8. **PLR0911 - Too Many Return Statements (2 occurrences)**
   - These often indicate functions that need refactoring
   - However, some complex logic legitimately requires many branches

#### Maintainability Issues
9. **ERA001 - Commented-Out Code (9 occurrences)**
   - Dead code that should be removed
   - Version control preserves history
   
10. **ARG002 - Unused Arguments (5 occurrences)**
    - Method arguments that aren't used
    - May indicate API design issues

### Implementation Strategy

#### Phase 1: Critical Fixes (Immediate)
1. Fix all BLE001 errors by:
   - Replacing `except Exception:` with specific exceptions
   - Adding proper error context and logging
   - Example transformation:
   ```python
   # Before
   try:
       result = some_operation()
   except Exception as e:
       logger.error(f"Operation failed: {e}")
   
   # After
   try:
       result = some_operation()
   except (ValueError, TypeError, KeyError) as e:
       logger.error(f"Operation failed with {type(e).__name__}: {e}")
   except Exception as e:
       logger.exception(f"Unexpected error in operation: {e}")
       raise
   ```

2. Fix E722 bare except clauses
3. Fix A002 builtin shadowing:
   - `all` → `all_items` or `show_all`
   - `dict` → `dict_params` or `params_dict`
   - `id` → `model_id` or `identifier`

#### Phase 2: Code Quality Improvements
1. Fix TRY300 by restructuring try-except-else blocks
2. Move dynamic imports to top-level where possible (PLC0415)
3. Remove commented-out code (ERA001)
4. Fix unused arguments (ARG002) by either:
   - Using them if needed
   - Adding `_` prefix for intentionally unused
   - Removing if part of public API that can be changed

#### Phase 3: Complexity Management
1. For PLR0912/PLR0915 (too many branches/statements):
   - Evaluate each case individually
   - Refactor where it improves readability
   - Add exclusions for legitimate complex logic
   
2. Consider breaking down large functions into smaller ones:
   - Extract validation logic
   - Extract error handling patterns
   - Create helper methods

### Ruff Configuration Updates

Add to `pyproject.toml`:

```toml
[tool.ruff]
# Existing configuration...

# Per-file ignores for legitimate exceptions
[tool.ruff.per-file-ignores]
# Complex CLI and API endpoints may have many branches
"src/lmstrix/api/main.py" = ["PLR0912", "PLR0915"]
"src/lmstrix/core/inference_manager.py" = ["PLR0912", "PLR0915"]
"src/lmstrix/core/inference.py" = ["PLR0912", "PLR0915"]

# Example scripts may have different standards
"examples/**/*.py" = ["PLR0915", "ERA001"]

# Test files may need different rules
"tests/**/*.py" = ["ARG002"]  # Test fixtures often have unused args

# Ignore specific rules globally with justification
ignore = [
    # These will be addressed individually, not blanket ignored
]
```

### Testing Strategy
1. Run full test suite after each phase
2. Add new tests for improved error handling
3. Verify no regression in functionality
4. Check performance impact of changes

### Success Metrics
- Reduce total Ruff errors from 143 to < 20
- All remaining errors have explicit exclusions with justification
- Improved error messages and debugging capability
- No functionality regression
- Better code maintainability

### Timeline
- Phase 1: 2-3 hours (Critical fixes)
- Phase 2: 1-2 hours (Quality improvements)
- Phase 3: 2-3 hours (Complexity management)
- Testing & validation: 1 hour

Total estimated time: 6-9 hours of focused work


## Current Status
### Problem Description
When running inference with `--verbose`, loguru was outputting the prompt and model response through its handlers, causing:
1. **Logging errors**: KeyError and ValueError exceptions in loguru handlers
2. **Output pollution**: Model responses were mixed with loguru formatting
3. **User requirement violation**: User explicitly stated to NEVER pass prompt or model output through loguru

### Root Cause
- In `api/client.py`, the prompt and model response were being logged via loguru
- Loguru was trying to format the output, causing issues with special characters like `</translation-instructions>`
- This violated the requirement to use `sys.stderr` for prompts and `sys.stdout` for model output


## CRITICAL: Issue #302 - Inference Output Mismatch

### Problem Description
When running the same translation prompt through LM Studio GUI vs lmstrix CLI, we get drastically different results:
- **LM Studio GUI**: Produces proper Polish translation (639 tokens)
- **lmstrix CLI**: Only outputs `</translate>` (4 tokens)

### Root Cause Analysis

#### Configuration Differences Found
1. **Temperature**: GUI uses 0.8, CLI uses 0.7
2. **top_k**: GUI uses 20, CLI uses 40  
3. **Context Length**: GUI uses full 131072, CLI uses 65536 (reduced)
4. **max_predict**: GUI uses -1 (unlimited), CLI calculates 117964
5. **Sampling Parameters**: Multiple differences in repeat_penalty, min_p, etc.

#### Potential Issues
1. **Early Stop Token**: Model might be hitting a stop token immediately
2. **Prompt Format**: The prompt might be wrapped or modified differently
3. **Chat Template**: Possible incorrect chat template application
4. **Parameter Mismatch**: Inference parameters not matching LM Studio defaults

## Current Top Priority

### Issue #302 - Inference Output Mismatch (CRITICAL)
**Priority: URGENT - Blocking Core Functionality**
- Model outputs only `</translate>` instead of full translation
- LM Studio GUI produces 639 tokens, lmstrix CLI produces 4 tokens  
- Critical inference functionality is broken for users

#### Implementation Steps:

##### Step 1: Add Diagnostic Logging
- Log the exact prompt being sent (with escape sequences visible)
- Log all inference parameters in detail
- Log stop tokens being used
- Add comparison with LM Studio expected values

##### Step 2: Parameter Alignment
- Change default temperature from 0.7 to 0.8
- Add CLI parameters for all inference settings
- Remove or make optional the maxTokens calculation

##### Step 3: Context Length Fix
- Fix context reduction from 131072 to 65536
- Use full model context unless explicitly limited
- Add warning when context is reduced

##### Step 4: Stop Token Investigation  
- Check why model stops at `</translate>`
- Verify stop token configuration
- Test with stop tokens disabled

### 2. Issue #105 - Adam.toml Simplification
**Priority: High** (after Issue #302)
- Simplify adam.toml structure to use flat format instead of nested groups
- Add --text and --text_file parameters to infer command for direct text input
- Update all prompt examples to use simplified approach
- Ensure backward compatibility with existing TOML files

## COMPLETED FEATURES ✅

### Compact Test Output ✅ COMPLETED
**Status: FULLY IMPLEMENTED AND WORKING**

Successfully implemented compact output for the test command:
- ✅ Live-updating rich tables for non-verbose mode
- ✅ Clean display of model ID, context size, and status
- ✅ Progress tracking for batch tests with `--all` flag
- ✅ Maintains backward compatibility with verbose mode
- ✅ Significantly improved readability for testing workflows

### Issue #307: Streaming Inference Support ✅ COMPLETED
**Status: FULLY IMPLEMENTED AND WORKING**

All original requirements have been successfully implemented:
- ✅ Async streaming API using lmstudio SDK's `complete_stream()`
- ✅ Full backward compatibility maintained
- ✅ CLI `--stream` and `--stream-timeout` flags
- ✅ Robust error handling and cancellation support
- ✅ Efficient token-by-token processing and display
- ✅ Streaming statistics and progress monitoring

### Issue #306: Batch Processing Tool ✅ COMPLETED  
**Status: FULLY IMPLEMENTED AND WORKING**

The adamall.py batch processing tool has been successfully created with all required features:
- ✅ Smart model management with reuse detection
- ✅ Processes all 6 target prompts efficiently
- ✅ Safe filename generation using pathvalidate
- ✅ Skip existing outputs for resumable processing
- ✅ Comprehensive error handling and progress tracking
- ✅ Intelligent model scheduling for optimal performance

#### Usage:
```bash
cd _keep_this/adam
python adamall.py
```

Output files are generated in `_keep_this/adam/out/` with safe naming patterns.

## Current Active Development

### Issue #105 - Adam.toml Simplification (Next Priority)
**Priority: High** (after Issue #302 is resolved)

#### Problem Statement
Current adam.toml structure uses nested groups which is complex for users:
```toml
[prompts.translate]
template = "Translate this to Polish: {text}"

[prompts.think.aps]  
template = "Think step by step: {text}"
```

#### Target Simplification
Change to flat structure for better usability:
```toml
[translate]
template = "Translate this to Polish: {text}"

[think_aps]
template = "Think step by step: {text}"
```

#### Implementation Requirements
1. Update prompt loader to handle flat structure
2. Add backward compatibility for existing nested files
3. Add --text and --text_file parameters to infer command
4. Update all examples to use simplified format
5. Migration guide for existing users

#### Success Criteria
- Users can create simple, flat TOML prompt files
- Existing nested files continue to work
- CLI supports direct text input without files

## Future Development Phases

### Phase A: Core Simplification (2-3 weeks)
1. **Configuration Unification**
   - Create utils/config.py for centralized configuration handling
   - Consolidate path handling functions
   - Remove redundant configuration code

2. **Error Handling Standardization**
   - Review and simplify custom exception hierarchy
   - Standardize error messages across codebase
   - Implement consistent logging patterns

### Phase B: CLI Enhancement (1-2 weeks)
1. **Command Improvements**
   - Enhance `scan` command with better progress reporting
   - Improve `list` command with filtering and sorting options
   - Add `reset` command for clearing model test data

2. **User Experience**
   - Better error messages with helpful suggestions
   - Improved help text and documentation
   - Enhanced progress indicators for long-running operations

### Phase C: Testing & Documentation (1 week)
1. **Test Suite Completion**
   - Ensure >90% test coverage maintained
   - Add integration tests for new features
   - Performance benchmarking of improvements

2. **Documentation Updates**
   - Update README.md with latest features
   - Create comprehensive CLI reference
   - Update examples to demonstrate new capabilities

## Success Metrics

- **Functionality**: All existing CLI commands work without regression
- **Performance**: Model loading and inference speed improvements
- **Usability**: Cleaner, more informative user interface
- **Maintainability**: Reduced complexity, better code organization
- **Documentation**: Up-to-date and comprehensive user guides


## Long-term Vision

The goal is to make LMStrix the most user-friendly and efficient tool for managing and testing LM Studio models, with:
- Real-time streaming inference with progress feedback and hang detection
- Intuitive CLI interface with beautiful, informative output
- Smart model management with automatic optimization
- Batch processing capabilities for productivity workflows
- Comprehensive testing capabilities with clear results
- Excellent developer experience with clean, well-documented code