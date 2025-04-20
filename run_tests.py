#!/usr/bin/env python3
import unittest
import os

if __name__ == "__main__":
    # Discover tests starting from the 'tests' directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir='tests', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with appropriate status code for CI/CD
    if result.wasSuccessful():
        exit(0)
    else:
        exit(1) 