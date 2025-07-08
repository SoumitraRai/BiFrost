#!/usr/bin/env bash
# Script to check if all tests pass

echo "Running all tests and capturing results..."

# Run pytest and capture the exit code
cd /home/soumitra/Projects/BiFrost/ProxyVPN && python -m pytest -v > /tmp/pytest_output.txt 2>&1
exit_code=$?

# Check if any tests failed
if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed successfully!"
    exit 0
else
    echo "❌ Some tests failed. See details in /tmp/pytest_output.txt"
    cat /tmp/pytest_output.txt
    exit 1
fi
