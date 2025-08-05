# _github Directory

<!-- this_file: _github/README.md -->

This directory contains GitHub workflow configurations and templates for the LMStrix documentation system.

## 📁 Directory Structure

```
_github/
├── workflows/
│   ├── docs.yml           # Main documentation build and deploy workflow
│   └── docs-preview.yml   # PR preview and quality checks
├── ISSUE_TEMPLATE/
│   └── documentation.md   # Documentation issue template
├── pull_request_template.md  # PR template
└── README.md             # This file
```

## 🔄 Workflows

### `docs.yml` - Main Documentation Workflow

**Triggers:**
- Push to `main` or `develop` branches (paths: `src_docs/**`, `src/lmstrix/**`)
- Pull requests to `main` (same paths)
- Manual workflow dispatch

**Jobs:**
1. **Build** - Builds MkDocs documentation from `src_docs/`
2. **Deploy** - Deploys to GitHub Pages (main branch only)
3. **Quality Check** - Validates links and structure
4. **Performance** - Tests build performance

**Key Features:**
- ✅ Full MkDocs Material theme support
- ✅ Git revision date plugin for last modified dates
- ✅ Minification for optimized loading
- ✅ Strict build mode to catch errors
- ✅ Automatic GitHub Pages deployment
- ✅ Link validation and structure checks
- ✅ Performance benchmarking

### `docs-preview.yml` - Documentation Preview

**Triggers:**
- Pull requests to `main` (paths: `src_docs/**`, `src/lmstrix/**`)

**Jobs:**
1. **Preview** - Builds documentation and creates preview artifact
2. **Accessibility Check** - Basic accessibility validation
3. **Mobile Preview** - Mobile responsiveness checks

**Key Features:**
- 🔍 PR comment with preview summary
- 📦 Downloadable preview artifact
- ♿ Accessibility validation
- 📱 Mobile responsiveness checks
- 📊 Build statistics and change summary

## 🛠️ Setup Instructions

### 1. Copy to `.github` Directory

To activate these workflows, copy this entire `_github` directory to `.github` in your repository root:

```bash
# From the repository root
cp -r _github .github
```

### 2. Enable GitHub Pages

1. Go to your repository **Settings** → **Pages**
2. Set **Source** to "GitHub Actions"
3. The documentation will be available at: `https://[username].github.io/[repository]/`

### 3. Configure Repository Permissions

Ensure the following permissions in **Settings** → **Actions** → **General**:

- ✅ **Workflow permissions**: "Read and write permissions"
- ✅ **Allow GitHub Actions to create and approve pull requests**

### 4. Set Branch Protection (Optional)

For production repositories, consider setting up branch protection:

1. **Settings** → **Branches** → **Add rule**
2. Branch pattern: `main`
3. ✅ **Require status checks to pass**
4. ✅ **Require branches to be up to date**
5. Select: `build`, `quality-check`, `preview`

## 📚 Documentation Workflow

### For Contributors

1. **Make Changes**: Edit files in `src_docs/md/`
2. **Test Locally**: 
   ```bash
   cd src_docs
   mkdocs serve
   ```
3. **Create PR**: Push changes and create pull request
4. **Review Preview**: Check the PR comment for preview link
5. **Address Feedback**: Fix any issues found by quality checks

### For Maintainers

1. **Review PR**: Check preview and quality check results
2. **Merge**: Merge to main triggers automatic deployment
3. **Verify**: Check deployed documentation at GitHub Pages URL

## 🔧 Customization

### Workflow Customization

**Add new quality checks** in `docs.yml`:
```yaml
- name: Custom Check
  run: |
    cd src_docs
    # Your custom validation script
```

**Modify build dependencies** in both workflows:
```yaml
- name: Install dependencies
  run: |
    pip install mkdocs mkdocs-material
    pip install your-additional-plugin
```

**Change trigger paths**:
```yaml
on:
  push:
    paths:
      - 'src_docs/**'
      - 'your-custom-path/**'
```

### Template Customization

**Documentation Issue Template**: Edit `ISSUE_TEMPLATE/documentation.md`
**PR Template**: Edit `pull_request_template.md`

### GitHub Pages Configuration

**Custom domain**: Add `CNAME` file to `docs/` directory
**Custom 404 page**: Add `404.html` to `src_docs/md/`

## 🚨 Troubleshooting

### Common Issues

**Build Fails**:
- Check MkDocs configuration syntax
- Verify all referenced files exist
- Review workflow logs for specific errors

**Pages Not Deploying**:
- Ensure GitHub Pages is enabled
- Check workflow permissions
- Verify `docs/` directory contains built files

**Quality Checks Fail**:
- Fix broken internal links
- Ensure all required files exist
- Check navigation structure in `mkdocs.yml`

**Preview Not Available**:
- Check if workflow completed successfully
- Download artifact manually from workflow run
- Verify PR targets the correct branch

### Debug Commands

```bash
# Test locally
cd src_docs
mkdocs build --verbose --strict

# Check configuration
python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"

# Validate links manually
grep -r "\]\(" md/ | grep -v "http"
```

## 📞 Support

If you encounter issues with these workflows:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review workflow run logs for specific errors
3. Create an issue using the documentation template
4. Check MkDocs and Material theme documentation

## 🔄 Workflow Updates

This workflow configuration is designed to be:
- **Maintainable**: Clear structure and documentation
- **Reliable**: Multiple quality checks and validations
- **Efficient**: Caching and optimized builds
- **Accessible**: Accessibility and mobile checks
- **User-friendly**: Clear preview and feedback

When updating workflows, please:
1. Test changes on a feature branch first
2. Update this README with any new features
3. Maintain backward compatibility when possible
4. Document any breaking changes