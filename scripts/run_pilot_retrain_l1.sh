#!/usr/bin/env bash
# Pilot: retrain one L1 concept RePS vectors (train-only pick layer), sweep mult, merge preview
# Usage: bash scripts/run_pilot_retrain_l1.sh L1_4
# Skip frozen: L1_1, L1_8
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/easyedit_reps"
source env.sh

CONCEPT="${1:?usage: run_pilot_retrain_l1.sh L1_X}"
if [[ ! "$CONCEPT" =~ ^L1_[0-9]+$ ]]; then
  echo "Error: concept must be L1_* (got $CONCEPT)" >&2
  exit 1
fi
if [[ "$CONCEPT" == "L1_1" || "$CONCEPT" == "L1_8" ]]; then
  echo "Error: $CONCEPT is frozen (official stubborn). Pick L1_2–L1_7 except L1_1/L1_8." >&2
  exit 1
fi

RUN="$PROJECT_ROOT/runs/pilot_retrain_${CONCEPT,,}"
VROOT="$EASYEDIT_REPS_ROOT/outputs/vectors/retrain_pilot_l1"
SWEEP="$RUN/sweep"
BASE="$PROJECT_ROOT/baseline/submission.json"
LAYERS_JSON="$PROJECT_ROOT/baseline/layers.json"
MULT_JSON="$PROJECT_ROOT/baseline/multipliers.json"
OUT="$PROJECT_ROOT/绝地邮兵_result_pilot_retrain_${CONCEPT}.json"
LOG="$RUN/run.log"
mkdir -p "$RUN" "$SWEEP"

BASE_LAYER=$(python3 -c "
import json
raw = json.load(open('$LAYERS_JSON'))
m = raw.get('concepts', raw)
print(m['$CONCEPT']['layer'] if isinstance(m['$CONCEPT'], dict) else m['$CONCEPT'])
")
BASE_MULT=$(python3 -c "import json; print(json.load(open('$MULT_JSON'))['$CONCEPT'])")

MULTS=$(python3 - <<PY
base = float("$BASE_MULT")
cands = sorted({round(x, 1) for x in (base - 1.0, base - 0.5, base, base + 0.5, base + 1.0) if 1.5 <= x <= 5.0})
print(",".join(str(x) for x in cands))
PY
)

echo "=== L1 retrain pilot: $CONCEPT (baseline L${BASE_LAYER} m=${BASE_MULT}, sweep m=${MULTS}) ===" | tee "$LOG"
echo "Vector root: $VROOT (separate from falsified L2 retrain_pilot)" | tee -a "$LOG"

for L in 16 18 20; do
  echo "--- train $CONCEPT layer=$L ---" | tee -a "$LOG"
  .venv/bin/python scripts/train_single_concept_layer.py \
    --concept "$CONCEPT" \
    --layer "$L" \
    --vector-base "$VROOT" \
    --force \
    2>&1 | tee "$RUN/train_L${L}.log"
done

echo "" | tee -a "$LOG"
echo "--- pick layer on train (10 samples) ---" | tee -a "$LOG"
.venv/bin/python scripts/pick_layer_on_train.py \
  --concept "$CONCEPT" \
  --layers "16,18,20" \
  --vector-base "$VROOT" \
  --train-samples 10 \
  --out "$RUN/layer_pick.json" \
  2>&1 | tee -a "$LOG"

PICK_L=$(python3 -c "import json; print(json.load(open('$RUN/layer_pick.json'))['best_layer'])")
echo "Picked layer: $PICK_L" | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "--- regen valid: mult ${MULTS} @ L${PICK_L} ---" | tee -a "$LOG"
.venv/bin/python scripts/sweep_l12_weak.py \
  --concept "$CONCEPT" \
  --multipliers "$MULTS" \
  --layers "$PICK_L" \
  --per-layer-base "$VROOT" \
  --out-dir "$SWEEP" \
  --tag retrain_pilot_l1 \
  2>&1 | tee "$RUN/sweep.log"

DEFAULT_M="$BASE_MULT"
PATCH="$SWEEP/${CONCEPT}_L${PICK_L}_m${DEFAULT_M}.json"
if [[ ! -f "$PATCH" ]]; then
  PATCH=$(ls "$SWEEP/${CONCEPT}_L${PICK_L}_m"*.json 2>/dev/null | grep -v _best | grep -v _summary | head -1)
fi
python "$PROJECT_ROOT/scripts/merge_submission.py" \
  --base "$BASE" \
  --patch "$PATCH" \
  --concepts "$CONCEPT" \
  --out "$OUT"

for p in "$SWEEP/${CONCEPT}_L${PICK_L}_m"*.json; do
  [[ -f "$p" ]] || continue
  [[ "$p" == *"_best"* || "$p" == *"_summary"* ]] && continue
  m=$(basename "$p" .json | sed "s/.*_m//")
  mtag=${m//./p}
  python "$PROJECT_ROOT/scripts/merge_submission.py" \
    --base "$BASE" \
    --patch "$p" \
    --concepts "$CONCEPT" \
    --out "$PROJECT_ROOT/绝地邮兵_result_pilot_retrain_${CONCEPT}_m${mtag}.json" \
    2>/dev/null || true
done

python3 <<PY | tee -a "$LOG"
import json
from pathlib import Path

base = next(b for b in json.loads(Path("$BASE").read_text()) if b["concept_id"] == "$CONCEPT")
cands = {}
for p in sorted(Path("$SWEEP").glob("${CONCEPT}_L*_m*.json")):
    if "_best" in p.name or "_summary" in p.name:
        continue
    block = json.loads(p.read_text())
    if isinstance(block, list):
        block = next(b for b in block if b["concept_id"] == "$CONCEPT")
    m = p.stem.split("_m", 1)[1]
    cands[m] = block

print(f"\n=== $CONCEPT 肉眼对比 (baseline L${BASE_LAYER} m=${BASE_MULT}) ===")
print(base["concept_name"])
for i, g in enumerate(base["generated_results"]):
    print(f"\n{'='*70}")
    print(f"Q{i+1}: {g['input']}")
    print(f"\n[baseline] ({len(g['pred'][0])}c)")
    print(g["pred"][0])
    for m in sorted(cands.keys(), key=lambda x: float(x)):
        ans = cands[m]["generated_results"][i]["pred"][0]
        tag = f"retrain L$PICK_L m={m}"
        if ans == g["pred"][0]:
            print(f"\n[{tag}] 与 baseline 相同")
        else:
            print(f"\n[{tag}] ({len(ans)}c)")
            print(ans)

print(f"\nFiles: $SWEEP | default: $OUT")
print("Official A/B: bash scripts/merge_pilot_submit.sh $CONCEPT [mult]")
PY

echo "" | tee -a "$LOG"
echo "Done $CONCEPT. Review $LOG before official submit." | tee -a "$LOG"
