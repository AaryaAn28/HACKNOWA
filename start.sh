#!/usr/bin/env bash
set -e

# Detect the appropriate Python runtime in Render's environment
if [ -f "./.venv/bin/python" ]; then
    PYTHON_CMD="./.venv/bin/python"
elif [ -f "/opt/render/project/src/.venv/bin/python" ]; then
    PYTHON_CMD="/opt/render/project/src/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "==> Starting Reality Sculptor using: $PYTHON_CMD"
exec $PYTHON_CMD run.py
