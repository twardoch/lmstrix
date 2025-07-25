# LMStrix Usage Examples

This directory contains a comprehensive set of runnable examples demonstrating the features of the LMStrix CLI and Python API.

## Prerequisites

1.  **LMStrix Installed**: Ensure you have installed LMStrix (`pip install lmstrix`).
2.  **LM Studio Running**: For most examples, you need LM Studio running in the background with a model loaded.
3.  **Model Downloaded**: You must have at least one model downloaded in LM Studio.

**Note**: Many scripts use a placeholder model identifier like `"ultron-summarizer-1b"`. You may need to edit these scripts to use an identifier that matches a model you have downloaded (e.g., `"llama-3.2-3b-instruct"`, `"qwen"`). You can see available model identifiers by running `lmstrix list`.

## How to Run Examples

You can run all examples at once using the main runner script. Open your terminal and run:

```bash
bash run_all_examples.sh
```

Alternatively, you can run each example individually.

---

## CLI Examples (`cli/`)

These examples are shell scripts that show how to use the `lmstrix` command-line tool.

-   **`basic_workflow.sh`**: Demonstrates the core end-to-end workflow: scanning for models, listing them, running a context test, and performing inference.
-   **`model_testing.sh`**: Provides focused examples of the `test` command, showing different strategies like binary search vs. linear ramp-up, forcing re-tests, and using custom prompts.
-   **`inference_examples.sh`**: Showcases the `infer` command, including how to use custom system prompts, adjust inference parameters, and load prompts from files.

### To run a specific CLI example:

```bash
bash cli/basic_workflow.sh
```

---

## Python API Examples (`python/`)

These examples are Python scripts that illustrate how to use the LMStrix library in your own projects.

-   **`basic_usage.py`**: Covers the fundamentals: initializing the client, scanning and listing models, and running a simple inference task.
-   **`advanced_testing.py`**: Dives deeper into context testing, showing how to run different test patterns (`BINARY`, `LINEAR`) and save the results.
-   **`custom_inference.py`**: Demonstrates advanced inference techniques, such as setting a custom system prompt, adjusting temperature, and prompting for structured (JSON) output.
-   **`batch_processing.py`**: Shows how to work with multiple models at once, including batch testing all untested models and running the same prompt across your entire model library.

### To run a specific Python example:

```bash
python3 python/basic_usage.py
```

---

## Prompt & Data Files

-   **`prompts/`**: Contains sample `.toml` files that show how to create structured, reusable prompt templates for different tasks (coding, analysis, etc.). These are used in some of the inference examples.
-   **`data/`**: Contains sample data used by the examples.
    -   `sample_context.txt`: A large text file used for context length testing.
    -   `test_questions.json`: A set of questions for demonstrating question-answering scenarios.