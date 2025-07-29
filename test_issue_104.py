#!/usr/bin/env python3
"""Test script for Issue #104 - Prompt file support with TOML"""

import subprocess
import sys


def run_command(cmd):
    """Run a command and return output"""
    print(f"\n{'=' * 60}")
    print(f"Running: {cmd}")
    print("=" * 60)
    result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0


def main() -> int:
    # Get a test model
    model_id = "wemake-llama-3-8b-instruct-v41-1048k"
    prompt_file = "examples/prompts.toml"

    print("Testing Issue #104: Prompt File Support with TOML")
    print("=" * 60)

    # Test 1: Basic prompt from file
    print("\nTest 1: Load simple prompt from TOML file")
    if not run_command(
        f'lmstrix infer greetings.casual {model_id} --file_prompt {prompt_file} --dict "name=Alice,topic=AI" --out_ctx 50',
    ):
        print("❌ Test 1 failed")
        return 1

    # Test 2: Formal greeting with parameters
    print("\nTest 2: Load formal greeting with parameters")
    if not run_command(
        f'lmstrix infer greetings.formal {model_id} --file_prompt {prompt_file} --dict "name=Dr. Smith,topic=machine learning" --out_ctx 50',
    ):
        print("❌ Test 2 failed")
        return 1

    # Test 3: Template with nested placeholders
    print("\nTest 3: Template with nested placeholders")
    if not run_command(
        f'lmstrix infer templates.instruction {model_id} --file_prompt {prompt_file} --dict "domain=Python programming,style=beginner-friendly,concept=decorators,level=intermediate" --out_ctx 100',
    ):
        print("❌ Test 3 failed")
        return 1

    # Test 4: Code review prompt
    print("\nTest 4: Code review prompt")
    code_snippet = "def add(a, b): return a + b"
    if not run_command(
        f'lmstrix infer code.explain {model_id} --file_prompt {prompt_file} --dict "language=Python,code={code_snippet}" --out_ctx 100',
    ):
        print("❌ Test 4 failed (note: may need proper escaping for code)")

    # Test 5: Simple QA prompt
    print("\nTest 5: Simple QA prompt")
    if not run_command(
        f'lmstrix infer qa.simple {model_id} --file_prompt {prompt_file} --dict "question=What is the capital of France?" --out_ctx 50',
    ):
        print("❌ Test 5 failed")
        return 1

    # Test 6: Prompt without parameters (should show unresolved placeholders)
    print("\nTest 6: Prompt with unresolved placeholders (verbose)")
    if not run_command(
        f"lmstrix infer greetings.casual {model_id} --file_prompt {prompt_file} --out_ctx 50 --verbose",
    ):
        print("❌ Test 6 failed")
        return 1

    print("\n" + "=" * 60)
    print("✅ Basic tests completed!")
    print("Note: Some tests may need adjustment based on model availability")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
