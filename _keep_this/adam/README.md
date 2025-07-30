# Simplified Prompt Templates - adam.toml

This directory contains simplified prompt templates demonstrating LMStrix's prompt system with the new `--text` and `--text_file` support.

## Overview

The `adam.toml` file contains various prompt templates that all use a single `{{text}}` placeholder. This simplification makes it easy to use any prompt with just the text content you want to process.

## Usage

### Basic CLI Usage

```bash
# Using --text for inline content
lmstrix infer <prompt_name> <model_id> --file_prompt adam.toml --text "Your text here"

# Using --text_file for file content
lmstrix infer <prompt_name> <model_id> --file_prompt adam.toml --text_file path/to/file.txt

# Direct prompt with placeholder
lmstrix infer "Summarize this: {{text}}" <model_id> --text "Your text here"
```

### Examples

```bash
# Abstractive Proposition Segmentation
lmstrix infer aps qwen3-14b-mlx --file_prompt adam.toml --text "Marie Curie won two Nobel Prizes."

# Text humanization
lmstrix infer humanize qwen3-14b-mlx --file_prompt adam.toml --text "The methodology employed..."

# Summary generation
lmstrix infer summary qwen3-14b-mlx --file_prompt adam.toml --text_file article.txt

# Code review
lmstrix infer code_review qwen3-14b-mlx --file_prompt adam.toml --text "def add(a,b): return a+b"
```

## Available Prompts

### Text Analysis & Processing
- **aps** - Abstractive Proposition Segmentation: breaks text into atomic facts
- **analyze** - Detailed analysis with multiple perspectives
- **summary** - Comprehensive summary generation
- **tldr** - Literary TLDR with 30% condensation
- **bullets** - Convert text to bullet points
- **outline** - Create structured outline

### Text Transformation
- **humanize** - Make AI text sound natural and conversational
- **rewrite** - Improve clarity and flow
- **tts_optimize** - Optimize for text-to-speech
- **translate** - Natural translation with flow

### Creative Tasks
- **song** - Song lyrics generation with guidelines
- **creative_write** - Creative writing from prompts

### Practical Tasks
- **code_review** - Code quality and security review
- **email** - Professional email drafting
- **instructions** - Step-by-step instructions
- **qa** - Question answering from context
- **explain** - Simple explanations
- **compare** - Compare and contrast analysis

## Demo Script

Run the demo script to see examples:

```bash
./adam.sh
```

Make sure to update the `MODEL_ID` in the script to match your LM Studio model.

## Features

- **Single placeholder**: All prompts use only `{{text}}` for simplicity
- **Embedded examples**: Each prompt includes guidelines and examples
- **No nested templates**: Direct, self-contained prompts
- **CLI integration**: Works seamlessly with `--text` and `--text_file` flags