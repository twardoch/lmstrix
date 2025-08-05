---
# this_file: src_docs/md/configuration.md
title: Configuration Guide
description: Master LMStrix configuration options, environment variables, and customization settings
---

# Configuration Guide

LMStrix offers extensive configuration options to customize its behavior for your specific needs. This guide covers all configuration methods, from environment variables to configuration files.

## 🎛️ Configuration Methods

LMStrix supports multiple configuration methods with the following priority order:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Default values** (lowest priority)

## 🌍 Environment Variables

### Core Settings

```bash
# LM Studio server configuration
export LMSTUDIO_BASE_URL="http://localhost:1234"  # Default LM Studio URL
export LMSTUDIO_API_KEY=""                        # API key if required

# Request timeout settings
export LMSTRIX_TIMEOUT="300"                      # API request timeout (seconds)
export LMSTRIX_CONNECT_TIMEOUT="30"               # Connection timeout (seconds)

# Model registry and data paths
export LMSTRIX_REGISTRY_PATH="~/.lmstrix/models.json"    # Model registry file
export LMSTRIX_CONFIG_PATH="~/.lmstrix/config.json"      # Configuration file
export LMSTRIX_CACHE_DIR="~/.lmstrix/cache"              # Cache directory

# Safety and performance
export LMSTRIX_SAFETY_THRESHOLD="65536"           # Default context limit threshold
export LMSTRIX_MAX_RETRIES="3"                    # API retry attempts
export LMSTRIX_RETRY_DELAY="1.0"                  # Retry delay (seconds)

# Logging and debugging
export LMSTRIX_DEBUG="false"                      # Enable debug logging
export LMSTRIX_LOG_LEVEL="INFO"                   # Log level (DEBUG, INFO, WARNING, ERROR)
export LMSTRIX_LOG_FILE=""                        # Log file path (empty = console only)

# Output formatting
export LMSTRIX_NO_COLOR="false"                   # Disable colored output
export LMSTRIX_NO_EMOJI="false"                   # Disable emoji in output
export LMSTRIX_COMPACT_OUTPUT="false"             # Use compact output format
```

### Example Environment Setup

Create a `.env` file for your project:

```bash
# .env file
LMSTUDIO_BASE_URL=http://localhost:1234
LMSTRIX_SAFETY_THRESHOLD=32768
LMSTRIX_DEBUG=true
LMSTRIX_LOG_LEVEL=DEBUG
LMSTRIX_TIMEOUT=600
```

Load it in your shell:

```bash
# Load environment variables
source .env

# Or use with specific commands
env $(cat .env | xargs) lmstrix scan --verbose
```

## 📁 Configuration Files

### Main Configuration File

Create `~/.lmstrix/config.json`:

```json
{
  "lmstudio": {
    "base_url": "http://localhost:1234",
    "api_key": null,
    "timeout": 300,
    "connect_timeout": 30,
    "verify_ssl": true
  },
  "safety": {
    "max_context_threshold": 65536,
    "enable_safety_checks": true,
    "max_memory_usage_mb": 8192,
    "max_concurrent_tests": 1
  },
  "performance": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "retry_backoff": 2.0,
    "keep_models_loaded": true,
    "cache_results": true
  },
  "output": {
    "verbose_by_default": false,
    "use_color": true,
    "use_emoji": true,
    "compact_tables": false,
    "show_progress": true
  },
  "logging": {
    "level": "INFO",
    "file": null,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "rotate": true,
    "max_size_mb": 10
  },
  "paths": {
    "registry_file": "~/.lmstrix/models.json",
    "cache_dir": "~/.lmstrix/cache",
    "prompts_dir": "~/.lmstrix/prompts"
  }
}
```

### Profile-Based Configuration

Create multiple configuration profiles:

```bash
# Development profile
~/.lmstrix/profiles/dev.json
{
  "safety": {
    "max_context_threshold": 16384
  },
  "logging": {
    "level": "DEBUG"
  },
  "output": {
    "verbose_by_default": true
  }
}

# Production profile  
~/.lmstrix/profiles/prod.json
{
  "safety": {
    "max_context_threshold": 131072,
    "enable_safety_checks": true
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/lmstrix.log"
  },
  "performance": {
    "max_retries": 5,
    "keep_models_loaded": true
  }
}
```

