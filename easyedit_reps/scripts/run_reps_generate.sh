#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/env.sh"
cd "$EASYEDIT_ROOT"
mkdir -p "$EASYEDIT_REPS_ROOT/outputs/generation"

echo "[RePS Step 2] 在 valid 上生成..."
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  python examples/steer_eval.py hydra.job.chdir=false \
  --config-path="$EASYEDIT_REPS_ROOT/config" \
  --config-name=steer_eval_reps_generate \
  "$@"

echo "生成结果: $EASYEDIT_REPS_ROOT/outputs/generation/ccks_baseline_reps/reps/all_generation_results_valid.json"
