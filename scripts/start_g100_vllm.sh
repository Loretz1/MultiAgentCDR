#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
MODEL_PATH="${MODEL_PATH:-$HOME/models/Qwen3-30B-A3B-Instruct-2507-FP8}"
VLLM_BIN="${VLLM_BIN:-$HOME/venvs/agent-vllm/bin/vllm}"

# Featurize's base image has no system nvcc. vLLM's FlashInfer sampler tries
# to compile a kernel at startup, so use the built-in sampler for this probe.
export VLLM_USE_FLASHINFER_SAMPLER=0

exec "$VLLM_BIN" serve "$MODEL_PATH" \
  --served-model-name "$MODEL_ID" \
  --host 127.0.0.1 \
  --port 8000 \
  --max-model-len 8192 \
  --max-num-seqs 4 \
  --gpu-memory-utilization 0.85 \
  --logprobs-mode raw_logprobs
