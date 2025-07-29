# LMStrix Development Plan - v1.1 Release

## 1. Project Vision & Status

**Vision**: Deliver a reliable, installable tool that solves the critical problem of models in LM Studio declaring false context limits. The tool provides automated discovery of true operational context limits.

**Current Status**: Core CLI enhancements completed. Primary focus on Issue #201 - Enhanced context testing strategy implementation to prevent system crashes and optimize multi-model testing performance.

## 2. Completed Phases

### Phase 1: Core Functionality (COMPLETED)
- ✓ System path detection and data storage
- ✓ Context testing engine with binary search
- ✓ Model management and registry
- ✓ CLI interface with all commands
- ✓ Package configuration

### Phase 2: Testing & Quality Assurance (COMPLETED)
- ✓ Comprehensive unit tests with mocking
- ✓ Integration tests for all components
- ✓ Edge case testing for binary search logic
- ✓ Type checking with mypy
- ✓ Linting with ruff

### Phase 3: Documentation (COMPLETED)
- ✓ Updated README with comprehensive guide
- ✓ API documentation with docstrings
- ✓ Examples directory with CLI and Python examples
- ✓ GitHub Pages documentation site
- ✓ Changelog maintenance

### Phase 3.5: CLI Enhancements (COMPLETED)
- ✓ Issue #204: Removed all asyncio dependencies, now fully synchronous
- ✓ Added `--sort` option to `test --all` command matching list command functionality
- ✓ Added `--ctx` option to work with `test --all` for batch testing at specific context sizes
- ✓ Added `--show` option to `list` command with multiple output formats (id, path, json)
- ✓ All show formats respect the sort option for flexible data export
- ✓ Enhanced model field updates during --ctx testing with proper persistence
- ✓ Fixed git upstream branch tracking configuration (v1.0.53)

## 3. Phase 4: Enhanced Context Testing (COMPLETED)

**Goal**: Implement safer and more efficient context testing strategy per Issue #201.

### 3.1. Implementation Status

✅ **--threshold Parameter (COMPLETED)**
   - ✓ Added to CLI test command with default 102,400
   - ✓ Controls maximum initial test size to prevent crashes
   - ✓ Integrated with min(threshold, declared_max) logic

✅ **Multi-Model Testing Infrastructure (COMPLETED)**
   - ✓ `test_all_models()` method implemented in ContextTester
   - ✓ Pass-based testing approach for efficiency
   - ✓ Progress persistence between model tests
   - ✓ Rich table output showing test results with efficiency percentages

✅ **Output Improvements (COMPLETED)**
   - ✓ Rich tables for final results summary
   - ✓ Model ID, Status, Optimal Context, Declared Limit, Efficiency columns
   - ✓ Clean progress indicators during batch testing

## 4. Phase 5: Package & Release (IN PROGRESS)

**Goal**: Release LMStrix v1.1.0 to PyPI with enhanced CLI features and testing capabilities.

