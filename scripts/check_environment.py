from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import transformers
from transformers import AutoConfig

from ccks_steering.config import load_config, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_caa.json")
    parser.add_argument("--out", default="runs/environment_report.json")
    args = parser.parse_args()

    config = load_config(args.config)
    cuda = torch.cuda.is_available()
    report = {
        "python": sys.version,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda_available": cuda,
        "cuda_device_count": torch.cuda.device_count() if cuda else 0,
        "cuda_devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())] if cuda else [],
        "model_name_or_path": config["model_name_or_path"],
        "model_config_cached": False,
        "model_config_error": None,
    }
    try:
        model_config = AutoConfig.from_pretrained(
            config["model_name_or_path"],
            trust_remote_code=True,
            local_files_only=True,
        )
        report["model_config_cached"] = True
        report["model_type"] = getattr(model_config, "model_type", None)
        report["num_hidden_layers"] = getattr(model_config, "num_hidden_layers", None)
        report["hidden_size"] = getattr(model_config, "hidden_size", None)
    except Exception as exc:
        report["model_config_error"] = str(exc)

    write_json(args.out, report)
    print(f"Wrote {args.out}")
    print(f"torch={report['torch']} cuda={report['cuda_available']} transformers={report['transformers']}")
    print(f"model_config_cached={report['model_config_cached']}")


if __name__ == "__main__":
    main()
