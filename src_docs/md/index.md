---
# this_file: src_docs/md/index.md
title: LMStrix Documentation
description: Professional Python toolkit for LM Studio with Adaptive Context Optimization
---

# LMStrix Documentation

Welcome to **LMStrix** - a professional Python toolkit designed to supercharge your interaction with [LM Studio](https://lmstudio.ai/). LMStrix provides powerful command-line interface (CLI) and Python API for managing, testing, and running local language models, with our standout feature: **Adaptive Context Optimization**.

## 🚀 Quick Overview

LMStrix revolutionizes how you work with local language models by automatically discovering their true operational context limits through intelligent binary search algorithms, while providing beautiful verbose logging, smart model management, and flexible inference capabilities.

---

## 📚 Documentation Structure

### 🔧 Getting Started
Essential information to get you up and running with LMStrix quickly and efficiently.

### 📖 User Guide  
Comprehensive guides for both CLI and Python API usage, covering all core functionality.

### 🎯 Advanced Topics
Deep dives into specialized features, optimization techniques, and advanced use cases.

---

## 📋 Table of Contents & Chapter Summaries

### **Chapter 1: [Installation](installation.md)**
**TLDR:** *Complete installation guide covering pip, uv, development setup, and system requirements. Get LMStrix running in under 5 minutes.*

- Multiple installation methods (pip, uv, from source)
- Development environment setup
- System requirements and dependencies
- Verification steps and troubleshooting
- Docker and virtual environment configurations

---

### **Chapter 2: [Quick Start](quickstart.md)**
**TLDR:** *Hit the ground running with essential commands and workflows. Learn the core LMStrix operations through practical examples.*

- First-time setup and configuration
- Essential CLI commands walkthrough
- Basic Python API usage examples
- Common workflows and patterns
- Your first context optimization test

---

### **Chapter 3: [Configuration](configuration.md)**
**TLDR:** *Master LMStrix configuration options, environment variables, and customization settings for optimal performance.*

- Configuration file structure and locations
- Environment variable reference
- LM Studio integration settings
- Safety and performance tuning
- Custom profiles and presets

---

### **Chapter 4: [CLI Interface](cli-interface.md)**
**TLDR:** *Complete command-line reference with examples, options, and advanced usage patterns for power users.*

- Complete command reference (`scan`, `list`, `test`, `infer`)
- Advanced CLI options and flags
- Output formatting and verbosity controls
- Batch processing and automation
- Integration with shell scripts and workflows

---

### **Chapter 5: [Python API](python-api.md)**
**TLDR:** *Comprehensive Python API documentation with code examples, class references, and integration patterns for developers.*

- Core API classes and methods
- Async/await patterns and best practices
- Error handling and exception management
- Integration examples and use cases
- Advanced programmatic usage

---

### **Chapter 6: [Context Testing](context-testing.md)**
**TLDR:** *Deep dive into LMStrix's signature Adaptive Context Optimization feature - how it works, configuration, and best practices.*

- Binary search algorithm explanation
- Safety mechanisms and thresholds
- Testing strategies and methodologies
- Performance optimization techniques
- Troubleshooting failed tests

---

### **Chapter 7: [Model Management](model-management.md)**
**TLDR:** *Master model discovery, registry management, persistence, and organization for efficient model workflows.*

- Model discovery and scanning
- Registry structure and persistence
- Model state management (loaded/unloaded)
- Batch operations and automation
- Model metadata and tagging

---

### **Chapter 8: [Prompt Templating](prompt-templating.md)**
**TLDR:** *Advanced prompt engineering with TOML templates, variable substitution, and reusable prompt libraries.*

- TOML template syntax and structure
- Variable substitution and templating
- Template organization and libraries
- Dynamic prompt generation
- Best practices for prompt design

---

### **Chapter 9: [Performance & Optimization](performance.md)**
**TLDR:** *Performance tuning, monitoring, optimization strategies, and advanced configuration for production deployments.*

- Performance monitoring and metrics
- Memory and resource optimization
- Concurrent processing strategies
- Production deployment patterns
- Troubleshooting and debugging

---

## 🎯 Key Features at a Glance

!!! tip "Core Capabilities"
    - **🔍 Automatic Context Discovery** - Binary search algorithm finds true operational context limits
    - **📊 Beautiful Verbose Logging** - Enhanced stats with emojis, timing, and token usage
    - **🚀 Smart Model Management** - Persistent models reduce loading overhead
    - **🎯 Flexible Inference Engine** - Powerful templating with percentage-based output control
    - **📋 Model Registry** - Track models, limits, and test results with JSON persistence
    - **🛡️ Safety Controls** - Configurable thresholds prevent system crashes
    - **💻 Rich CLI Interface** - Beautiful terminal output with progress indicators
    - **📈 Compact Test Output** - Live-updating tables without verbose clutter

## 🚦 Getting Started

Ready to dive in? Start with our [Installation Guide](installation.md) to get LMStrix set up, then follow the [Quick Start](quickstart.md) tutorial to run your first context optimization test.

!!! example "Quick Install"
    ```bash
    # Using pip
    pip install lmstrix
    
    # Using uv (recommended)
    uv pip install lmstrix
    
    # Verify installation
    lmstrix --help
    ```

## 🤝 Community & Support

- **GitHub Repository**: [github.com/your-organization/lmstrix](https://github.com/your-organization/lmstrix)
- **PyPI Package**: [pypi.org/project/lmstrix](https://pypi.org/project/lmstrix)
- **Issue Tracker**: Report bugs and request features
- **Discussions**: Join the community conversations

---

*Happy modeling with LMStrix! 🚀*