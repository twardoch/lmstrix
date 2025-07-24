#!/bin/bash
# This script executes all the example scripts in the `cli` and `python` directories.
# It is designed to be run from the root of the project.

set -e # Exit immediately if a command exits with a non-zero status.

echo "Running all examples..."

# --- Run CLI Examples ---
echo "\n--- Running CLI Examples ---"

# Note: The CLI examples themselves have their main commands commented out
# to avoid long run times. This script will execute them, but they will
# mostly print information rather than perform the actual tests or inferences.

chmod +x examples/cli/*.sh

for script in examples/cli/*.sh; do
    echo "\nExecuting $script..."
    bash "$script"
    echo "Finished $script."
done

# --- Run Python Examples ---
echo "\n--- Running Python Examples ---"

# Similarly, the Python examples have their core logic commented out.
# This will run the scripts, but they will not perform the long-running tasks.

for script in examples/python/*.py; do
    echo "\nExecuting $script..."
    # Use python -m to run the module from the project root
    module_name=$(basename -s .py "$script")
    python -m "examples.python.$module_name"
    echo "Finished $script."
done

echo "\nAll examples have been executed."
