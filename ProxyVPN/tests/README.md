# BiFrost ProxyVPN Test Suite

This directory contains tests for the BiFrost ProxyVPN system.

## Test Structure

- `test_proxy.py`: Tests for the main proxy functionality
- `test_payment_filter.py`: Tests for the payment detection and filtering
- `test_approval_mechanism.py`: Tests for the approval mechanism API
- `test_ml_payment_detector.py`: Tests for the machine learning payment detector
- `test_metrics.py`: Tests for the metrics collection

## Running Tests

To run the tests, you'll need to install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
./run_tests.py
```

Or use pytest directly:

```bash
pytest -xvs --cov=. --cov-report=term --cov-report=html:coverage_report tests/
```

## Coverage Reports

Running the tests will generate a coverage report in HTML format in the `coverage_report` directory.
Open `coverage_report/index.html` in a browser to view the coverage details.

## Writing New Tests

When adding new functionality to the system, make sure to add corresponding tests.
Each test module should correspond to a component of the system, and test files should
be named `test_*.py` to be discovered by pytest.

## Troubleshooting

If you encounter import errors when running the tests, make sure:

1. All required dependencies are installed
2. The tests are running from the correct directory
3. PYTHONPATH includes the project root directory
