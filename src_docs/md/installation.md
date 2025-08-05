---
# this_file: src_docs/md/installation.md
title: Installation Guide
description: Complete installation guide for LMStrix - multiple methods, development setup, and troubleshooting
---

# Installation Guide

This guide covers everything you need to install LMStrix and get it running on your system. LMStrix supports multiple installation methods and platforms.

## 🚀 Quick Install

### Using pip (Standard)

```bash
# Install from PyPI
pip install lmstrix

# Verify installation
lmstrix --help
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver, written in Rust.

```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install LMStrix with uv
uv pip install lmstrix

# Verify installation
lmstrix --help
```

!!! tip "Why uv?"
    uv is significantly faster than pip and provides better dependency resolution. It's particularly useful for Python development workflows and is our recommended installation method.

## 📋 System Requirements

### Minimum Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows 10+, macOS 10.15+, Linux (most distributions)
- **RAM**: 4GB minimum (8GB+ recommended for larger models)
- **Storage**: 500MB for LMStrix + space for your models

### Required Dependencies

LMStrix automatically installs these dependencies:

- `lmstudio-python` - Official LM Studio Python SDK
- `httpx` - Async HTTP client for API communication
- `pydantic` - Data validation and settings management
- `fire` - Command-line interface framework
- `rich` - Terminal formatting and progress indicators
- `tenacity` - Retry logic with exponential backoff
- `tiktoken` - Token counting for various models
- `loguru` - Advanced logging capabilities

### LM Studio Requirements

!!! warning "LM Studio Required"
    LMStrix requires [LM Studio](https://lmstudio.ai/) to be installed and running on your system. Download it from the official website and ensure it's configured properly.

**LM Studio Setup:**

1. Download and install LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Start LM Studio and enable the local server
3. Download at least one model
4. Verify the server is running (default: `http://localhost:1234`)

## 🔧 Development Installation

### From Source

For developers who want to contribute or use the latest features:

```bash
# Clone the repository
git clone https://github.com/your-organization/lmstrix.git
cd lmstrix

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

### Development Dependencies

The development installation includes additional tools:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `ruff` - Fast Python linter
- `mypy` - Static type checking
- `hatch` - Build system and project management

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/lmstrix --cov-report=html

# Run specific test categories
pytest -m "not integration"  # Unit tests only
pytest -m integration        # Integration tests only
```

### Code Quality Checks

```bash
# Format code
hatch run lint:fmt

# Check style and types
hatch run lint:all

# Individual tools
black .
ruff check .
mypy src/lmstrix
```

## 🐳 Docker Installation

### Using Docker

```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Install LMStrix
RUN uv pip install lmstrix

# Set working directory
WORKDIR /app

# Entry point
ENTRYPOINT ["lmstrix"]
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  lmstrix:
    build: .
    volumes:
      - ./data:/app/data
      - ./prompts:/app/prompts
    environment:
      - LMSTUDIO_BASE_URL=http://host.docker.internal:1234
    depends_on:
      - lmstudio
```

## 🌐 Virtual Environments

### Using venv

```bash
# Create virtual environment
python -m venv lmstrix-env

# Activate (Linux/macOS)
source lmstrix-env/bin/activate

# Activate (Windows)
lmstrix-env\Scripts\activate

# Install LMStrix
pip install lmstrix
```

### Using conda

```bash
# Create conda environment
conda create -n lmstrix python=3.11

# Activate environment
conda activate lmstrix

# Install LMStrix
pip install lmstrix
```

### Using pipenv

```bash
# Create Pipfile and install
pipenv install lmstrix

# Activate shell
pipenv shell
```

## ⚙️ Configuration

### Environment Variables

LMStrix can be configured using environment variables:

```bash
# LM Studio server URL (default: http://localhost:1234)
export LMSTUDIO_BASE_URL="http://localhost:1234"

# Default timeout for API calls (default: 300 seconds)
export LMSTRIX_TIMEOUT="300"

# Enable debug logging
export LMSTRIX_DEBUG="true"

# Model registry file location
export LMSTRIX_REGISTRY_PATH="~/.lmstrix/models.json"
```

### Configuration File

Create a configuration file at `~/.lmstrix/config.json`:

```json
{
  "lmstudio_base_url": "http://localhost:1234",
  "default_timeout": 300,
  "max_retries": 3,
  "debug": false,
  "registry_path": "~/.lmstrix/models.json",
  "safety_threshold": 65536
}
```

## ✅ Verification

### Test Installation

```bash
# Check LMStrix version
lmstrix --version

# Test LM Studio connection
lmstrix scan

# Run basic health check
lmstrix list
```

### Expected Output

```bash
$ lmstrix scan
🔍 Scanning for models...
✅ Found 3 models in LM Studio
📋 Updated model registry

$ lmstrix list
Model                           Size    Context    Status
llama-3.2-3b-instruct          3.2B    Unknown    Not tested
mistral-7b-instruct            7.1B    Unknown    Not tested
codellama-13b-python           13.0B   Unknown    Not tested
```

## 🔧 Troubleshooting

### Common Issues

#### 1. LM Studio Connection Failed

**Problem:** `ConnectionError: Could not connect to LM Studio`

**Solutions:**
- Ensure LM Studio is running
- Check the server URL (default: `http://localhost:1234`)
- Verify firewall settings
- Try different port if 1234 is occupied

#### 2. Python Version Compatibility

**Problem:** `Python 3.11+ is required`

**Solutions:**
- Update Python to 3.11 or higher
- Use pyenv to manage multiple Python versions
- Check your virtual environment Python version

#### 3. Permission Errors

**Problem:** `Permission denied when installing`

**Solutions:**
```bash
# Use user installation
pip install --user lmstrix

# Or create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install lmstrix
```

#### 4. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'lmstrix'`

**Solutions:**
- Verify installation: `pip list | grep lmstrix`
- Check Python path: `python -c "import sys; print(sys.path)"`
- Reinstall: `pip uninstall lmstrix && pip install lmstrix`

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Run with `--debug` flag for detailed output
2. **Search issues**: Check [GitHub Issues](https://github.com/your-organization/lmstrix/issues)
3. **Report bugs**: Create a new issue with detailed information
4. **Join discussions**: Participate in community discussions

### System Information

To help with troubleshooting, gather system information:

```bash
# Python version
python --version

# LMStrix version
lmstrix --version

# System information
uname -a  # Linux/macOS
systeminfo  # Windows

# LM Studio status
curl http://localhost:1234/v1/models
```

## 🚀 Next Steps

Once LMStrix is installed and verified:

1. **[Quick Start](quickstart.md)** - Learn basic usage and commands
2. **[Configuration](configuration.md)** - Customize LMStrix for your needs
3. **[CLI Interface](cli-interface.md)** - Master the command-line tools
4. **[Context Testing](context-testing.md)** - Optimize your models

---

*Installation complete! Ready to supercharge your LM Studio experience? 🚀*