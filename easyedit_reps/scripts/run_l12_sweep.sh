#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/env.sh"

echo "[L1/L2 sweep] RePS multiplier search for L1_1..L2_8"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  "$ROOT/.venv/bin/python" "$ROOT/scripts/sweep_l12_multipliers.py" \
  --multipliers "${MULTIPLIERS:-0.5,1.0,1.5,2.0,2.5,3.0}" \
  "$@"

OUT_DIR="$ROOT/outputs/generation/l12_tuned"
SUBMISSION="$PROJECT_ROOT/绝地邮兵_result.json"

echo "[L1/L2 sweep] Export submission + local eval"
cd "$EASYEDIT_ROOT"
"$ROOT/.venv/bin/python" "$ROOT/scripts/export_submission.py" \
  --in "$OUT_DIR/all_generation_results_valid.json" \
  --out "$SUBMISSION"

cd "$PROJECT_ROOT"
python3 <<'PY'
import json
from pathlib import Path

valid = json.loads(Path("valid.json").read_text(encoding="utf-8"))
submission = json.loads(Path("绝地邮兵_result.json").read_text(encoding="utf-8"))
valid_map = {(r["concept_id"], r["question"]): r for r in valid}
predictions = []
for block in submission:
    cid = block["concept_id"]
    for item in block["generated_results"]:
        rec = valid_map[(cid, item["input"])]
        pred = item.get("pred") or []
        predictions.append({
            "domain": rec["domain"],
            "concept_id": cid,
            "concept": rec["concept"],
            "question_id": rec["question_id"],
            "question": item["input"],
            "answer": pred[0] if pred else "",
            "steering_method": "reps_l12_l3_tuned",
        })
out = Path("runs/reps_full_tuned/predictions.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {out}")
PY

python scripts/local_eval.py \
  --gold valid.json \
  --pred runs/reps_full_tuned/predictions.json \
  --out runs/reps_full_tuned/local_eval.json
