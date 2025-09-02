#!/bin/bash

# Script to test installation from TestPyPI

# Create a test environment
echo "Creating test environment..."
uv venv test-pypi-env
source test-pypi-env/bin/activate

# Install from TestPyPI
echo "Installing from TestPyPI..."
uv pip install --index-url https://test.pypi.org/simple/ \
              --extra-index-url https://pypi.org/simple/ \
              security-lake-tools

# Test the command
echo "Testing the command..."
security-lake-tools --help

# Test with uvx
echo "Testing with uvx..."
deactivate
uvx --from https://test.pypi.org/simple/ \
    --index-url https://test.pypi.org/simple/ \
    security-lake-tools --help

# Clean up
echo "Cleaning up..."
rm -rf test-pypi-env