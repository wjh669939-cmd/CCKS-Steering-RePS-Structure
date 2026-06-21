#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/env.sh"

echo "[L3 sweep] RePS multiplier search for L3_1..L3_8"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  "$ROOT/.venv/bin/python" "$ROOT/scripts/sweep_l3_multipliers.py" \
  --multipliers "${MULTIPLIERS:-0.5,1.0,1.5,2.0,2.5,3.0}" \
  "$@"

echo "[L3 sweep] Export submission + local eval"
bash "$ROOT/scripts/merge_and_eval_l3_tuned.sh"
