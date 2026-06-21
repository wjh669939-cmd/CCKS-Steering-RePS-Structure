#!/usr/bin/env bash
# 激活 easyedit_reps 专用环境（复用主项目 torch/transformers，额外安装 hydra 等）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export EASYEDIT_REPS_ROOT="$ROOT"
export EASYEDIT_ROOT="$ROOT/EasyEdit"
export VIRTUAL_ENV="$ROOT/.venv"
export PATH="$ROOT/.venv/bin:$PATH"
export PYTHONPATH="$EASYEDIT_ROOT:${PYTHONPATH:-}"
