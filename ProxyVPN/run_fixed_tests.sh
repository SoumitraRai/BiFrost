#!/usr/bin/env bash
# Script to run the failing test

echo "Running the previously failing ML detector test..."
python -m pytest -xvs tests/test_ml_payment_detector.py::TestMLPaymentDetector::test_extract_features

if [ $? -eq 0 ]; then
    echo -e "\n✅ The test now passes! The issue has been fixed."
    echo -e "\nTrying all tests to make sure everything passes..."
    ./run_tests.py
else
    echo -e "\n❌ The test still fails. Further debugging needed."
fi
