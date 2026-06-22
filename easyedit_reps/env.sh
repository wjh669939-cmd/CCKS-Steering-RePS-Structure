#!/usr/bin/env bash
# 激活 easyedit_reps 专用环境（复用系统 torch，.venv 装其余依赖）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export EASYEDIT_REPS_ROOT="$ROOT"
export EASYEDIT_ROOT="$ROOT/EasyEdit"
export VIRTUAL_ENV="$ROOT/.venv"
export PATH="$ROOT/.venv/bin:$PATH"
PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONDA_SITE="${CONDA_SITE:-/root/miniconda3/lib/python${PYVER}/site-packages}"
export PYTHONPATH="$EASYEDIT_ROOT:$CONDA_SITE:${PYTHONPATH:-}"
