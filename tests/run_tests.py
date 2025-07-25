#!/usr/bin/env python
"""Simple test runner script."""

import subprocess
import sys


def run_tests():
    """Run the test suite."""
    print("Running LMStrix test suite...")
    print("-" * 50)

    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
        "tests/",
    ]

    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
