#!/usr/bin/env bash
# 整理提交 JSON：根目录只保留官方最优，其余按阶段归档到 archive/submissions/
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUB="$ROOT/archive/submissions"
mkdir -p \
  "$SUB/00_current" \
  "$SUB/01_milestones" \
  "$SUB/02_phase_f" \
  "$SUB/02_phase_d" \
  "$SUB/03_phase_e" \
  "$SUB/04_pilot" \
  "$SUB/05_ablation" \
  "$SUB/06_ba_bon" \
  "$SUB/06_early"

mv_if() {
  local src="$1" dst="$2"
  [[ -f "$src" ]] || return 0
  mkdir -p "$(dirname "$dst")"
  if [[ -f "$dst" ]]; then
    echo "  skip (exists): $(basename "$dst")"
  else
    mv -v "$src" "$dst"
  fi
}

echo "=== Organize submissions ==="

# 根目录：仅保留主提交
if [[ -f "$ROOT/绝地邮兵_result.json" ]]; then
  cp -f "$ROOT/绝地邮兵_result.json" "$SUB/00_current/绝地邮兵_result.json"
  ln -sf "../../绝地邮兵_result.json" "$SUB/00_current/LINK_to_root.json" 2>/dev/null || true
fi

# 根目录实验提交 → 归档
for f in "$ROOT"/绝地邮兵_result_*.json; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f")"
  case "$base" in
    phase_d*|*phase_d*)
      mv_if "$f" "$SUB/02_phase_d/$base"
      ;;
    phase_e*|*phase_e*)
      mv_if "$f" "$SUB/03_phase_e/$base"
      ;;
    pilot_*|*pilot_*)
      mv_if "$f" "$SUB/04_pilot/$base"
      ;;
    ba_bon_*|*ba_bon*)
      mv_if "$f" "$SUB/06_ba_bon/$base"
      ;;
    *phase_f_L2*|*phase_f_l2*)
      mv_if "$f" "$SUB/02_phase_f/$base"
      ;;
    round5_*|l1_1_*|l3_*|*caa*|*hybrid*|*token_direction*)
      mv_if "$f" "$SUB/05_ablation/$base"
      ;;
    *)
      mv_if "$f" "$SUB/05_ablation/$base"
      ;;
  esac
done

# 扁平 archive/submissions 历史文件 → 分子目录
classify() {
  local base="$1"
  case "$base" in
    绝地邮兵_result.json|绝地邮兵_result_best.json) ;;
    绝地邮兵_result_phase_c*|*phase_c*)
      mv_if "$SUB/$base" "$SUB/01_milestones/$base" ;;
    *phase_f_l2_2*|*phase_f*0.6714*)
      mv_if "$SUB/$base" "$SUB/01_milestones/$base" ;;
    *phase_f_merged*|*merged_0.6583*)
      mv_if "$SUB/$base" "$SUB/02_phase_f/$base" ;;
    *phase_d*)
      mv_if "$SUB/$base" "$SUB/02_phase_d/$base" ;;
    *phase_e*)
      mv_if "$SUB/$base" "$SUB/03_phase_e/$base" ;;
    *pilot*)
      mv_if "$SUB/$base" "$SUB/04_pilot/$base" ;;
    *ba_bon*)
      mv_if "$SUB/$base" "$SUB/06_ba_bon/$base" ;;
    *best_merge*|*weak8*|*pre_optimize*|*regen_768*|*submit1*|*layer20*|*round2*|*round3*|*trunc_fix*|*combo*|*l2_up*|*personality*)
      mv_if "$SUB/$base" "$SUB/01_milestones/$base" ;;
    *phase_b*|*l3_caa*|*matching_pick*|*pos_aware*)
      mv_if "$SUB/$base" "$SUB/05_ablation/$base" ;;
    *)
      [[ -f "$SUB/$base" ]] && mv_if "$SUB/$base" "$SUB/06_early/$base" ;;
  esac
}

for f in "$SUB"/*.json; do
  [[ -f "$f" ]] || continue
  classify "$(basename "$f")"
done

# 配置快照
mkdir -p "$ROOT/baseline/archive"
mv_if "$ROOT/baseline/phase_e_config.json" "$ROOT/baseline/archive/phase_e_config.json"

echo ""
echo "Done. Root keeps: 绝地邮兵_result.json"
echo "Index: docs/SUBMISSIONS.md"
find "$SUB" -maxdepth 2 -name '*.json' | wc -l | xargs echo "Archived json count:"
