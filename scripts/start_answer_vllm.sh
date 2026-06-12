#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${REPO_ROOT}/outputs/services"
PID_FILE="${SERVICE_DIR}/answer_vllm.pid"
LOG_FILE="${SERVICE_DIR}/answer_vllm_qwen3_30b.log"
SESSION_NAME="agent_memory_answer_vllm"
ANSWER_MODEL="${ANSWER_MODEL:-Qwen/Qwen3-30B-A3B-Instruct-2507}"
ANSWER_HOST="${ANSWER_HOST:-127.0.0.1}"
ANSWER_PORT="${ANSWER_PORT:-8000}"
ANSWER_CUDA_VISIBLE_DEVICES="${ANSWER_CUDA_VISIBLE_DEVICES:-0,1,2,3}"
ANSWER_TENSOR_PARALLEL_SIZE="${ANSWER_TENSOR_PARALLEL_SIZE:-4}"
ANSWER_GPU_MEMORY_UTILIZATION="${ANSWER_GPU_MEMORY_UTILIZATION:-0.8}"
ANSWER_MAX_MODEL_LEN="${ANSWER_MAX_MODEL_LEN:-131072}"
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
  echo 'starting ${ANSWER_MODEL} on ${ANSWER_HOST}:${ANSWER_PORT}' | tee -a '${LOG_FILE}' &&
  CUDA_VISIBLE_DEVICES=${ANSWER_CUDA_VISIBLE_DEVICES} \
  PYTHONUNBUFFERED=1 \
  PATH=${VLLM_BIN_DIR}:\$PATH \
  exec ${VLLM_BIN} serve ${ANSWER_MODEL} \
    --host ${ANSWER_HOST} \
    --port ${ANSWER_PORT} \
    --tensor-parallel-size ${ANSWER_TENSOR_PARALLEL_SIZE} \
    --gpu-memory-utilization ${ANSWER_GPU_MEMORY_UTILIZATION} \
    --max-model-len ${ANSWER_MAX_MODEL_LEN} \
    --reasoning-parser qwen3 \
    2>&1 | tee -a '${LOG_FILE}'
"

tmux display-message -p -t "${SESSION_NAME}" "#{pane_pid}" > "${PID_FILE}"
echo "started ${SESSION_NAME} pane_pid=$(cat "${PID_FILE}")"
echo "log ${LOG_FILE}"
