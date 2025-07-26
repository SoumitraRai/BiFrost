#!/usr/bin/env python3
"""
Run all tests for the BiFrost ProxyVPN system.
"""
import os
import sys
import pytest

def run_tests():
    """Run all tests in the tests directory."""
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the tests directory
    tests_dir = os.path.join(script_dir, 'tests')
    
    # Print test banner
    print("\n" + "="*80)
    print(" BiFrost ProxyVPN Test Suite ")
    print("="*80 + "\n")
    
    # Run pytest with coverage
    try:
        exit_code = pytest.main([
            '-xvs',                  # Verbose, stop on first failure, don't capture output
            '--cov=.',               # Measure coverage for all modules
            '--cov-report=term',     # Display coverage report in terminal
            '--cov-report=html:coverage_report',  # Generate HTML coverage report
            tests_dir                # Path to test directory
        ])
        
        if exit_code == 0:
            print("\n✅ All tests passed successfully!")
            print(f"\nHTML coverage report available at: {os.path.join(script_dir, 'coverage_report/index.html')}")
        else:
            print("\n❌ Some tests failed.")
        
        return exit_code
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
