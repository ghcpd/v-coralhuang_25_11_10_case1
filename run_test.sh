#!/bin/bash
# Test runner for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "=== Flask SearchableMixin Event Binding - Test Runner ==="
echo "OS: $(uname -s)"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest not found. Please run setup.sh first."
    exit 1
fi

echo "Python: $(python --version)"
echo "pytest: $(pytest --version)"
echo ""

# Run tests with coverage
echo "Running tests with coverage report..."
pytest test_search_events.py -v --tb=short --cov=. --cov-report=html --cov-report=term 2>&1 | tee logs/test_run.log

TEST_RESULT=${PIPESTATUS[0]}

echo ""
echo "=== Test Execution Complete ==="
echo "Log file: logs/test_run.log"
echo "Coverage report: htmlcov/index.html"

exit $TEST_RESULT
