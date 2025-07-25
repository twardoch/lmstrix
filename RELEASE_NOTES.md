# Release Notes - LMStrix v1.0.30

## Overview

LMStrix v1.0.30 represents a mature, production-ready release of the toolkit for managing and testing LM Studio models with automatic context limit discovery.

## What is LMStrix?

LMStrix solves a critical problem with LM Studio: models often declare higher context limits than they can actually handle. This leads to runtime failures and wasted time. LMStrix automatically discovers the true operational context window for any model using an efficient binary search algorithm.

## Key Features

- **Automatic Context Discovery**: Binary search algorithm finds the actual usable context window
- **Native LM Studio Integration**: Direct integration via the official `lmstudio` SDK
- **Beautiful CLI**: Rich terminal interface with progress indicators and formatted output
- **Comprehensive Python API**: Full programmatic access to all functionality
- **Persistent Registry**: Tracks tested models and their verified context limits
- **Detailed Logging**: Complete test history for debugging and analysis

## Installation

```bash
pip install lmstrix
```

## PyPI Upload Instructions

To publish this release to PyPI, run:

```bash
python -m twine upload dist/*
```

You will need:
1. PyPI account credentials
2. API token configured (recommended) or username/password

For test uploads:
```bash
python -m twine upload --repository testpypi dist/*
```

## Quick Start

```bash
# Scan for available models
lmstrix scan

# Test a specific model
lmstrix test "llama-3.2-1b-instruct"

# Run inference with verified context
lmstrix infer "llama-3.2-1b-instruct" -p "Explain quantum computing"
```

## What's New in v1.0.30

- Enhanced documentation with GitHub Pages site
- Improved example scripts with better error handling  
- Fixed attribute access issues for embedding models
- Better error messages throughout
- Comprehensive logging for debugging

## Documentation

- GitHub Repository: [Your GitHub URL]
- Documentation Site: [Your GitHub Pages URL]
- PyPI Package: https://pypi.org/project/lmstrix/

## License

Apache-2.0