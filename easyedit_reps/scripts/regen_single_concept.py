#!/usr/bin/env python3
"""Regenerate one concept with multiple multipliers; pick best by local HM."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
EASYEDIT_ROOT = ROOT / "EasyEdit"
sys.path.insert(0, str(EASYEDIT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from steer.datasets.dataset_loader import DatasetLoader
from steer.vector_appliers.vector_applier import BaseVectorApplier
from scripts.local_eval import score_item

VECTOR_ROOT = ROOT / "outputs/vectors/ccks_baseline_reps"


def build_cfg(multiplier: float) -> OmegaConf:
    return OmegaConf.create(
        {
            "model_name_or_path": "/root/autodl-tmp/models/Qwen3-4B-Instruct-2507",
            "dtype": "bfloat16",
            "device": "cuda:0",
            "seed": 42,
            "use_chat_template": True,
            "system_prompt": "",
            "use_cache": True,
            "generate_orig_output": False,
            "vllm_enable": False,
            "vllm_gpu_memory_utilization": 0.9,
            "vllm_max_model_len": None,
            "save_activations": True,
            "enable_thinking": None,
            "method": "reps",
            "dataset": "SteerEval/personality",
            "exp": "valid",
            "layers": [18],
            "multipliers": [multiplier],
            "apply_steer_hparam_paths": [
                str(EASYEDIT_ROOT / "hparams/Steer/ccks2026_hparams/qwen3-4b-it/reps/apply_reps.yaml")
            ],
            "steer_vector_load_dir": [str(VECTOR_ROOT)],
            "generation_output_dir": str(ROOT / "outputs/generation/regen"),
            "generation_data_size": None,
            "num_responses": 1,
            "steer_from_end_position": False,
            "generation_params": {
                "max_new_tokens": 256,
                "temperature": 0,
                "do_sample": False,
            },
        }
    )


def main() -> None:
    os.chdir(EASYEDIT_ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", required=True)
    parser.add_argument("--multipliers", default="2.0,2.5,3.0")
    parser.add_argument("--gold", type=Path, default=PROJECT_ROOT / "valid.json")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/generation/regen/out.json")
    args = parser.parse_args()

    gold_map = {
        (r["concept_id"], r["question"]): r
        for r in json.loads(args.gold.read_text(encoding="utf-8"))
        if r["concept_id"] == args.concept
    }
    loader = DatasetLoader(config_path=str(EASYEDIT_ROOT / "hparams/Steer/dataset_format.yaml"))
    eval_data = loader.load_file("SteerEval/personality", "valid")[args.concept]

    best = None
    for mult in [float(x) for x in args.multipliers.split(",")]:
        print(f"concept={args.concept} multiplier={mult}")
        applier = BaseVectorApplier(build_cfg(mult))
        applier._load_model()
        applier.hparams_dict["reps"].steer_vector_load_dir = str(
            VECTOR_ROOT / f"steer_eval_concept_{args.concept}" / "reps_vector"
        )
        applier.hparams_dict["reps"].multipliers = [mult]
        applier.apply_vectors()
        generated = applier.generate({"steer_eval_eval": eval_data}, save_results=False)
        applier.model.reset_all()
        del applier.model
        import torch

        torch.cuda.empty_cache()

        rows = []
        for item in generated:
            g = gold_map[(args.concept, item["input"])]
            rows.append(score_item(g, {"answer": item["pred"][0]}))
        hm = sum(r["hm_proxy"] for r in rows) / len(rows)
        print(f"  hm={hm:.3f}")
        if best is None or hm > best["hm"]:
            best = {"hm": hm, "mult": mult, "generated_results": generated}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "concept_id": args.concept,
                "best_multiplier": best["mult"],
                "hm_proxy": best["hm"],
                "generated_results": best["generated_results"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {args.out} best_mult={best['mult']} hm={best['hm']:.3f}")


if __name__ == "__main__":
    main()
