#!/usr/bin/env bash
# install.sh — Install lmstrix locally
# lmstrix is a toolkit for managing and testing LM Studio models with automatic context limit discovery
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing lmstrix..."
uv pip install -e . 2>/dev/null || pip install -e . 2>/dev/null || echo "Install failed"
echo "Done."
