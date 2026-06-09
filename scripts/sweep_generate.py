from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import read_json, write_json


def parse_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_floats(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def run_command(args: list[str]) -> None:
    print(" ".join(args))
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_caa.json")
    parser.add_argument("--layers", default="16,20,24,28,32")
    parser.add_argument("--strengths", default="0.5,1.0,1.5,2.0")
    parser.add_argument("--gold", default="valid.json")
    parser.add_argument("--out-dir", default="runs/sweeps/baseline_caa")
    parser.add_argument("--limit-per-concept", type=int)
    parser.add_argument("--allow-partial-eval", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    layers = parse_ints(args.layers)
    strengths = parse_floats(args.strengths)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for layer in layers:
        for strength in strengths:
            run_dir = out_dir / f"layer_{layer}_strength_{strength:g}"
            pred_path = run_dir / "predictions.json"
            eval_path = run_dir / "local_eval.json"
            run_dir.mkdir(parents=True, exist_ok=True)

            if args.overwrite or not pred_path.exists():
                command = [
                    sys.executable,
                    "scripts/generate.py",
                    "--config",
                    args.config,
                    "--layer",
                    str(layer),
                    "--strength",
                    str(strength),
                    "--out",
                    str(pred_path),
                ]
                if args.limit_per_concept is not None:
                    command.extend(["--limit-per-concept", str(args.limit_per_concept)])
                run_command(command)
            else:
                print(f"Skip existing predictions: {pred_path}")

            row = {
                "layer": layer,
                "strength": strength,
                "predictions": str(pred_path),
                "local_eval": str(eval_path),
                "mean_hm_proxy": None,
            }

            if not args.skip_eval:
                if args.overwrite or not eval_path.exists():
                    command = [
                        sys.executable,
                        "scripts/local_eval.py",
                        "--gold",
                        args.gold,
                        "--pred",
                        str(pred_path),
                        "--out",
                        str(eval_path),
                    ]
                    if args.allow_partial_eval:
                        command.append("--allow-partial")
                    run_command(command)
                else:
                    print(f"Skip existing eval: {eval_path}")
                row["mean_hm_proxy"] = read_json(eval_path).get("mean_hm_proxy")

            summary.append(row)

    summary_path = out_dir / "summary.json"
    write_json(summary_path, summary)
    print(f"Wrote {summary_path}")
    if any(row["mean_hm_proxy"] is not None for row in summary):
        best = max((row for row in summary if row["mean_hm_proxy"] is not None), key=lambda row: row["mean_hm_proxy"])
        print(json.dumps({"best": best}, ensure_ascii=False))


if __name__ == "__main__":
    main()
