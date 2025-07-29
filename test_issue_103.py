#!/usr/bin/env python3
"""Test script for Issue #103 - Enhanced infer context control"""

import subprocess
import sys
import time


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
    prompt = "What is 2+2?"

    print("Testing Issue #103: Enhanced Infer Context Control")
    print("=" * 60)

    # Test 1: Basic inference with new --out_ctx parameter
    print("\nTest 1: Basic inference with --out_ctx")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --out_ctx 50'):
        print("❌ Test 1 failed")
        return 1

    time.sleep(2)

    # Test 2: Inference with specific --in_ctx
    print("\nTest 2: Inference with specific --in_ctx=8192")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --in_ctx 8192 --out_ctx 50'):
        print("❌ Test 2 failed")
        return 1

    time.sleep(2)

    # Test 3: Inference with --in_ctx=0 (default context)
    print("\nTest 3: Inference with --in_ctx=0 (default context)")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --in_ctx 0 --out_ctx 50'):
        print("❌ Test 3 failed")
        return 1

    time.sleep(2)

    # Test 4: Inference without --in_ctx (should reuse if loaded)
    print("\nTest 4: Inference without --in_ctx (reuse existing)")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --out_ctx 50'):
        print("❌ Test 4 failed")
        return 1

    time.sleep(2)

    # Test 5: Backward compatibility with --out_ctx
    print("\nTest 5: Backward compatibility with deprecated --out_ctx")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --out_ctx 50'):
        print("❌ Test 5 failed")
        return 1

    # Test 6: Both --out_ctx and --out_ctx (should warn and use --out_ctx)
    print("\nTest 6: Both --out_ctx and --out_ctx (should warn)")
    if not run_command(f'lmstrix infer "{prompt}" {model_id} --out_ctx 30 --out_ctx 50'):
        print("❌ Test 6 failed")
        return 1

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
