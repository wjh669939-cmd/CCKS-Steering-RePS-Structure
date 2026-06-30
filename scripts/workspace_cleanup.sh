#!/usr/bin/env bash
# 工作区清理：归档历史实验产物，保留 baseline + 训练/复现所需文件
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCH="$ROOT/archive"
RUNS="$ARCH/runs"
OUT="$ARCH/outputs"
SCR="$ARCH/scripts"
EXT="$ARCH/external"

mkdir -p "$ARCH/baseline" "$EXT" "$RUNS" "$OUT/sweep" "$OUT/generation" "$OUT/vectors"

echo "=== [1/5] 归档历史提交 JSON ==="
bash "$ROOT/scripts/organize_submissions.sh"

echo "=== [2/5] 归档 runs/ 实验目录 ==="
KEEP_RUNS=(
  phase_a
  phase_c
)
KEEP_RUN_FILES=(
  ba_bon_official.md
  baseline_concept_audit.json
  data_report.json
  environment_report.json
  phase_f_merge_decisions.md
  phase_f_l2_batch.log
  phase_f_l2_picks.json
)

if [[ -d runs ]]; then
  for d in runs/*/; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    keep=0
    for k in "${KEEP_RUNS[@]}"; do
      [[ "$name" == "$k" ]] && keep=1 && break
    done
    if [[ $keep -eq 1 ]]; then
      echo "  keep runs/$name"
    else
      mv -v "$d" "$RUNS/"
    fi
  done
fi

echo "=== [3/5] 归档 easyedit_reps/outputs 中间产物 ==="
EE="$ROOT/easyedit_reps/outputs"
if [[ -d "$EE" ]]; then
  for d in submit1_l3 submit1_l3_low submit_final_l2 round2 personality_trial; do
    [[ -d "$EE/$d" ]] && mv -v "$EE/$d" "$OUT/sweep/"
  done
  if [[ -d "$EE/generation" ]]; then
    for d in "$EE/generation"/*; do
      [[ -e "$d" ]] || continue
      if [[ -d "$d" ]] && [[ -n "$(ls -A "$d" 2>/dev/null)" ]]; then
        mv -v "$d" "$OUT/generation/"
      elif [[ -d "$d" ]]; then
        rmdir "$d" 2>/dev/null || true
      fi
    done
  fi
  if [[ -d "$EE/vectors" ]]; then
    for d in ccks_layer20_reps ccks_l3_caa lora pos_only; do
      [[ -d "$EE/vectors/$d" ]] && mv -v "$EE/vectors/$d" "$OUT/vectors/"
    done
  fi
fi

echo "=== [4/5] 归档 obsolete scripts ==="
for s in \
  run_best_merge.sh run_round2.sh run_round2_optimize.sh \
  run_weak8_layer_pilot.sh run_weak8_l3_mult_sweep.sh \
  run_submit1_l3.sh run_submit1_l3_low.sh run_submit2_l2.sh run_submit_final.sh \
  run_layer20_trial.sh run_l3_caa.sh run_matching_pick.sh \
  run_personality_trial.sh run_pos_aware_regen.sh \
  run_round3_l3_partial_sweep.sh run_round3_pos_only.sh \
  run_phase_b_l3_lora.sh \
  finalize_submission.sh finalize_official_submission.sh; do
  [[ -f "scripts/$s" ]] && mv -v "scripts/$s" "$SCR/"
done

echo "=== [5/5] 精简 baseline/ 重复项 ==="
rm -f baseline/phase_c_layers.json baseline/phase_c_multipliers.json
[[ -f baseline/round3_l3_partial_mult.json ]] && mv -v baseline/round3_l3_partial_mult.json "$ARCH/baseline/"
[[ -f baseline/layer20_manifest.json ]] && mv -v baseline/layer20_manifest.json "$ARCH/baseline/"
[[ -f baseline/round2_manifest.json ]] && mv -v baseline/round2_manifest.json "$ARCH/baseline/"
rm -f 绝地邮兵_result_baseline_v1.json
[[ -d 大创 ]] && mv -v 大创 "$EXT/"

echo ""
echo "Done. Active workspace:"
echo "  绝地邮兵_result.json          (0.6714 主提交)"
echo "  baseline/{submission,layers,multipliers,concept_lock}.json"
echo "  easyedit_reps/outputs/vectors/{per_layer,ccks_baseline_reps,retrain_pilot,retrain_pilot_l1}"
echo "  scripts/{regen_from_baseline,rollback*,run_l2_2_mult_sweep,check_concept_lock}.sh"
echo "  runs/{phase_a,phase_c,ba_bon_official.md,baseline_concept_audit.json}"
echo "Archive: $ARCH/"
