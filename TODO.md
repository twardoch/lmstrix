# TODO List for LMStrix

## Immediate Tasks

- [ ] Test the improved context testing with actual models
- [ ] Verify progress saving/resuming works correctly
- [ ] Update documentation to reflect new testing behavior
- [ ] Consider adding unit tests for new functionality

## Phase 4: Package & Release

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