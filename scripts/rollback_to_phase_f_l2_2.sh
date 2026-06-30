#!/usr/bin/env bash
# Rollback to Phase F L2_2-only official best (0.6714)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/archive/submissions/01_milestones/绝地邮兵_result_phase_f_l2_2_retrain_0.6714.json"
MERGED="$ROOT/archive/submissions/01_milestones/绝地邮兵_result_phase_f_merged.json"
VPL="$ROOT/easyedit_reps/outputs/vectors/per_layer"
ARCH="$ROOT/archive/outputs/vectors"

[[ -f "$SRC" ]] || { echo "Missing $SRC"; exit 1; }

# Archive failed merge if at root
if [[ -f "$ROOT/绝地邮兵_result.json" ]] && ! cmp -s "$ROOT/绝地邮兵_result.json" "$SRC"; then
  cp -f "$ROOT/绝地邮兵_result.json" "$ROOT/archive/submissions/02_phase_f/绝地邮兵_result_phase_f_merged_0.6583.json" 2>/dev/null || \
  mkdir -p "$ROOT/archive/submissions/02_phase_f" && \
  cp -f "$ROOT/绝地邮兵_result.json" "$ROOT/archive/submissions/02_phase_f/绝地邮兵_result_phase_f_merged_0.6583.json"
fi

cp -f "$SRC" "$ROOT/绝地邮兵_result.json"
cp -f "$SRC" "$ROOT/baseline/submission.json"
cp -f "$SRC" "$ROOT/archive/submissions/00_current/绝地邮兵_result.json"

# Restore vectors overwritten by merge (L2_3 L16, L2_5 L18)
for spec in "L2_3:16" "L2_5:18"; do
  IFS=: read -r CID L <<< "$spec"
  bak="$ARCH/per_layer_${CID}_layer${L}_phase_f"
  dst="$VPL/$CID/layer_${L}"
  if [[ -d "$bak" ]]; then
    rm -rf "$dst"
    cp -a "$bak" "$dst"
    echo "Restored vector $CID L$L"
  fi
done

# layers + mult (phase_c + L2_2 only)
python3 <<'PY'
import json
from pathlib import Path
root = Path("/root/CCKS2026-Steering")
layers = json.loads((root / "baseline/layers.json").read_text())
mult = json.loads((root / "baseline/multipliers.json").read_text())

# phase_c layers for L2 (L2_6/L2_7 were wrongly set to 16 in merge)
layers["concepts"]["L2_6"]["layer"] = 18
layers["concepts"]["L2_7"]["layer"] = 18

# phase_c mult + L2_2 m=3.5
phase_c_l2 = {"L2_1": 3.5, "L2_2": 3.5, "L2_3": 2.0, "L2_4": 3.0, "L2_5": 3.0, "L2_6": 4.0, "L2_7": 3.0, "L2_8": 2.5}
mult.update(phase_c_l2)

(root / "baseline/layers.json").write_text(json.dumps(layers, indent=2) + "\n", encoding="utf-8")
(root / "baseline/multipliers.json").write_text(json.dumps(mult, indent=2) + "\n", encoding="utf-8")
print("Restored layers.json + multipliers.json (L2_2-only config)")
PY

echo "Rollback done. Official best: 0.6714 (L2_2 only)"