Use profiles with:

```bash
# Load specific profile
lmstrix --profile dev scan

# Or set environment variable
export LMSTRIX_PROFILE=prod
lmstrix test --all
```

## ⚙️ LM Studio Integration

### Connection Settings

Configure how LMStrix connects to LM Studio:

```json
{
  "lmstudio": {
    "base_url": "http://localhost:1234",
    "api_key": null,
    "endpoints": {
      "models": "/v1/models",
      "chat": "/v1/chat/completions",
      "completions": "/v1/completions"
    },
    "headers": {
      "User-Agent": "LMStrix/1.0",
      "Accept": "application/json"
    },
    "timeout": 300,
    "connect_timeout": 30,
    "read_timeout": 300,
    "verify_ssl": true,
    "follow_redirects": true
  }
}
```

### Authentication

If your LM Studio instance requires authentication:

```bash
# Set API key
export LMSTUDIO_API_KEY="your-api-key"

# Or in config file
{
  "lmstudio": {
    "api_key": "your-api-key",
    "auth_type": "bearer"  # or "basic"
  }
}
```

### Custom LM Studio Setup

For non-standard LM Studio configurations:

```json
{
  "lmstudio": {
    "base_url": "https://remote-lmstudio.example.com",
    "port": 8080,
    "use_https": true,
    "custom_endpoints": {
      "health": "/health",
      "models": "/api/v1/models",
      "chat": "/api/v1/chat"
    }
  }
}
```

## 🛡️ Safety Configuration

### Context Limits and Thresholds

```json
{
  "safety": {
    "max_context_threshold": 65536,
    "default_test_threshold": 32768,
    "emergency_stop_threshold": 131072,
    "enable_safety_checks": true,
    "safety_margin_tokens": 1024,
    "max_test_iterations": 20,
    "min_test_context": 512
  }
}
```

### Memory and Resource Limits

```json
{
  "safety": {
    "max_memory_usage_mb": 8192,
    "max_concurrent_tests": 1,
    "test_timeout_seconds": 300,
    "enable_resource_monitoring": true,
    "memory_check_interval": 30
  }
}
```

### Failure Handling

```json
{
  "safety": {
    "max_consecutive_failures": 3,
    "failure_cooldown_seconds": 60,
    "auto_reduce_context_on_failure": true,
    "context_reduction_factor": 0.8,
    "enable_automatic_recovery": true
  }
}
```

## 🚀 Performance Configuration

### Retry Logic

```json
{
  "performance": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "retry_backoff": 2.0,
    "retry_on_errors": [
      "ConnectionError",
      "TimeoutError",
      "HTTPStatusError"
    ],
    "exponential_backoff": true,
    "jitter": true
  }
}
```

### Caching

```json
{
  "performance": {
    "cache_results": true,
    "cache_ttl_hours": 24,
    "cache_size_mb": 100,
    "cache_compression": true,
    "cache_cleanup_interval": 3600
  }
}
```

### Model Management

```json
{
  "performance": {
    "keep_models_loaded": true,
    "model_load_timeout": 60,
    "model_unload_delay": 300,
    "auto_unload_inactive": true,
    "memory_threshold_unload": 0.8
  }
}
```

## 📊 Output Configuration

### Formatting Options

```json
{
  "output": {
    "verbose_by_default": false,
    "use_color": true,
    "use_emoji": true,
    "compact_tables": false,
    "show_progress": true,
    "table_style": "rounded",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "number_format": "comma"
  }
}
```

### Verbosity Levels

```json
{
  "output": {
    "verbosity_levels": {
      "quiet": 0,
      "normal": 1,
      "verbose": 2,
      "debug": 3
    },
    "default_verbosity": 1,
    "show_timestamps": true,
    "show_model_info": true,
    "show_performance_stats": true
  }
}
```

## 📝 Logging Configuration

### Basic Logging

```json
{
  "logging": {
    "level": "INFO",
    "file": "~/.lmstrix/logs/lmstrix.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S"
  }
}
```

