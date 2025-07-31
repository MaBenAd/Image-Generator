#!/bin/bash

# Test runner script for the Django project

echo "🧪 Running Django Tests..."

# Check if coverage is available
if command -v coverage &> /dev/null; then
    echo "📊 Running tests with coverage..."
    coverage run --source='.' manage.py test
    coverage report
    coverage html
    echo "📁 Coverage report generated in htmlcov/"
else
    echo "⚠️  Coverage not available, running tests without coverage..."
    python3 manage.py test -v 2
fi

echo "✅ Tests completed!" 