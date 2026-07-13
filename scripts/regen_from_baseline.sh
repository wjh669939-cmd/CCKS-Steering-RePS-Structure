#!/usr/bin/env bash
# 从 baseline/layers.json + baseline/multipliers.json 重生成提交（0.6714+ per-concept，非 0.3817）
# 0.3817 请用: bash scripts/regen_from_baseline_0.3817.sh 512
# 用法: bash scripts/regen_from_baseline.sh [max_new_tokens] [tag]
# 示例: bash scripts/regen_from_baseline.sh 512 phase_c
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/easyedit_reps"
source env.sh

MAX_TOKENS="${1:-512}"
TAG="${2:-baseline_${MAX_TOKENS}}"
OUT="$PROJECT_ROOT/绝地邮兵_result_regen_${TAG}.json"

.venv/bin/python scripts/regen_mixed_layers.py \
  --layers-json "$PROJECT_ROOT/baseline/layers.json" \
  --per-layer-base "$EASYEDIT_REPS_ROOT/outputs/vectors/per_layer" \
  --multipliers "$PROJECT_ROOT/baseline/multipliers.json" \
  --max-new-tokens "$MAX_TOKENS" \
  --tag "$TAG" \
  --out-export "$OUT"

echo "Wrote $OUT"
