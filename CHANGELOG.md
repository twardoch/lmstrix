# Changelog

All notable changes to the LMStrix project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Issue #307**: Streaming Inference Support
  - Added `stream_completion()` method to LMStudioClient using lmstudio SDK's `complete_stream()`
  - Implemented token-by-token streaming with callbacks and progress monitoring
  - Added `stream_infer()` methods to InferenceEngine and InferenceManager
  - Added CLI `--stream` flag for real-time token display during inference
  - Added `--stream-timeout` parameter (default 120s) for hang detection
  - Streaming statistics: tokens/second, time to first token
- **Issue #306**: Batch Processing Tool (`_keep_this/adam/adamall.py`)
  - Processes multiple prompts across all models automatically
  - Smart model management - reuses loaded models when possible
  - Skips existing outputs for resumable batch processing
  - Safe filename generation using pathvalidate
  - Error capture to output files on failure
  - Progress tracking with percentage completion
  - Processes prompts: `think,aps`, `think,humanize`, `think,tldr`, `think,tts_optimize`, `translate`, `tldr`
- Created `src/lmstrix/api/main.py` with `LMStrixService` class containing all business logic
- Implemented separation of concerns with thin CLI wrapper in `__main__.py`

### Changed
- Default temperature changed from 0.7 to 0.8 to match LM Studio GUI defaults
- Default `out_ctx` now falls back to the model's `ctx_out − 1` when callers leave it as `-1`. This avoids LM Studio SDK hangs triggered by unlimited generations.
- Refactored CLI architecture - moved all business logic from `__main__.py` to `api/main.py`
- Updated `__main__.py` to be a thin wrapper that delegates to `LMStrixService`
- Modified test imports to use new module structure

### Fixed
- **Issue #303**: Fixed loguru output interference with model responses
  - Removed loguru formatting of config dictionaries and raw model responses
  - Changed problematic log messages in `api/client.py` lines 265 and 267 to simple status messages
  - Prevented KeyError and ValueError exceptions when loguru tried to parse model output
  - Ensures clean separation of diagnostic output (stderr) from model output (stdout)
- Fixed import error after removing `src/lmstrix/cli` directory
- Updated `pyproject.toml` entry point from `lmstrix.cli.main:main` to `lmstrix.__main__:main`

### Removed
- Removed `src/lmstrix/cli` directory (merged functionality into `__main__.py`)

## [1.0.59] - 2025-07-31

### Major Improvements & Bug Fixes

#### Issues 201-204 (Completed)
- **Issue 201**: Enhanced model persistence - models now stay loaded between inference calls when no explicit context is specified
- **Issue 202**: Beautiful enhanced logging with emojis, model info, config details, and prompt statistics  
- **Issue 203**: Fixed model lookup to find by both path and ID without changing JSON structure
- **Issue 204**: Added comprehensive verbose stats logging including time to first token, predicted tokens, tokens/second, and total inference time

#### Model Registry Improvements
- Fixed smart model lookup that works with both model paths and IDs
- Preserved original JSON structure keyed by path
- No data duplication - registry size maintained
- Backward compatible with existing path-based lookups

#### Enhanced Logging & Statistics
- Beautiful formatted logging with visual separators and emojis
- Complete inference statistics display including:
  - ⚡ Time to first token
  - ⏱️ Total inference time  
  - 🔢 Predicted tokens
  - 📝 Prompt tokens
  - 🎯 Total tokens
  - 🚀 Tokens/second
  - 🛑 Stop reason
- Eliminated duplicate stats display at end of output

### Added

- **Context Parameter Percentage Support**
  - `--out_ctx` parameter now supports percentage notation (e.g., "80%")
  - Created `utils/context_parser.py` for parsing context parameters
  - Percentage calculated from model's tested or declared maximum context

- **Improved CLI Output**
  - Non-verbose mode for `infer` command now shows only model response
  - Removed extra formatting and status information in quiet mode

