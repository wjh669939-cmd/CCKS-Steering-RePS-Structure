#!/usr/bin/env bash
# Build A/B submission files for official score optimization:
#   A) raw RePS (512 tokens, tuned multipliers, no postprocess)
#   B) official-light postprocess (disclaimer strip + L3 constraints + sentence fix)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RAW="${1:-绝地邮兵_result_pre_optimize_long.json}"
OUT_RAW="${2:-$RAW}"
OUT_OFFICIAL="${3:-绝地邮兵_result_official.json}"

if [[ ! -f "$RAW" ]]; then
  echo "Missing raw submission: $RAW"
  echo "Run: cd easyedit_reps && source env.sh && .venv/bin/python scripts/regen_tuned_all.py"
  exit 1
fi

echo "=== Version A: raw RePS (no postprocess) ==="
if [[ "$RAW" != "$OUT_RAW" ]]; then
  cp -f "$RAW" "$OUT_RAW"
fi
python3 - <<PY
import json
from pathlib import Path

def audit(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    bad = total = 0
    for b in data:
        for g in b["generated_results"]:
            total += 1
            t = (g.get("pred") or [""])[0]
            if len(t) > 200 and t.rstrip()[-1] not in '.!?"\\'」』）]':
                bad += 1
    print(f"  {path}: truncation {bad}/{total}")

audit("$OUT_RAW")
PY

echo "=== Version B: official-light postprocess ==="
python scripts/postprocess_submission.py --in "$RAW" --out "$OUT_OFFICIAL" --mode official

echo "Done."
echo "  Submit A (raw):      $OUT_RAW"
echo "  Submit B (official): $OUT_OFFICIAL"
