#!/usr/bin/env bash
# CCKS2026 RePS baseline 0.3817 完整流程编排
# 用法: bash scripts/run_baseline_0_3817.sh [step1|step3|step4|step5|all]
set -euo pipefail
STEP="${1:-all}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EASYEDIT_REPS="$PROJECT_ROOT/easyedit_reps"
BASELINE_DIR="$PROJECT_ROOT/baseline/reps_raw_v1"
LOG_DIR="$PROJECT_ROOT/runs/baseline_0_3817"
mkdir -p "$LOG_DIR"

: "${REPS_MODEL_PATH:=/root/autodl-tmp/models/Qwen3-4B-Instruct-2507}"
export REPS_MODEL_PATH

if [[ ! -f "$REPS_MODEL_PATH/config.json" ]]; then
  echo "ERROR: model not found at REPS_MODEL_PATH=$REPS_MODEL_PATH" >&2
  exit 1
fi

cd "$EASYEDIT_REPS"
# shellcheck source=/dev/null
source env.sh

run_step1() {
  echo "========== Step 1: 训练 RePS 向量 (24 concepts, layer 18) =========="
  bash scripts/run_reps_vectors.sh \
    "model_name_or_path=${REPS_MODEL_PATH}" \
    2>&1 | tee "$LOG_DIR/step1_vectors.log"
}

run_step3() {
  echo "========== Step 3: L3 multiplier 扫参 =========="
  bash scripts/run_l3_sweep.sh 2>&1 | tee "$LOG_DIR/step3_l3_sweep.log"
}

run_step4() {
  echo "========== Step 4: L1/L2 multiplier 扫参 =========="
  bash scripts/run_l12_sweep.sh 2>&1 | tee "$LOG_DIR/step4_l12_sweep.log"
}

run_step5() {
  echo "========== Step 5: 用冻结 multipliers 重生成 (512 token) =========="
  cd "$PROJECT_ROOT"
  bash scripts/regen_from_baseline_0.3817.sh 512 2>&1 | tee "$LOG_DIR/step5_regen.log"
  python3 docs/reproduction/scripts/validate_submission.py \
    "$PROJECT_ROOT/绝地邮兵_result_regen_baseline_0.3817_512.json"
}

case "$STEP" in
  step1) run_step1 ;;
  step3) run_step3 ;;
  step4) run_step4 ;;
  step5) run_step5 ;;
  all)
    run_step1
    run_step3
    run_step4
    run_step5
    ;;
  *)
    echo "用法: bash $0 [step1|step3|step4|step5|all]"
    echo "  step1 — 训练向量 (~2-3h GPU)"
    echo "  step3 — L3 multiplier 扫参 (~1h)"
    echo "  step4 — L1/L2 multiplier 扫参 (~1.5h)"
    echo "  step5 — 用 baseline/reps_raw_v1/multipliers.json 重生成 (~15min)"
    exit 1
    ;;
esac

echo "Done. Logs: $LOG_DIR"
