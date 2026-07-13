#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/env.sh"
cd "$EASYEDIT_ROOT"
mkdir -p "$EASYEDIT_REPS_ROOT/outputs/vectors" "$EASYEDIT_REPS_ROOT/outputs/logs"

echo "[RePS Step 1] 训练 24 个 concept 的 steering 向量..."
MODEL="${REPS_MODEL_PATH:-/root/autodl-tmp/models/Qwen3-4B-Instruct-2507}"
VEC_DIR="${EASYEDIT_REPS_ROOT}/outputs/vectors/ccks_baseline_reps"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  python examples/steer_eval.py hydra.job.chdir=false \
  --config-path="$EASYEDIT_REPS_ROOT/config" \
  --config-name=steer_eval_reps_local \
  "model_name_or_path=${MODEL}" \
  "steer_vector_output_dirs=[${VEC_DIR}]" \
  "steer_vector_load_dir=[${VEC_DIR}]" \
  "$@"

echo "向量输出: $EASYEDIT_REPS_ROOT/outputs/vectors/ccks_baseline_reps"
