#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/env.sh"
cd "$EASYEDIT_ROOT"
mkdir -p "$EASYEDIT_REPS_ROOT/outputs/generation"

echo "[RePS Step 2] 在 valid 上生成..."
MODEL="${REPS_MODEL_PATH:-/root/autodl-tmp/models/Qwen3-4B-Instruct-2507}"
VEC_DIR="${EASYEDIT_REPS_ROOT}/outputs/vectors/ccks_baseline_reps"
GEN_DIR="${EASYEDIT_REPS_ROOT}/outputs/generation/ccks_baseline_reps/reps"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  python examples/steer_eval.py hydra.job.chdir=false \
  --config-path="$EASYEDIT_REPS_ROOT/config" \
  --config-name=steer_eval_reps_generate \
  "model_name_or_path=${MODEL}" \
  "steer_vector_load_dir=[${VEC_DIR}]" \
  "generation_output_dir=${GEN_DIR}" \
  "$@"

echo "生成结果: $EASYEDIT_REPS_ROOT/outputs/generation/ccks_baseline_reps/reps/all_generation_results_valid.json"
