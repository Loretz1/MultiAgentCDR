#!/usr/bin/env bash
# Run inside the unpacked experiment directory on the rented GPU instance.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs outputs
if [[ -f logs/experiment.pid ]] && kill -0 "$(cat logs/experiment.pid)" 2>/dev/null; then
  echo "Experiment is already running with PID $(cat logs/experiment.pid)"
  exit 0
fi
nohup "$HOME/venvs/agent-vllm/bin/python" -u scripts/run_g100_v6_background.py > logs/experiment.log 2>&1 < /dev/null &
echo "$!" > logs/experiment.pid
echo "Started experiment PID $(cat logs/experiment.pid)"
