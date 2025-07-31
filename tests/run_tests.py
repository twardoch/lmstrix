#!/usr/bin/env python
"""Simple test runner script."""

import subprocess
import sys

from lmstrix.utils.logging import logger


def run_tests() -> int:
    """Run the test suite."""
    logger.info("Running LMStrix test suite...")
    logger.info("-" * 50)

    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
        "tests/",
    ]

    result = subprocess.run(cmd, check=True)  # noqa: S603

    if result.returncode == 0:
        logger.info("\n✅ All tests passed!")
    else:
        logger.info("\n❌ Some tests failed.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
