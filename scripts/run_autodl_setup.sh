#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${ENV_NAME:-ccks}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu128}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"

if [ -f /etc/network_turbo ]; then
  # AutoDL academic network acceleration.
  # shellcheck disable=SC1091
  source /etc/network_turbo
fi

export HF_HOME="${HF_HOME:-/root/autodl-tmp/cache/huggingface}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/transformers}"
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE"

pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

if command -v git-lfs >/dev/null 2>&1; then
  git lfs install
else
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y git-lfs
    git lfs install
  fi
fi

if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    conda create -n "$ENV_NAME" "python=$PYTHON_VERSION" -y
  fi
  conda activate "$ENV_NAME"
fi

cd "$PROJECT_DIR"
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio --index-url "$TORCH_INDEX_URL"
python -m pip install -r requirements.txt

python - <<'PY'
import torch

print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
    print("memory_gb", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))
PY

python scripts/check_environment.py --config configs/baseline_caa.json --out runs/environment_report.json
