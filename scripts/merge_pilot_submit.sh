#!/usr/bin/env bash
# Merge one pilot-retrain concept onto 0.6714 baseline for official A/B.
# Usage:
#   bash scripts/merge_pilot_submit.sh L1_4
#   bash scripts/merge_pilot_submit.sh L1_4 3.5
#   bash scripts/merge_pilot_submit.sh L2_2 3.0
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="$ROOT/baseline/submission.json"
CONCEPT="${1:?usage: merge_pilot_submit.sh CONCEPT [mult]}"
MULT_OVERRIDE="${2:-}"

# concept_lock.json: only STUBBORN queue may be patched
if ! python3 "$ROOT/scripts/check_concept_lock.py" "$CONCEPT"; then
  echo "See baseline/concept_lock.json and docs/CONCEPT_LOCK.md" >&2
  exit 1
fi

if [[ "$CONCEPT" =~ ^L1_ ]]; then
  VTAG="l1"
  RUN="$ROOT/runs/pilot_retrain_${CONCEPT,,}"
elif [[ "$CONCEPT" =~ ^L2_ ]]; then
  VTAG="l2"
  RUN="$ROOT/runs/pilot_retrain_${CONCEPT,,}"
else
  echo "Error: only L1_* or L2_* supported (got $CONCEPT)" >&2
  exit 1
fi

PICK="$RUN/layer_pick.json"
[[ -f "$PICK" ]] || { echo "Missing $PICK — run pilot retrain first." >&2; exit 1; }

read -r PICK_L DEFAULT_M <<EOF
$(python3 -c "import json; p=json.load(open('$PICK')); print(p['best_layer'], p.get('multiplier',''))")
EOF

if [[ -z "$MULT_OVERRIDE" ]]; then
  MULT_OVERRIDE=$(python3 -c "import json; print(json.load(open('$ROOT/baseline/multipliers.json'))['$CONCEPT'])")
fi

SWEEP="$RUN/sweep"
PATCH="$SWEEP/${CONCEPT}_L${PICK_L}_m${MULT_OVERRIDE}.json"
if [[ ! -f "$PATCH" ]]; then
  PATCH=$(ls "$SWEEP/${CONCEPT}_L${PICK_L}_m"*.json 2>/dev/null | grep -v _best | grep -v _summary | head -1)
fi
[[ -f "$PATCH" ]] || { echo "No sweep patch for $CONCEPT L${PICK_L} m=${MULT_OVERRIDE}" >&2; exit 1; }

OUT="$ROOT/绝地邮兵_result_pilot_retrain_${CONCEPT}_m${MULT_OVERRIDE//./p}_submit.json"
python "$ROOT/scripts/merge_submission.py" \
  --base "$BASE" \
  --patch "$PATCH" \
  --concepts "$CONCEPT" \
  --out "$OUT"

echo "Wrote $OUT"
echo "  concept=$CONCEPT layer=$PICK_L mult=$MULT_OVERRIDE"
echo "  base=0.6714 baseline, changed 5/120 answers"
echo "Submit this file to 天池 (one concept A/B only)."
