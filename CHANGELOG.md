# Changelog

All notable changes to the LMStrix project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