### Advanced Logging

```json
{
  "logging": {
    "level": "DEBUG",
    "handlers": [
      {
        "type": "file",
        "filename": "~/.lmstrix/logs/lmstrix.log",
        "max_size_mb": 10,
        "backup_count": 5,
        "level": "INFO"
      },
      {
        "type": "console",
        "level": "WARNING",
        "format": "%(levelname)s: %(message)s"
      }
    ],
    "loggers": {
      "lmstrix.api": "DEBUG",
      "lmstrix.core": "INFO",
      "httpx": "WARNING"
    }
  }
}
```

## 🔧 CLI Configuration

### Default Command Options

```json
{
  "cli": {
    "defaults": {
      "scan": {
        "verbose": false,
        "refresh": false
      },
      "test": {
        "threshold": 32768,
        "verbose": false,
        "timeout": 300
      },
      "infer": {
        "temperature": 0.7,
        "out_ctx": "auto",
        "verbose": false
      },
      "list": {
        "sort": "name",
        "show": "table"
      }
    }
  }
}
```

### Command Aliases

```json
{
  "cli": {
    "aliases": {
      "s": "scan",
      "l": "list",
      "t": "test",
      "i": "infer",
      "q": "infer --out_ctx 50",
      "v": "--verbose"
    }
  }
}
```

## 📍 Path Configuration

### Custom Paths

```json
{
  "paths": {
    "registry_file": "~/Documents/lmstrix/models.json",
    "cache_dir": "~/Documents/lmstrix/cache",
    "prompts_dir": "~/Documents/lmstrix/prompts",
    "logs_dir": "~/Documents/lmstrix/logs",
    "config_dir": "~/Documents/lmstrix/config"
  }
}
```

### Workspace Configuration

For project-specific settings, create `.lmstrix.json` in your project root:

```json
{
  "workspace": {
    "name": "my-project",
    "prompts_dir": "./prompts",
    "cache_dir": "./.lmstrix/cache",
    "preferred_models": [
      "llama-3.2-3b-instruct",
      "mistral-7b-instruct"
    ]
  },
  "safety": {
    "max_context_threshold": 16384
  }
}
```

## 🎯 Configuration Examples

### Development Setup

```json
{
  "lmstudio": {
    "base_url": "http://localhost:1234"
  },
  "safety": {
    "max_context_threshold": 16384
  },
  "logging": {
    "level": "DEBUG",
    "file": "./debug.log"
  },
  "output": {
    "verbose_by_default": true,
    "use_color": true
  }
}
```

### Production Setup

```json
{
  "lmstudio": {
    "base_url": "http://lmstudio-server:1234",
    "timeout": 600
  },
  "safety": {
    "max_context_threshold": 131072,
    "enable_safety_checks": true
  },
  "performance": {
    "max_retries": 5,
    "cache_results": true
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/lmstrix.log"
  }
}
```

### Research Setup

```json
{
  "safety": {
    "max_context_threshold": 262144,
    "max_test_iterations": 50
  },
  "performance": {
    "cache_results": false,
    "keep_models_loaded": false
  },
  "output": {
    "verbose_by_default": true,
    "show_performance_stats": true
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

## 🔍 Configuration Validation

### Validate Configuration

```bash
# Check current configuration
lmstrix config show

# Validate configuration file
lmstrix config validate ~/.lmstrix/config.json

# Show effective configuration (after merging all sources)
lmstrix config effective
```

### Configuration Schema

LMStrix validates configuration against a JSON schema. Invalid configurations will show helpful error messages:

```
Configuration Error: Invalid value for 'safety.max_context_threshold'
Expected: integer between 512 and 1048576
Received: "invalid"
Location: ~/.lmstrix/config.json:3:28
```

## 🚀 Next Steps

With configuration mastered:

- **[CLI Interface](cli-interface.md)** - Advanced command usage
- **[Context Testing](context-testing.md)** - Optimize testing with configuration
- **[Performance & Optimization](performance.md)** - Performance tuning
- **[Python API](python-api.md)** - Programmatic configuration

---

*Configuration is power - tune LMStrix to perfection! ⚙️*