#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${REPO_ROOT}/outputs/services"
PID_FILE="${SERVICE_DIR}/rerank_vllm.pid"
LOG_FILE="${SERVICE_DIR}/rerank_vllm_qwen3_0_6b.log"
SESSION_NAME="agent_memory_rerank_vllm"
RERANK_MODEL="${RERANK_MODEL:-Qwen/Qwen3-Reranker-0.6B}"
RERANK_HOST="${RERANK_HOST:-127.0.0.1}"
RERANK_PORT="${RERANK_PORT:-8002}"
RERANK_CUDA_VISIBLE_DEVICES="${RERANK_CUDA_VISIBLE_DEVICES:-5}"
RERANK_GPU_MEMORY_UTILIZATION="${RERANK_GPU_MEMORY_UTILIZATION:-0.4}"
RERANK_MAX_MODEL_LEN="${RERANK_MAX_MODEL_LEN:-8192}"
RERANK_TEMPLATE="${RERANK_TEMPLATE:-${REPO_ROOT}/scripts/templates/qwen3_reranker.jinja}"
RERANK_HF_OVERRIDES="${RERANK_HF_OVERRIDES:-{\"architectures\":[\"Qwen3ForSequenceClassification\"],\"classifier_from_token\":[\"no\",\"yes\"],\"is_original_qwen3_reranker\":true}}"
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
  echo 'starting ${RERANK_MODEL} on ${RERANK_HOST}:${RERANK_PORT}' | tee -a '${LOG_FILE}' &&
  VLLM_USE_V1=0 \
  CUDA_VISIBLE_DEVICES=${RERANK_CUDA_VISIBLE_DEVICES} \
  PYTHONUNBUFFERED=1 \
  PATH=${VLLM_BIN_DIR}:\$PATH \
  exec ${VLLM_BIN} serve ${RERANK_MODEL} \
    --host ${RERANK_HOST} \
    --port ${RERANK_PORT} \
    --served-model-name ${RERANK_MODEL} \
    --runner pooling \
    --gpu-memory-utilization ${RERANK_GPU_MEMORY_UTILIZATION} \
    --max-model-len ${RERANK_MAX_MODEL_LEN} \
    --chat-template '${RERANK_TEMPLATE}' \
    --hf-overrides '${RERANK_HF_OVERRIDES}' \
    2>&1 | tee -a '${LOG_FILE}'
"

tmux display-message -p -t "${SESSION_NAME}" "#{pane_pid}" > "${PID_FILE}"
echo "started ${SESSION_NAME} pane_pid=$(cat "${PID_FILE}")"
echo "log ${LOG_FILE}"
