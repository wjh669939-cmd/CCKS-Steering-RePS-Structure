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
export CONDA_NO_PLUGINS="${CONDA_NO_PLUGINS:-true}"
export CONDA_SOLVER="${CONDA_SOLVER:-classic}"
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

cd "$PROJECT_DIR"

ENV_READY=0
if command -v conda >/dev/null 2>&1; then
  set +e
  eval "$(CONDA_NO_PLUGINS=true CONDA_SOLVER=classic conda shell.bash hook)"
  CONDA_HOOK_STATUS=$?
  if [ "$CONDA_HOOK_STATUS" -eq 0 ]; then
    CONDA_CREATE_STATUS=0
    if ! CONDA_NO_PLUGINS=true CONDA_SOLVER=classic conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
      CONDA_NO_PLUGINS=true CONDA_SOLVER=classic conda create -n "$ENV_NAME" "python=$PYTHON_VERSION" -y
      CONDA_CREATE_STATUS=$?
    fi
    if [ "$CONDA_CREATE_STATUS" -eq 0 ]; then
      conda activate "$ENV_NAME"
      CONDA_ACTIVATE_STATUS=$?
      if [ "$CONDA_ACTIVATE_STATUS" -eq 0 ]; then
        ENV_READY=1
      fi
    fi
  fi
  set -e
fi

if [ "$ENV_READY" -eq 0 ]; then
  echo "Conda is unavailable or failed; falling back to .venv-autodl"
  PYTHON_BIN="$(command -v python3 || command -v python)"
  "$PYTHON_BIN" -m venv .venv-autodl
  # shellcheck disable=SC1091
  source .venv-autodl/bin/activate
fi

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
