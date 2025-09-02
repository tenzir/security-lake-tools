# Development Guide

## Running from Source

There are several ways to run the script from the source tree:

### Method 1: Using uvx with local path (Quickest for testing)

```bash
# From anywhere, point to your local development directory
uvx --from /path/to/security-lake-tools security-lake-tools --help

# Or from within the project directory
uvx --from . security-lake-tools --help
```

### Method 2: Using uv run (Recommended for development)

```bash
# From the project root directory
uv run python -m security_lake_tools.create_source --help

# Or with arguments
uv run python -m security_lake_tools.create_source 1001 \
  --external-id test \
  --region us-east-1
```

### Method 2: Install in editable mode

```bash
# Install the package in editable/development mode
uv pip install -e .

# Now you can use the command directly
security-lake-tools --help
```

### Method 3: Direct Python execution

```bash
# Make sure dependencies are installed
uv pip install boto3

# Run directly
python src/security_lake_tools/create_source.py --help
```

### Method 4: Using PYTHONPATH

```bash
# Add src to PYTHONPATH and run
PYTHONPATH=src:$PYTHONPATH python -m security_lake_tools.create_source --help
```

## Development Workflow

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/security-lake-tools
cd security-lake-tools

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
uv pip install -e ".[dev]"
```

Note: The virtual environment is required for `uv pip install`. Alternatively, you can use `uv run` which handles the environment automatically.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=security_lake_tools

# Run specific test file
uv run pytest tests/test_create_source.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run black src tests

# Check formatting (no changes)
uv run black --check src tests

# Lint code
uv run ruff check src tests

# Fix linting issues
uv run ruff check --fix src tests

# Type checking
uv run mypy src
```

### Building the Package

```bash
# Build distributions
uv build

# Check the built files
ls -la dist/
```

### Testing the Built Package

```bash
# Create a test virtual environment
uv venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install the built wheel
uv pip install dist/security_lake_tools-*.whl

# Test it works
security-lake-tools --help

# Clean up
deactivate
rm -rf test-env
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (if you have one)
3. Commit changes
4. Create and push a tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. Create a GitHub release
6. The GitHub Action will automatically publish to PyPI

## Testing PyPI Publishing

You can test the publishing process using TestPyPI:

```bash
# Build the package
uv build

# Upload to TestPyPI (requires account and API token)
uv publish --repository testpypi

# Test installation from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ security-lake-tools
```
