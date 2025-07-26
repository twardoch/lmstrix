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

## Issue #201: Enhanced Context Testing Strategy (LARGELY COMPLETED)

### Core Implementation (COMPLETED)
- [x] Add --threshold parameter to CLI test command (default: 102400)
- [x] Refactor ContextTester.test_model() for new incremental/binary search algorithm
- [x] Implement test_all_models() method for efficient batch testing
- [x] Update output to use Rich tables for test results

### Testing Algorithm Changes (COMPLETED)
- [x] Implement initial test at min(threshold, declared_max)
- [x] Add incremental testing (increase by 10240) when threshold > declared_max
- [x] Ensure binary search only happens on failure
- [x] Save progress after each individual test

### Multi-Model Optimization (--all flag) (COMPLETED)
- [x] Sort models by declared context size before testing
- [x] Implement pass-based testing to minimize model loading
- [x] Track failed models and exclude from subsequent passes
- [x] Persist progress between passes

### Output Improvements (COMPLETED)
- [x] Create tabular output similar to 'list' command
- [x] Show: Model ID, Context Size, Result, Duration
- [x] Remove live updates, just append rows

### Remaining Tasks for Full Completion
- [ ] Review and optimize incremental testing algorithm performance
- [ ] Validate binary search edge cases with comprehensive testing
- [ ] Add performance benchmarking suite
- [ ] Update documentation for new --threshold parameter and enhanced strategy
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