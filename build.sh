#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define log files
LOG_FILE="build.log.txt"
ERR_FILE="build.err.txt"

# Clean up previous build artifacts and logs
echo "Cleaning up previous build artifacts and logs..."
rm -f $LOG_FILE $ERR_FILE
rm -rf dist/

# Redirect stdout and stderr to log files
exec > >(tee -a "$LOG_FILE") 2> >(tee -a "$ERR_FILE" >&2)

# Lint and format
echo "Running linter and formatter..."
hatch run lint:all

# Run tests
echo "Running tests with coverage..."
hatch run cov

# Build the package
echo "Building the package..."
hatch build

echo "Build process completed successfully!"
echo "Check $LOG_FILE and $ERR_FILE for details."
