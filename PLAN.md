# LMStrix Current Development Plan

## Current Status
- ✅ CLI refactoring completed - business logic moved to `api/main.py`
- ✅ Issues 201-204 have been completed successfully
- ✅ Issue #303 - Fixed loguru output interference with model responses

## COMPLETED: Issue #303 - Fix Loguru Output Interference ✅

### Problem Description
When running inference with `--verbose`, loguru was outputting the prompt and model response through its handlers, causing:
1. **Logging errors**: KeyError and ValueError exceptions in loguru handlers
2. **Output pollution**: Model responses were mixed with loguru formatting
3. **User requirement violation**: User explicitly stated to NEVER pass prompt or model output through loguru

### Root Cause
- In `api/client.py`, the prompt and model response were being logged via loguru
- Loguru was trying to format the output, causing issues with special characters like `</translation-instructions>`
- This violated the requirement to use `sys.stderr` for prompts and `sys.stdout` for model output

### Fix Applied
1. **✅ Removed all loguru logging of prompts and model responses**
2. **✅ Now using sys.stderr for prompt display in verbose mode**
3. **✅ Using sys.stdout for model output only**
4. **✅ Keeping loguru only for diagnostic/status messages**

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

## Immediate Priorities

### 1. Fix Issue #302 - Inference Output Mismatch
**Priority: CRITICAL - NOW TOP PRIORITY**
- This is blocking proper inference functionality
- Users cannot get correct model outputs
- Model only outputs `</translation>` instead of full translation

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

## Implementation Order

### Phase 0: CRITICAL FIXES (Immediate - 1 day)
1. **✅ Issue #303 - Loguru Fix** (COMPLETED):
   - ✅ Removed loguru from prompt/response logging
   - ✅ Implemented proper stderr/stdout separation
   - ✅ Tested with translation example - no more errors!

2. **Issue #302 - Inference Fix** (NOW TOP PRIORITY):
   - Align parameters with LM Studio
   - Fix context length handling
   - Investigate stop token issue

### Phase 1: Normal Development (After Issue #302)
- Continue with Issue #105 and other planned improvements

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
- Intuitive CLI interface with beautiful, informative output
- Smart model management with automatic optimization
- Comprehensive testing capabilities with clear results
- Excellent developer experience with clean, well-documented code