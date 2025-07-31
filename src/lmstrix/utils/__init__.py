"""Utility functions for LMStrix."""

from lmstrix.utils.logging import logger, setup_logging
from lmstrix.utils.paths import (
    get_context_test_log_path,
    get_context_tests_dir,
    get_contexts_dir,
    get_default_models_file,
    get_lmstrix_data_dir,
    get_lmstrix_log_path,
    get_lmstudio_path,
    get_prompts_dir,
)

__all__ = [
    "get_context_test_log_path",
    "get_context_tests_dir",
    "get_contexts_dir",
    "get_default_models_file",
    "get_lmstrix_data_dir",
    "get_lmstrix_log_path",
    "get_lmstudio_path",
    "get_prompts_dir",
    "setup_logging",
]
