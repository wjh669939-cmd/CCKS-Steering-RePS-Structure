#!/usr/bin/env bash
# 从 baseline/reps_raw_v1 重生成 0.3817 提交（layer 18 统一 + 冻结 multipliers）
# 用法: bash scripts/regen_from_baseline_0.3817.sh [max_new_tokens] [tag]
# 示例: bash scripts/regen_from_baseline_0.3817.sh 512
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_DIR="$PROJECT_ROOT/baseline/reps_raw_v1"
cd "$PROJECT_ROOT/easyedit_reps"
# shellcheck source=/dev/null
source env.sh

MAX_TOKENS="${1:-512}"
TAG="${2:-baseline_0.3817_${MAX_TOKENS}}"
OUT="$PROJECT_ROOT/绝地邮兵_result_regen_${TAG}.json"
VECTOR_ROOT="${EASYEDIT_REPS_ROOT}/outputs/vectors/ccks_baseline_reps"

if [[ ! -f "$BASELINE_DIR/multipliers.json" ]]; then
  echo "ERROR: missing $BASELINE_DIR/multipliers.json" >&2
  exit 1
fi

if [[ ! -d "$VECTOR_ROOT" ]]; then
  echo "ERROR: vector dir not found: $VECTOR_ROOT" >&2
  echo "Run: bash scripts/run_baseline_0_3817.sh step1" >&2
  exit 1
fi

.venv/bin/python scripts/regen_tuned_all.py \
  --max-new-tokens "$MAX_TOKENS" \
  --tag "$TAG" \
  --layer 18 \
  --vector-root "$VECTOR_ROOT" \
  --multipliers "$BASELINE_DIR/multipliers.json" \
  --out-export "$OUT"

echo "Wrote $OUT"
echo "Validate: python3 docs/reproduction/scripts/validate_submission.py $OUT"
