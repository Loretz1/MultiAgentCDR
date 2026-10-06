#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${EVIDENCE_ENV:-$HOME/venvs/agent-evidence}/bin/python"
RUN="${RUN_DIR:-runs/pilot_v1}"
CONFIG="${AGENT_CONFIG:-scripts/configs/cloth_sports_agent.json}"
GROUP="${AGENT_GROUP:-prompt_dev}"
mkdir -p "$RUN/logs"
export PYTHONUNBUFFERED=1
export HF_HOME="${HF_HOME:-$HOME/models/hf-cache}"
"$PY" scripts/prepare_agent_server.py preflight --bundle bundle | tee "$RUN/logs/preflight.log"
# Processes run sequentially so the GPU is released between stages.
"$PY" scripts/encode_agent_text.py --bundle bundle --output "$RUN/encoder" --config "$CONFIG" 2>&1 | tee "$RUN/logs/encode.log"
"$PY" scripts/train_agent_g.py --bundle bundle --output "$RUN/g" --config "$CONFIG" 2>&1 | tee "$RUN/logs/g.log"
"$PY" scripts/export_agent_evidence.py --bundle bundle --encoder "$RUN/encoder" --g "$RUN/g" --output "$RUN/inputs_$GROUP" --config "$CONFIG" --group "$GROUP" 2>&1 | tee "$RUN/logs/export.log"
echo "Completed: $RUN/inputs_$GROUP/agent_inputs.jsonl"
