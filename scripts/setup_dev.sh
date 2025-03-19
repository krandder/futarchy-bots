#!/bin/bash

# Exit on error
set -e

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python3 -m pip install --upgrade pip

# Install the package in editable mode with development dependencies
pip install -e .
pip install -r requirements.txt

# Print environment info
echo "✅ Development environment setup complete"
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip --version)"
echo ""
echo "To activate the environment, run:"
echo "source venv/bin/activate" 