#!/usr/bin/env bash
# Zero-training: sweep L2_2 multiplier only (existing retrain vector @ L18).
# Usage: bash scripts/run_l2_2_mult_sweep.sh
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/easyedit_reps"
source env.sh

CONCEPT="L2_2"
LAYER=18
VROOT="$EASYEDIT_REPS_ROOT/outputs/vectors/per_layer"
RUN="$PROJECT_ROOT/runs/l2_2_mult_sweep"
SWEEP="$RUN/sweep"
BASE="$PROJECT_ROOT/baseline/submission.json"
mkdir -p "$SWEEP"

MULTS="3.0,3.5,4.0"
echo "=== L2_2 mult sweep (no retrain) L${LAYER} m=${MULTS} ==="

.venv/bin/python scripts/sweep_l12_weak.py \
  --concept "$CONCEPT" \
  --multipliers "$MULTS" \
  --layers "$LAYER" \
  --per-layer-base "$VROOT" \
  --out-dir "$SWEEP" \
  --tag mult_sweep

for p in "$SWEEP/${CONCEPT}_L${LAYER}_m"*.json; do
  [[ -f "$p" ]] || continue
  [[ "$p" == *"_best"* || "$p" == *"_summary"* ]] && continue
  m=$(basename "$p" .json | sed "s/.*_m//")
  mtag=${m//./p}
  python "$PROJECT_ROOT/scripts/merge_submission.py" \
    --base "$BASE" \
    --patch "$p" \
    --concepts "$CONCEPT" \
    --out "$PROJECT_ROOT/绝地邮兵_result_l2_2_m${mtag}_only.json"
  echo "  绝地邮兵_result_l2_2_m${mtag}_only.json"
done

echo "Done. Current official best is m=3.5 (0.6714). Pick another mult for A/B if needed."
