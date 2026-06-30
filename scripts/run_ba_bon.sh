#!/usr/bin/env bash
# BA-BoN for one STUBBORN concept → merge onto 0.6714 baseline
# Usage: bash scripts/run_ba_bon.sh L3_3
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONCEPT="${1:?usage: run_ba_bon.sh L3_X}"

python3 "$PROJECT_ROOT/scripts/check_concept_lock.py" "$CONCEPT"

cd "$PROJECT_ROOT/easyedit_reps"
source env.sh

RUN="$PROJECT_ROOT/runs/ba_bon_${CONCEPT,,}"
LOG="$RUN/run.log"
mkdir -p "$RUN"

echo "=== BA-BoN $CONCEPT $(date -Iseconds) ===" | tee "$LOG"

.venv/bin/python scripts/regen_ba_bon.py \
  --concept "$CONCEPT" \
  --out-dir "$RUN" \
  --out-export "$PROJECT_ROOT/绝地邮兵_result_ba_bon_${CONCEPT}_submit.json" \
  2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "Review: $RUN/${CONCEPT}_summary.json" | tee -a "$LOG"
echo "Submit:  绝地邮兵_result_ba_bon_${CONCEPT}_submit.json" | tee -a "$LOG"
