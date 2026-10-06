#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BASE_PYTHON="${BASE_PYTHON:-python3}"
ENV_DIR="${EVIDENCE_ENV:-$HOME/venvs/agent-evidence}"
"$BASE_PYTHON" -c 'import sys; assert (3,10) <= sys.version_info[:2] <= (3,12), "Use Python 3.10-3.12, preferably 3.11"'
mkdir -p "$HOME/venvs" runs/setup
"$BASE_PYTHON" -m venv "$ENV_DIR"
PY="$ENV_DIR/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
"$PY" -m pip install -r scripts/requirements-agent-evidence.txt
"$PY" -m pip check
"$PY" -m pip freeze > runs/setup/evidence-requirements.lock.txt
"$PY" -c 'import torch; assert torch.cuda.is_available(), "CUDA unavailable; inspect nvidia-smi/driver"; print(torch.__version__, torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory / 2**30, "GiB")'
nvidia-smi > runs/setup/nvidia-smi.txt
"$PY" scripts/prepare_agent_server.py preflight --bundle bundle
echo "Evidence environment ready: $ENV_DIR"
