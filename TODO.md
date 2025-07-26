# TODO List for LMStrix

## Recent CLI Enhancements (COMPLETED)
- [x] Add --sort option to `test --all` command
- [x] Add --ctx option to work with `test --all`
- [x] Add --show option to `list` command with id/path/json formats
- [x] Make all --show formats respect --sort option
- [x] Fix model field updates during --ctx testing

## Issue #204: Remove all asyncio from lmstrix (COMPLETED)
- [x] Remove asyncio from context_tester.py
- [x] Remove asyncio from client.py
- [x] Remove asyncio from cli/main.py
- [x] Remove asyncio from inference.py
- [x] Remove asyncio from context.py
- [x] Remove asyncio from __init__.py
- [x] Test files still use AsyncMock (low priority)

## Issue #201: Enhanced Context Testing Strategy

### Core Implementation
- [ ] Add --threshold parameter to CLI test command (default: 102400)
- [ ] Refactor ContextTester.test_model() for new incremental/binary search algorithm
- [ ] Implement test_all_models() method for efficient batch testing
- [ ] Update output to use Rich tables for test results

### Testing Algorithm Changes
- [ ] Implement initial test at min(threshold, declared_max)
- [ ] Add incremental testing (increase by 10240) when threshold > declared_max
- [ ] Ensure binary search only happens on failure
- [ ] Save progress after each individual test

### Multi-Model Optimization (--all flag)
- [ ] Sort models by declared context size before testing
- [ ] Implement pass-based testing to minimize model loading
- [ ] Track failed models and exclude from subsequent passes
- [ ] Persist progress between passes

### Output Improvements
- [ ] Create tabular output similar to 'list' command
- [ ] Show: Model ID, Context Size, Result, Duration
- [ ] Remove live updates, just append rows

### Validation & Documentation
- [ ] Test with actual models to verify no system crashes
- [ ] Update unit tests for new functionality
- [ ] Update documentation for new --threshold parameter
- [ ] Update README with new testing strategy explanation

## Phase 5: Package & Release (After Issue #201)

### Release Tasks

- [x] Create git tag v1.0.30 with release message
- [ ] Push tag to GitHub repository
- [x] Build distribution packages with `python -m build`
- [x] Verify wheel and sdist files
- [ ] Publish to PyPI using `twine upload dist/*`
- [ ] Test installation from PyPI: `pip install lmstrix`
- [ ] Verify all CLI commands work after PyPI install
- [ ] Create GitHub release from v1.0.30 tag
- [ ] Write comprehensive release notes for GitHub

## Future Improvements

- [ ] Add support for custom test prompts via CLI argument
- [ ] Add option to test multiple prompts for more robust validation
- [ ] Consider adding GPU memory monitoring during tests
- [ ] Add visual progress bar for context testing
- [ ] Support for testing with specific document types (code, prose, etc.)