#!/usr/bin/env bash
# Finalize submission: RePS tuned base + L3 constraints + L1/L2 cleanup
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BASE="${1:-绝地邮兵_result_pre_optimize.json}"
OUT="${2:-绝地邮兵_result.json}"

python scripts/postprocess_submission.py --in "$BASE" --out "$OUT"

python3 <<'PY'
import json
from pathlib import Path

valid = json.loads(Path("valid.json").read_text(encoding="utf-8"))
sub = json.loads(Path("绝地邮兵_result.json").read_text(encoding="utf-8"))
vm = {(r["concept_id"], r["question"]): r for r in valid}
preds = []
for b in sub:
    for g in b["generated_results"]:
        r = vm[(b["concept_id"], g["input"])]
        preds.append(
            {
                "domain": r["domain"],
                "concept_id": b["concept_id"],
                "concept": r["concept"],
                "question_id": r["question_id"],
                "question": g["input"],
                "answer": g["pred"][0],
                "steering_method": "reps_postprocessed",
            }
        )
out = Path("runs/reps_postprocessed/predictions.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(preds, ensure_ascii=False, indent=2), encoding="utf-8")
PY

python scripts/local_eval.py \
  --gold valid.json \
  --pred runs/reps_postprocessed/predictions.json \
  --out runs/reps_postprocessed/local_eval.json
