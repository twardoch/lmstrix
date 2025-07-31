# LMStrix Current Development Plan

## Current Status
Recent issues 201-204 have been completed successfully:
- ✅ Enhanced model persistence and state management
- ✅ Beautiful enhanced logging with comprehensive statistics  
- ✅ Fixed model lookup to work with both paths and IDs
- ✅ Integrated verbose stats display without duplication

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

## CRITICAL: Test Suite Failures (cleanup.txt analysis)

### Priority 0: Critical Test Failures - MUST FIX IMMEDIATELY

#### 0.1 Missing Methods Causing AttributeErrors
**Severity: CRITICAL - Breaks core functionality**

1. **Model.validate_integrity() Missing**
   - Location: src/lmstrix/loaders/model_loader.py:181
   - Error: `AttributeError: 'Model' object has no attribute 'validate_integrity'`
   - Impact: Prevents model loading and registry updates
   - Fix: Add validate_integrity() method to Model class

2. **PromptResolver Methods Missing**
   - Errors: Multiple AttributeErrors for:
     - `_resolve_phase` (private method)
     - `resolve_template` (public method)
     - `_count_tokens` (private method)
   - Impact: Completely breaks prompt resolution
   - Fix: Implement all missing methods in PromptResolver

3. **ContextTester Methods Missing**
   - Missing: `_test_at_context`, `test_model`
   - Impact: Context testing non-functional
   - Fix: Add methods to ContextTester class

4. **ModelScanner.sync_with_registry() Missing**
   - Impact: Cannot sync discovered models with registry
   - Fix: Implement sync_with_registry method

#### 0.2 Type and Format Errors
**Severity: HIGH - Breaks tests and logging**

1. **Mock Format String Errors**
   - Location: src/lmstrix/api/client.py:221
   - Error: `TypeError: unsupported format string passed to Mock.__format__`
   - Cause: `logger.info(f"📏 CONTEXT: {llm.config.contextLength:,} tokens")`
   - Fix: Handle None/Mock values in format strings

2. **Invalid Format Specifier**
   - Location: src/lmstrix/core/prompts.py:133
   - Error: `ValueError: Invalid format specifier ' 'Important'' for object of type 'str'`
   - Fix: Properly escape format strings in templates

#### 0.3 Initialization and Path Issues
**Severity: MEDIUM - Test failures**

1. **Model Constructor Arguments**
   - Error: `TypeError: Model.__init__() missing 3 required positional arguments`
   - Fix: Update tests to provide required args: path, size_bytes, ctx_in

2. **Path Handling in Scanner**
   - Error: `ValueError: path is not in the subpath`
   - Fix: Handle paths outside expected directory

## Immediate Priorities

### 1. Fix Issue #302 - Inference Output Mismatch
**Priority: CRITICAL**
- This is blocking proper inference functionality
- Users cannot get correct model outputs
- Must be fixed before any other work

#### Implementation Steps:

##### Step 1: Add Diagnostic Logging
- Log the exact prompt being sent (with escape sequences visible)
- Log all inference parameters in detail
- Log stop tokens being used
- Add comparison with LM Studio expected values

##### Step 2: Parameter Alignment
- Change default temperature from 0.7 to 0.8
- Add CLI parameters for all inference settings:
  - `--top_k`, `--top_p`, `--min_p`
  - `--repeat_penalty`, `--repeat_last_n`
  - `--stop_tokens` (to override defaults)
- Remove or make optional the maxTokens calculation

##### Step 3: Context Length Fix
- Fix context reduction from 131072 to 65536
- Use full model context unless explicitly limited
- Add warning when context is reduced

##### Step 4: Stop Token Investigation  
- Check why model stops at `</translate>`
- Verify stop token configuration
- Test with stop tokens disabled

##### Step 5: Testing and Validation
- Compare output with LM Studio for identical prompts
- Ensure token counts match
- Verify quality of translation output

### 2. Fix All Critical Test Failures
**Priority: HIGH** (after Issue #302)
- See Priority 0 section below - required for stability
- Estimated time: 2-3 days
- Success metric: All tests passing

### 2. Issue #105 - Adam.toml Simplification
**Priority: High** (but AFTER test fixes)
- Simplify adam.toml structure to use flat format instead of nested groups
- Add --text and --text_file parameters to infer command for direct text input
- Update all prompt examples to use simplified approach
- Ensure backward compatibility with existing TOML files

### 3. Context Testing Streamlining  
**Priority: Medium**
- Simplify ContextTester class by merging methods into single test_context() function
- Remove complex state management and resumption logic
- Streamline binary search algorithm
- Consolidate test result logging

### 4. Model Loading Optimization
**Priority: Medium**  
- Improve model reuse detection to avoid unnecessary loading messages
- Add context length display in enhanced logging when available
- Optimize model loading workflow for better performance

## Implementation Order

### Phase 0: CRITICAL FIX (Immediate - 2-3 days)
1. **Day 1: Core Method Implementation**
   - Add Model.validate_integrity() 
   - Implement all PromptResolver missing methods
   - Add ContextTester missing methods
   - Add ModelScanner.sync_with_registry()

2. **Day 2: Type/Format Fixes**
   - Fix mock format string handling in client.py
   - Fix prompt format specifier issues
   - Update tests with proper model initialization

3. **Day 3: Testing & Validation**
   - Run full test suite
   - Fix any remaining failures
   - Ensure no regressions

### Phase 1: Resume Normal Development (After tests pass)
- Continue with priorities 2-4 above

## Future Development Phases

### Phase A: Core Simplification (2-3 weeks)
1. **Configuration Unification**
   - Create utils/config.py for centralized configuration handling
   - Consolidate path handling functions (get_lmstudio_path, etc.)
   - Remove redundant configuration code

2. **Error Handling Standardization**
   - Review and simplify custom exception hierarchy
   - Standardize error messages across codebase
   - Implement consistent logging patterns

3. **Code Quality Improvements**
   - Add comprehensive type hints to public APIs
   - Ensure all functions have proper docstrings
   - Remove deprecated TODO comments from code

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

## Technical Debt Reduction

### Code Architecture
- Review and simplify InferenceManager class structure
- Consolidate duplicate logic across modules
- Improve separation of concerns between CLI and core logic

### Performance Optimization
- Profile model loading and caching behavior
- Optimize JSON registry read/write operations
- Reduce memory usage in context testing

### Dependency Management
- Review and minimize external dependencies
- Ensure compatibility with latest Python versions
- Update build and packaging configuration

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