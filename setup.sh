#!/bin/bash
# Setup script for Linux/macOS

set -e

echo "=== Flask SearchableMixin Event Binding - Setup ==="
echo "OS: $(uname -s)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=== Setup Complete ==="
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests, use:"
echo "  bash run_test.sh"
