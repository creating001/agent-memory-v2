#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${REPO_ROOT}/outputs/services"
PID_FILE="${SERVICE_DIR}/embedding_vllm.pid"
LOG_FILE="${SERVICE_DIR}/embedding_vllm_qwen3_0_6b.log"
SESSION_NAME="agent_memory_embedding_vllm"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-Qwen/Qwen3-Embedding-0.6B}"
EMBEDDING_HOST="${EMBEDDING_HOST:-127.0.0.1}"
EMBEDDING_PORT="${EMBEDDING_PORT:-8001}"
EMBEDDING_CUDA_VISIBLE_DEVICES="${EMBEDDING_CUDA_VISIBLE_DEVICES:-4}"
EMBEDDING_MAX_MODEL_LEN="${EMBEDDING_MAX_MODEL_LEN:-32768}"
VLLM_BIN="${VLLM_BIN:-/data1/yangyan/conda/envs/vllm/bin/vllm}"
VLLM_BIN_DIR="$(dirname "${VLLM_BIN}")"

mkdir -p "${SERVICE_DIR}"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "already_running ${SESSION_NAME}"
  exit 0
fi

rm -f "${PID_FILE}" "${LOG_FILE}"

tmux new-session -d -s "${SESSION_NAME}" "
  cd '${REPO_ROOT}' &&
  echo 'starting ${EMBEDDING_MODEL} on ${EMBEDDING_HOST}:${EMBEDDING_PORT}' | tee -a '${LOG_FILE}' &&
  CUDA_VISIBLE_DEVICES=${EMBEDDING_CUDA_VISIBLE_DEVICES} \
  PYTHONUNBUFFERED=1 \
  PATH=${VLLM_BIN_DIR}:\$PATH \
  exec ${VLLM_BIN} serve ${EMBEDDING_MODEL} \
    --host ${EMBEDDING_HOST} \
    --port ${EMBEDDING_PORT} \
    --runner pooling \
    --served-model-name ${EMBEDDING_MODEL} \
    --max-model-len ${EMBEDDING_MAX_MODEL_LEN} \
    2>&1 | tee -a '${LOG_FILE}'
"

tmux display-message -p -t "${SESSION_NAME}" "#{pane_pid}" > "${PID_FILE}"
echo "started ${SESSION_NAME} pane_pid=$(cat "${PID_FILE}")"
echo "log ${LOG_FILE}"
