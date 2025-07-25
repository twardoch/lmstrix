# LMStrix Development Plan - v1.1 Release

## 1. Project Vision & Status

**Vision**: Deliver a reliable, installable tool that solves the critical problem of models in LM Studio declaring false context limits. The tool provides automated discovery of true operational context limits.

**Current Status**: Working on Issue #201 - Enhanced context testing strategy to prevent system crashes and optimize multi-model testing.

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

## 3. Phase 4: Enhanced Context Testing (IN PROGRESS)

**Goal**: Implement safer and more efficient context testing strategy per Issue #201.

### 3.1. Implementation Tasks

1. **Add --threshold Parameter**
   - Add to CLI test command with default 102,400
   - Controls maximum initial test size to prevent crashes
   - Use min(threshold, declared_max) for second test

2. **New Testing Algorithm**
   - Test at 1024 first
   - Then test at min(threshold, declared_max)
   - If success and threshold > declared_max: increment by 10,240
   - If failure: binary search downwards
   - Save progress after each test

3. **Multi-Model Testing (--all flag)**
   - Sort models by declared context size (ascending)
   - Test in passes to minimize loading/unloading
   - Pass 1: Test all at 1024, exclude failures
   - Pass 2+: Continue with remaining models
   - Track and persist progress between passes

4. **Improved Output**
   - Replace primitive output with Rich tables
   - Show one row per model test
   - Include: Model ID, Context Size, Result, Duration
   - No live updates, just append rows

## 4. Phase 5: Package & Release (PENDING)

**Goal**: Release LMStrix v1.1.0 to PyPI with enhanced testing capabilities.

### 3.1. Release Steps

1. **Git Tag Creation**
   - Create annotated tag `v1.0.0` with release message
   - Push tag to GitHub repository

2. **Package Building**
   - Run `python -m build` to create distribution packages
   - Verify wheel and sdist files are created correctly

3. **PyPI Publication**
   - Use `twine upload dist/*` to publish to PyPI
   - Ensure package metadata is correct

4. **Post-Release Verification**
   - Test installation: `pip install lmstrix`
   - Verify all CLI commands work
   - Test Python API imports

5. **GitHub Release**
   - Create GitHub release from v1.0.0 tag
   - Include comprehensive release notes
   - Highlight key features and improvements

### 3.2. Release Notes Summary

**LMStrix v1.0.0 - Initial Release**

Key Features:
- Automatic discovery of true model context limits
- Binary search algorithm for efficient testing
- Native integration with LM Studio
- Beautiful CLI with rich formatting
- Comprehensive Python API
- Persistent model registry
- Detailed logging and progress tracking

This release solves the critical problem of LM Studio models falsely advertising higher context limits than they can actually handle, saving users time and preventing runtime failures.