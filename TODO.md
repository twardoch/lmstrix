# TODO List for LMStrix v1.0 Release

## Phase 4: Package & Release

### Release Tasks

- [ ] Create git tag v1.0.0 with release message
- [ ] Push tag to GitHub repository
- [ ] Build distribution packages with `python -m build`
- [ ] Verify wheel and sdist files
- [ ] Publish to PyPI using `twine upload dist/*`
- [ ] Test installation from PyPI: `pip install lmstrix`
- [ ] Verify all CLI commands work after PyPI install
- [ ] Create GitHub release from v1.0.0 tag
- [ ] Write comprehensive release notes for GitHub