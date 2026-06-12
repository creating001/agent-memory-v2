#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="agent_memory_embedding_vllm"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  tmux kill-session -t "${SESSION_NAME}"
  echo "stopped ${SESSION_NAME}"
else
  echo "not_running ${SESSION_NAME}"
fi
