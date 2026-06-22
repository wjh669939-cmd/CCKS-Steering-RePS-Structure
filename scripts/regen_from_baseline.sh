#!/usr/bin/env bash
# 从 baseline/multipliers.json 重生成提交（raw，无后处理）
# 用法: bash scripts/regen_from_baseline.sh [max_new_tokens] [tag]
# 示例: bash scripts/regen_from_baseline.sh 768
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/easyedit_reps"
source env.sh

MAX_TOKENS="${1:-512}"
TAG="${2:-$MAX_TOKENS}"

.venv/bin/python scripts/regen_tuned_all.py \
  --max-new-tokens "$MAX_TOKENS" \
  --tag "$TAG" \
  --multipliers "$PROJECT_ROOT/baseline/multipliers.json"
