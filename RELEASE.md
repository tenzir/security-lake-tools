# Release Process

## Prerequisites

1. **PyPI Account**: Create at <https://pypi.org/account/register/>
2. **TestPyPI Account**: Create at <https://test.pypi.org/account/register/>
3. **GitHub Repository**: Push code to GitHub

## Testing with TestPyPI

### 1. Build the Package

```bash
uv build
```

### 2. Upload to TestPyPI

```bash
# Set your TestPyPI token
export UV_PUBLISH_TOKEN=pypi-xxxxx
export UV_PUBLISH_URL=https://test.pypi.org/legacy/
uv publish
```

### 3. Test Installation

```bash
# Test with pip
uv pip install --index-url https://test.pypi.org/simple/ \
               --extra-index-url https://pypi.org/simple/ \
               security-lake-tools

# Test with uvx
uvx --index https://test.pypi.org/simple/ \
    security-lake-tools --help
```

## Production Release

### Option 1: Manual Release with UV

1. **Update Version** in `pyproject.toml`
2. **Build**:

   ```bash
   uv build
   ```

3. **Upload to PyPI**:

   ```bash
   export UV_PUBLISH_TOKEN=pypi-xxxxx  # Your real PyPI token
   uv publish
   ```

### Option 2: GitHub Release (Recommended)

1. **Set up Trusted Publishing** on PyPI:
   - Go to <https://pypi.org/manage/account/publishing/>
   - Add a new publisher:
     - Owner: yourusername
     - Repository: security-lake-tools
     - Workflow: publish.yml
     - Environment: pypi

2. **Create GitHub Environments**:
   - Go to Settings → Environments in your GitHub repo
   - Create `pypi` environment
   - Create `testpypi` environment

3. **Create a Release**:

   ```bash
   # Tag the version
   git tag v0.1.0
   git push origin v0.1.0
   ```

   - Go to GitHub → Releases → Create Release
   - Choose the tag
   - GitHub Actions will automatically publish to PyPI

## Version Bumping

Before each release:

1. Update version in `pyproject.toml`
2. Commit: `git commit -am "Bump version to 0.2.0"`
3. Tag: `git tag v0.2.0`
4. Push: `git push && git push --tags`

## Post-Release Verification

```bash
# Install from PyPI
uvx security-lake-tools --version

# Check PyPI page
open https://pypi.org/project/security-lake-tools/
```
