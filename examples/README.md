# LMStrix Examples

This directory contains a comprehensive set of examples to demonstrate the usage of both the `lmstrix` command-line interface (CLI) and the Python library. These examples are designed to be run from the root of the project repository.

## How to Run the Examples

A convenience script, `run_all_examples.sh`, is provided to execute all the examples in this directory. To run it, simply execute the following command from the project root:

```bash
bash examples/run_all_examples.sh
```

**Note**: Most of the long-running operations within the example scripts (like model testing and inference) are commented out by default to prevent accidental execution. You can inspect each script and uncomment the relevant lines to run them fully.

## Directory Structure

-   `cli/`: Contains shell scripts that demonstrate the usage of the `lmstrix` CLI.
-   `python/`: Contains Python scripts that show how to use the `lmstrix` library.
-   `prompts/`: Contains sample TOML files with predefined prompts for different tasks.
-   `data/`: Contains sample data files used in the examples, such as a large text file for context testing.

## CLI Examples (`cli/`)

-   `basic_workflow.sh`: A complete, step-by-step workflow showing how to scan for models, list them, test one, and run inference.
-   `model_testing.sh`: Focused examples of the `lmstrix test` command, including how to test a specific model, force a re-test, and customize the test range.
-   `inference_examples.sh`: Demonstrates various ways to run inference, such as using system prompts, reading prompts from files, and streaming responses.

## Python Library Examples (`python/`)

-   `basic_usage.py`: Covers the fundamental operations of the library: scanning, listing, and running a simple inference.
-   `advanced_testing.py`: Shows more advanced context testing scenarios, like running a full scan on all untested models and forcing a re-test.
-   `custom_inference.py`: Illustrates how to customize the inference process with system prompts, streaming, and custom generation parameters.
-   `batch_processing.py`: An example of how to run inference on multiple models in a batch.

## Prompt Files (`prompts/`)

These files contain sample prompts that can be used with the `lmstrix` library. They are organized by task type:

-   `analysis.toml`
-   `creative.toml`
-   `coding.toml`
-   `qa.toml`

## Data Files (`data/`)

-   `sample_context.txt`: A large text file used for context length testing.
-   `test_questions.json`: A set of sample questions for use in question-answering scenarios.