### 4.1. Pre-Release Checklist
   - ✓ Core functionality stable and tested
   - ✓ CLI enhancements completed (--sort, --ctx, --show)
   - ✓ Asyncio removal completed (Issue #204)
   - ✓ Enhanced context testing completed (Issue #201)
   - ✓ Git configuration fixed (v1.0.53)
   - ✓ Enhanced infer context control (Issue #103)
   - [ ] Documentation updates for new features
   - [ ] Final validation testing with real models
   - [ ] Performance benchmarking suite

### 4.2. Release Steps

1. **Git Tag Creation**
   - Create annotated tag `v1.1.0` with release message highlighting CLI enhancements
   - Push tag to GitHub repository

2. **Package Building**
   - Run `python -m build` to create distribution packages
   - Verify wheel and sdist files are created correctly

3. **PyPI Publication**
   - Use `twine upload dist/*` to publish to PyPI
   - Ensure package metadata reflects v1.1.0

4. **Post-Release Verification**
   - Test installation: `pip install lmstrix`
   - Verify all CLI commands work, especially new --sort, --ctx, --show options
   - Test Python API imports

5. **GitHub Release**
   - Create GitHub release from v1.1.0 tag
   - Include comprehensive release notes
   - Highlight CLI enhancements and performance improvements

### 4.3. Release Notes Summary

**LMStrix v1.1.0 - Enhanced CLI & Performance Release**

Major Enhancements:
- **Enhanced CLI Functionality**: Added --sort, --ctx, and --show options for flexible model management
- **Full Synchronous Architecture**: Removed all asyncio dependencies for improved reliability
- **Optimized Context Testing**: Enhanced testing strategy with threshold controls and batch processing
- **Flexible Data Export**: Multiple output formats (id, path, json) with sorting support
- **Improved Safety**: Better context limit validation and crash prevention

This release significantly improves usability and performance while maintaining the core value proposition of discovering true model context limits.

## 5. Issue #103: Enhanced Infer Context Control (COMPLETED)

✅ **Successfully implemented** `--in_ctx` and `--out_ctx` options for better control over model loading and generation context.

### 5.1. Implementation Summary

- ✓ Added `--in_ctx` parameter to control model loading context size
- ✓ Added `--out_ctx` parameter to replace deprecated `--max_tokens`
- ✓ Implemented smart loading logic that unloads/reloads only when needed
- ✓ Supports `--in_ctx 0` to load model without context specification
- ✓ Maintains backward compatibility with deprecation warnings
- ✓ Enhanced memory management with conditional unloading

## 6. Immediate Improvements (Pre v1.1.0)

### 6.1. Model State Detection Enhancement

**Goal**: Improve the infer command to actually detect if a model is already loaded in LM Studio.

#### Implementation Plan:
1. Add `get_loaded_models()` method to LMStudioClient
2. Check loaded models before deciding to reload in InferenceEngine
3. Display status message when reusing already loaded model
4. Add `--force-reload` flag to force reload even if already loaded

#### Benefits:
- Better performance by avoiding unnecessary reloads
- Clear feedback about model loading status
- More intuitive behavior matching user expectations

### 6.2. Inference Status Display

**Goal**: Provide better feedback during inference operations.

#### Implementation Plan:
1. Add loading context information to status messages
2. Show whether model was reloaded or reused
3. Display actual context size used for loading
4. Add timing information for load vs inference phases

#### Example Output:
```
Loading model at context 8192... (explicit --in_ctx)
Model loaded successfully in 2.3s
Running inference...
Inference completed in 1.5s
```

### 6.3. Error Message Improvements

**Goal**: Provide more helpful error messages for common issues.

#### Implementation Plan:
1. Detect and report when requested context exceeds model limits
2. Suggest optimal context when load fails
3. Add hints for memory-related failures
4. Include model's tested context in error messages

### 6.4. CLI Usability Enhancements

**Goal**: Make the CLI more user-friendly.

#### Implementation Plan:
1. Add `lmstrix infer --list-loaded` to show currently loaded models
2. Add context size validation before attempting to load
3. Warn when --in_ctx significantly differs from tested context
4. Add `--dry-run` flag to show what would happen without executing

## 7. Issue #104: Prompt File Support with TOML

**Goal**: Implement `--file_prompt` and `--dict` parameters for loading prompts from TOML files with advanced placeholder resolution.

### 7.1. Requirements Analysis

The issue requests:
1. **`--file_prompt`**: Path to a TOML file containing prompt templates
2. **`--prompt`**: When used with `--file_prompt`, refers to the prompt name in the TOML file
3. **`--dict`**: Dictionary of variables to resolve placeholders in the TOML file
4. Use `topl` library for enhanced TOML parsing and placeholder resolution

### 7.2. Implementation Plan

#### Phase 1: CLI Parameter Updates
1. Add `--file_prompt` parameter to specify TOML file path
2. Add `--dict` parameter to accept key=value pairs
3. Modify `--prompt` behavior when `--file_prompt` is present
4. Validate parameter combinations

#### Phase 2: Parameter Parsing
1. Parse `--dict` parameter into dictionary format
   - Support formats: `--dict key1=value1 key2=value2`
   - Alternative: `--dict "key1=value1,key2=value2"`
2. Validate TOML file exists and is readable
3. Handle path expansion (~, relative paths)

#### Phase 3: Prompt Loading Integration
1. Detect when `--file_prompt` is provided
2. Load TOML file using existing `load_single_prompt` function
3. Pass dictionary parameters for placeholder resolution
4. Use resolved prompt text for inference

#### Phase 4: Enhanced Resolution (Optional)
1. Consider integrating `topl` library features:
   - Circular reference detection
   - Multi-pass internal resolution
   - Better error reporting for unresolved placeholders
2. Maintain backward compatibility with existing prompt system

### 7.3. Technical Details

#### CLI Interface
```bash
# Load prompt from file with parameters
lmstrix infer my_prompt model-id \
  --file_prompt prompts.toml \
  --dict name=Alice topic=AI

# Or with comma-separated format
lmstrix infer my_prompt model-id \
  --file_prompt prompts.toml \
  --dict "name=Alice,topic=AI,style=formal"
```

#### TOML File Example
```toml
# prompts.toml
[greetings]
formal = "Good day, {{name}}. How may I assist you with {{topic}}?"
casual = "Hey {{name}}! What's up with {{topic}}?"

[templates]
base = "You are an expert in {{domain}}."
instruction = "{{templates.base}} Please explain {{concept}} in {{style}} terms."
```

#### Implementation Flow
```python
if file_prompt:
    # Load and resolve prompt from TOML
    prompt_params = parse_dict_parameter(dict_param)
    resolved = load_single_prompt(
        toml_path=Path(file_prompt),
        prompt_name=prompt,  # Now refers to prompt name in TOML
        **prompt_params
    )
    actual_prompt = resolved.resolved
else:
    # Use prompt parameter directly as text
    actual_prompt = prompt
```

### 7.4. Benefits

1. **Reusable Prompts**: Store prompts in version-controlled files
2. **Dynamic Templates**: Use placeholders for flexible prompts
3. **Better Organization**: Separate prompt logic from code
4. **Team Collaboration**: Share prompt libraries across projects

### 7.5. Considerations

1. **Error Handling**:
   - Clear messages when prompt not found in TOML
   - Report unresolved placeholders
   - Validate TOML syntax

2. **Performance**:
   - Cache loaded TOML files
   - Efficient placeholder resolution

3. **Security**:
   - Validate file paths
   - Sanitize parameter values
   - Prevent path traversal attacks

## 8. Future Phases (Post v1.1.0)

### Phase 6: Performance & Monitoring
- [ ] Add performance benchmarking suite for context testing efficiency
- [ ] Implement progress bars for long-running context tests
- [ ] Add GPU memory monitoring during tests
- [ ] Create performance regression testing

### Phase 7: Advanced Features
- [ ] Support for custom test prompts via CLI argument
- [ ] Multi-prompt testing for more robust validation
- [ ] Document type-specific testing (code, prose, technical content)
- [ ] Integration with external model registries

### Phase 8: Ecosystem Integration
- [ ] Plugin system for custom testing strategies
- [ ] Integration with popular ML workflow tools
- [ ] REST API for programmatic access
- [ ] Docker containerization for isolated testing

### Phase 9: Enterprise Features
- [ ] Batch model management across multiple LM Studio instances
- [ ] Team collaboration features for shared model registries
- [ ] Advanced reporting and analytics
- [ ] Integration with CI/CD pipelines