- **Prompt File Support with TOML (Issue #104)**
  - Added `--file_prompt` parameter to load prompts from TOML files
  - Added `--dict` parameter for passing key=value pairs for placeholder resolution
  - When using `--file_prompt`, the prompt parameter refers to the prompt name in the TOML file
  - Supports nested placeholders and internal template references
  - Reports unresolved placeholders in verbose mode
  - Includes comprehensive example prompt file with various use cases

- **Enhanced Infer Context Control (Issue #103)**
  - Added `--in_ctx` parameter to control model loading context size
  - Added `--out_ctx` parameter to replace deprecated `--max_tokens`
  - Supports `--in_ctx 0` to load model without context specification
  - When `--in_ctx` is not specified, uses optimal context (tested or declared)
  - Explicit `--in_ctx` always unloads existing models and reloads with specified context
  - Smart unloading: only unloads models that were explicitly loaded with `--in_ctx`

- **Smart Model Loading**
  - Added model state detection to check if models are already loaded
  - Reuses existing loaded models when no explicit context specified
  - Added `--force-reload` flag to force model reload even if already loaded
  - Shows clear status messages about model reuse vs reload

- **Model State Persistence (Issue #201)**
  - Models now stay loaded between `infer` calls when `--in_ctx` is not specified
  - Added StateManager to track last-used model across sessions
  - Model ID parameter (`-m`) is now optional - uses last-used model when omitted
  - Significantly improves performance by avoiding repeated model loading/unloading
  - Created `examples/cli/model_state_demo.sh` demonstrating the feature

- **Context Validation**
  - Validates requested context against model's declared and tested limits
  - Warns when context exceeds safe limits
  - Suggests optimal context values

### Changed

- **Inference Command**
  - Deprecated `--max_tokens` in favor of `--out_ctx` (backward compatible with warnings)
  - Updated help text and documentation for new parameters
  - Improved model loading logic for better memory management
  - Enhanced status messages during inference operations

## [1.0.53] - 2025-07-29

### Fixed

- **Git Configuration**
  - Fixed git pull error by setting upstream branch tracking with `git branch --set-upstream-to=origin/main main`
  - Resolved "exit code(1)" error when running `git pull -v -- origin` without branch specification

### Changed

- **Version Maintenance**
  - Updated to version 1.0.53 with proper git configuration fixes

## [1.0.28 - 1.0.52] - 2025-07-25 to 2025-07-29

### Added

- **Enhanced CLI Features**
  - Added `--sort` option to `lmstrix test --all` command with same sort options as list (id, ctx, dtx, size, etc.)
  - Added `--ctx` option to `lmstrix test --all` for testing all untested models at a specific context size
  - Added `--show` option to `lmstrix list` with three output formats:
    - `id`: Plain newline-delimited list of model IDs
    - `path`: Newline-delimited list of relative paths (same as id currently)
    - `json`: Full JSON array from the registry
  - All `--show` formats respect the `--sort` option for flexible output

- **CLI Improvements**
  - Modified `--ctx` to work with `--all` flag for batch testing at specific context sizes
  - `test --all --ctx` filters models based on context limits and safety checks
  - Added proper status updates and persistence when using `--ctx` for single model tests
  - Fixed model field updates (tested_max_context, last_known_good_context) during --ctx testing

### Changed

- **Removed all asyncio dependencies (Issue #204)**
  - Converted entire codebase from async to synchronous
  - Now uses the native synchronous `lmstudio` package API directly
  - Simplified architecture by removing async/await complexity
  - Implemented signal-based timeout for Unix systems
  - All methods now return results directly without await

### Added

- **Context Size Safety Validation**
  - Added validation to prevent testing at or above `last_known_bad_context`
  - CLI `--ctx` parameter now checks against `last_known_bad_context` and limits to 90% of last bad
  - Automatic testing algorithms now respect `last_known_bad_context` during iterations
  - Added warning messages when context size approaches 80% or 90% of last known bad context
  - Prevents system crashes by avoiding previously failed context sizes

- **Enhanced Context Testing Strategy (Issue #201)**
  - Added `--threshold` parameter to test command (default: 102,400 tokens)
  - Prevents system crashes by limiting initial test size
  - New incremental testing algorithm: test at 1024, then threshold, then increment by 10,240
  - Optimized batch testing for `--all` flag with pass-based approach
  - Models sorted by declared context size to minimize loading/unloading
  - Rich table output showing test results with efficiency percentages

- **Smart Context Testing with Progress Saving**
  - Context tests now start with small context (32) to verify model loads
  - Added fields to track last known good/bad context sizes
  - Tests can resume from previous state if interrupted
  - Progress is saved to JSON after each test iteration
  - Changed test prompt from "2+2=" to "Say hello" for better reliability

### Fixed

- **Terminology Improvements**
  - Changed "Loaded X models" to "Read X models" to avoid confusion with LM Studio's model loading
  - Replaced generic "Check logs for details" with specific error messages

- **Context Testing Stability**
  - Added delays between model load/unload operations to prevent rapid cycling
  - Fixed connection reset issues caused by too-rapid operations
  - Enhanced binary search logging to show progress clearly

### Changed

- **Model Data Structure**
  - Added `last_known_good_context` field for resumable testing
  - Added `last_known_bad_context` field for resumable testing
  - Updated registry serialization to include new fields

## [1.0.28] - 2025-07-25

### Added

- **GitHub Pages Documentation Site**
  - Created comprehensive documentation site structure under `docs/`
  - Added Jekyll configuration with custom theme and navigation
  - Created documentation pages: installation, usage, API reference, how-it-works
  - Set up automatic changelog integration with documentation
  - Added responsive design and syntax highlighting

- **Example Improvements**
  - Added example output logging to `examples.log.txt` and `examples.err.txt`
  - Enhanced error handling in example scripts
  - Added more detailed comments in Python examples

### Fixed

- **Client Compatibility**
  - Fixed attribute access issues in `api/client.py` for embedding models
  - Added proper handling for different model types (LLMs vs Embeddings)
  - Improved error messages for unsupported model types

- **Context Testing Robustness**
  - Enhanced context size detection with better error handling
  - Improved inference validation logic
  - Added fallback mechanisms for edge cases

### Changed

- **CLI Enhancements**
  - Improved output formatting for model listings
  - Better progress indicators during testing
  - More informative error messages

- **Documentation Updates**
  - Updated README with clearer examples
  - Enhanced API documentation with more details
  - Added troubleshooting section

## [1.0.23] - 2025-07-25

### Added

- Implemented comprehensive `test_binary_search_logic` test function with edge cases:
  - Model that works at all sizes
  - Model that never works  
  - Model that loads but never passes inference
  - Model that works up to a specific context size
  - Model that never loads

### Fixed

- Fixed syntax errors in Python example files:
  - `examples/python/batch_processing.py` - Fixed unterminated string literals
  - `examples/python/custom_inference.py` - Fixed similar syntax issues
- Improved code quality by fixing linting issues:
  - Updated file operations to use `Path.open()` instead of `open()` (PTH123)
  - Added proper exception chaining with `from e` (B904)
  - Fixed shadowing of Python builtin `all` by renaming to `all_models` (A002)
- Updated `api/client.py` to handle different attribute names for LLMs vs Embeddings

### Changed

- All mypy type checking now passes without errors
- Package builds successfully as v1.0.23

## [1.0.21] - 2025-07-25

### Fixed

- Code formatting improvements in test files for better readability
- Updated `cleanup.sh` script
- Reduced size of `llms.txt` file significantly for better performance

## [1.0.0] - 2025-07-25

### Changed

- **Major Refactoring: `litellm` to Native `lmstudio` Integration**
  - **Dependency Pivot**: Completely removed the `litellm` dependency and replaced it with the native `lmstudio` package for all model interactions. This provides a more robust, reliable, and direct integration.
  - **API Client (`api/client.py`)**: Rewritten to be a direct, thin wrapper around the `lmstudio` package’s core functions (`list_downloaded_models`, `llm`, `complete`, `unload`).
  - **Context Tester (`core/context_tester.py`)**: The engine for finding the true context limit of a model has been completely rewritten to use the native `lmstudio` client. It now performs a binary search, efficiently loading, testing, and unloading models to determine the maximum operational context size.
  - **Inference Engine (`core/inference.py`)**: Updated to use the native client, ensuring models are loaded with their tested, validated context length before running inference.
  - **Model Discovery (`loaders/model_loader.py`)**: The model scanner now uses `lmstudio` to discover all downloaded models, ensuring the local registry is always perfectly in sync with the LM Studio application.

### Added

- **System Path and Data Storage**
  - Implemented robust detection of the LM Studio data directory by reading the `$HOME/.lmstudio-home-pointer` file.
  - All application data, including the model registry, is now stored in a clean, standardized `lmstrix.json` file directly within the located LM Studio data directory.
  - All test logs are stored in a `context_tests` subdirectory within a new `lmstrix` folder in the LM Studio data directory.

- **CLI and API Enhancements**
  - **CLI (`cli/main.py`)**: All commands (`scan`, `list`, `test`, `infer`) have been updated to use the new, refactored core logic, providing a seamless user experience.
  - **Public API (`__init__.py`)**: The high-level `LMStrix` class has been simplified to provide a clean, modern, and programmatic interface to the library's `lmstudio`-native functionality.

### Fixed

- Resolved all previous import and dependency issues related to `litellm`.
- Standardized the data storage location to prevent fragmentation and improve reliability.

## [0.1.0] - 2025-07-24

### Added

- Initial project structure with `src/` layout.
- First implementation of core components using `litellm`.
- Basic CLI and API interfaces.
