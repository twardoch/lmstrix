# Changelog

All notable changes to the LMStrix project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
