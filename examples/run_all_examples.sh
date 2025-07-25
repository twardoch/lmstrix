#!/bin/bash
#
# This script runs all the examples in the `cli` and `python` directories.
# It's a way to functionally test that all example code is working as expected.
#
# NOTE: This script assumes you have a model downloaded in LM Studio
# and that the identifier 'ultron-summarizer-1b' will match it. If not, please edit the
# example files to use an identifier for a model you have.
#

set -e # Exit on any error

echo "===== Running All LMStrix Examples ====="

# --- Running CLI Examples ---
echo -e "

--- Testing CLI Examples ---"
echo "NOTE: The CLI scripts have a placeholder model identifier ('ultron-summarizer-1b')."
echo "Please edit them if you don't have a model matching that ID."

echo -e "
>>> Running basic_workflow.sh"
bash "$(dirname "$0")/cli/basic_workflow.sh"

echo -e "
>>> Running model_testing.sh"
bash "$(dirname "$0")/cli/model_testing.sh"

echo -e "
>>> Running inference_examples.sh"
bash "$(dirname "$0")/cli/inference_examples.sh"

echo -e "
--- CLI Examples Complete ---"


# --- Running Python Examples ---
echo -e "

--- Testing Python Examples ---"
echo "NOTE: The Python scripts will use the first model they find."

echo -e "
>>> Running basic_usage.py"
python3 "$(dirname "$0")/python/basic_usage.py"

echo -e "
>>> Running advanced_testing.py"
python3 "$(dirname "$0")/python/advanced_testing.py"

echo -e "
>>> Running custom_inference.py"
python3 "$(dirname "$0")/python/custom_inference.py"

echo -e "
>>> Running batch_processing.py"
python3 "$(dirname "$0")/python/batch_processing.py"

echo -e "
--- Python Examples Complete ---"


echo -e "

===== All Examples Finished Successfully ====="