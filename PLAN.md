# LMStrix Current Development Plan


## ACTIVE: Issue #302 - Inference Output Mismatch (Major Progress Made)

### Current Status
**Major diagnostic improvements completed in v1.0.66:**
- ✅ Added comprehensive diagnostic logging for all inference parameters
- ✅ Updated default temperature from 0.7 to 0.8 to match LM Studio GUI
- ✅ Added CLI parameters for configuring inference settings
- ✅ Created diagnostic tools for parameter comparison
- ✅ Fixed table display and response preview issues

### Remaining Issues to Investigate
1. **Context Length**: GUI uses full 131072, CLI may reduce to 65536
2. **max_predict**: GUI uses -1 (unlimited), CLI calculates specific values
3. **Stop Token Configuration**: May differ between GUI and CLI
4. **Prompt Formatting**: Possible differences in chat template application

## Current Top Priority

### Issue #302 - Inference Output Mismatch (FINAL PHASE)
**Priority: HIGH - Core diagnostic work completed**

#### Remaining Implementation Steps:

##### Step 1: Context Length Investigation ⚠️
- Fix context reduction from full model context to reduced values
- Use full model context by default unless explicitly limited
- Add warning when context is automatically reduced
- Test with full context vs reduced context

##### Step 2: Stop Token Configuration ⚠️
- Compare stop token configuration between GUI and CLI
- Test with stop tokens disabled to rule out early termination
- Verify chat template application doesn't introduce stop tokens

##### Step 3: Final Validation ⚠️
- Run side-by-side comparison with identical parameters
- Verify token counts match between lmstrix and LM Studio
- Create regression test to prevent future issues

### Issue #105 - Adam.toml Simplification (Next Priority)
**Priority: Medium** (after Issue #302 is resolved)
- Simplify adam.toml structure to use flat format instead of nested groups
- Add --text and --text_file parameters to infer command for direct text input
- Update all prompt examples to use simplified approach
- Ensure backward compatibility with existing TOML files


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