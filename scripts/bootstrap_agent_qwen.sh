#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_DIR="${QWEN_ENV:-$HOME/venvs/agent-vllm}"
python3 -m venv "$ENV_DIR"
PY="$ENV_DIR/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install vllm==0.29.0 httpx==0.28.1
"$PY" -m pip check
mkdir -p runs/setup "$HOME/models"
"$PY" -m pip freeze > runs/setup/qwen-requirements.lock.txt
"$PY" - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path
snapshot_download('Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',
    revision='5a5a776300a41aaa681dd7ff0106608ef2bc90db',
    local_dir=Path.home()/'models/Qwen3-30B-A3B-Instruct-2507-FP8', max_workers=4)
PY
echo 'Qwen environment and frozen model ready'
