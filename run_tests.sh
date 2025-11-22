#!/bin/bash
# Test runner script for tt.py

set -e

echo "🧪 Running Time Tracker Test Suite..."
echo ""

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "⚠️  pytest not found. Installing test dependencies..."
    pip3 install -r requirements-dev.txt
    echo ""
fi

# Parse arguments
if [ "$1" == "coverage" ]; then
    echo "📊 Running tests with coverage report..."
    python3 -m pytest test_tt.py -v --cov=tt --cov-report=term-missing --cov-report=html
    echo ""
    echo "✅ Coverage report generated in htmlcov/index.html"
elif [ "$1" == "quick" ]; then
    echo "⚡ Running quick test (no verbose)..."
    python3 -m pytest test_tt.py
elif [ "$1" == "class" ] && [ -n "$2" ]; then
    echo "🎯 Running test class: $2"
    python3 -m pytest "test_tt.py::$2" -v
elif [ "$1" == "watch" ]; then
    echo "👀 Watching for changes..."
    if ! command -v pytest-watch &> /dev/null; then
        echo "Installing pytest-watch..."
        pip3 install pytest-watch
    fi
    ptw test_tt.py -- -v
else
    echo "📋 Running all tests (verbose)..."
    python3 -m pytest test_tt.py -v
fi

echo ""
echo "✨ Done!"

