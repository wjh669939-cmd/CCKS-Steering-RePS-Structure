#!/usr/bin/env python3
"""Regenerate all 24 concepts with tuned multipliers and longer max_new_tokens."""
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

DEFAULT_VECTOR_ROOT = ROOT / "outputs/vectors/ccks_baseline_reps"
DEFAULT_LAYER = 18
L3_MULT = ROOT / "outputs/generation/l3_tuned/best_l3_multipliers.json"
L12_MULT = ROOT / "outputs/generation/l12_tuned/best_l12_multipliers.json"
ALL_CONCEPTS = [f"L1_{i}" for i in range(1, 9)] + [f"L2_{i}" for i in range(1, 9)] + [f"L3_{i}" for i in range(1, 9)]


def build_cfg(
    multiplier: float,
    max_new_tokens: int,
    tag: str,
    layer: int = DEFAULT_LAYER,
    vector_root: Path | None = None,
    steer_from_end_position: bool = False,
) -> OmegaConf:
    vector_root = vector_root or DEFAULT_VECTOR_ROOT
    out_dir = ROOT / f"outputs/generation/regen_{tag}"
    return OmegaConf.create(
        {
            "model_name_or_path": os.environ.get(
                "REPS_MODEL_PATH", "/root/autodl-tmp/models/Qwen3-4B-Instruct-2507"
            ),
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
            "layers": [layer],
            "multipliers": [multiplier],
            "apply_steer_hparam_paths": [
                str(EASYEDIT_ROOT / "hparams/Steer/ccks2026_hparams/qwen3-4b-it/reps/apply_reps.yaml")
            ],
            "steer_vector_load_dir": [str(vector_root)],
            "generation_output_dir": str(out_dir),
            "generation_data_size": None,
            "num_responses": 1,
            "steer_from_end_position": steer_from_end_position,
            "generation_params": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0,
                "do_sample": False,
            },
        }
    )


def load_multipliers(path: Path | None = None) -> dict[str, float]:
    if path is not None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if all(isinstance(v, (int, float)) for v in raw.values()):
            return {k: float(v) for k, v in raw.items()}
        out = {k: float(v["best_multiplier"]) for k, v in raw.items()}
        for cid in ALL_CONCEPTS:
            if cid not in out:
                raise KeyError(f"Missing tuned multiplier for {cid}")
        return out
    l3 = json.loads(L3_MULT.read_text(encoding="utf-8"))
    l12 = json.loads(L12_MULT.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    for cid, info in l3.items():
        out[cid] = float(info["best_multiplier"])
    for cid, info in l12.items():
        out[cid] = float(info["best_multiplier"])
    for cid in ALL_CONCEPTS:
        if cid not in out:
            raise KeyError(f"Missing tuned multiplier for {cid}")
    return out


def train_meta(train_path: Path) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for rec in json.loads(train_path.read_text(encoding="utf-8")):
        cid = rec["concept_id"]
        if cid not in meta:
            meta[cid] = {
                "concept_name": rec["concept"],
                "concept_description": rec.get("concept_description") or rec.get("llm_description"),
            }
    return meta


def generate_concept(
    concept_id: str,
    multiplier: float,
    max_new_tokens: int,
    tag: str,
    eval_data,
    layer: int = DEFAULT_LAYER,
    vector_root: Path | None = None,
    steer_from_end_position: bool = False,
    intervention_method: str = "vector",
) -> list[dict]:
    vector_root = vector_root or DEFAULT_VECTOR_ROOT
    applier = BaseVectorApplier(
        build_cfg(
            multiplier,
            max_new_tokens,
            tag,
            layer,
            vector_root,
            steer_from_end_position=steer_from_end_position,
        )
    )
    applier._load_model()
    applier.hparams_dict["reps"].steer_vector_load_dir = str(
        vector_root / f"steer_eval_concept_{concept_id}" / f"reps_{intervention_method}"
    )
    applier.hparams_dict["reps"].multipliers = [multiplier]
    applier.hparams_dict["reps"].intervention_method = intervention_method
    applier.apply_vectors()
    generated = applier.generate({"steer_eval_eval": eval_data}, save_results=False)
    applier.model.reset_all()
    del applier.model
    import torch

    torch.cuda.empty_cache()
    return generated


def to_submission_block(concept_id: str, generated: list[dict], meta: dict) -> dict:
    results = []
    for item in generated:
        pred = item.get("pred") or [""]
        answer = pred[0] if pred else ""
        results.append(
            {
                "input": item["input"],
                "orig_pred": item.get("orig_pred", []),
                "pred": [answer],
                "reference_response": item.get("reference_response"),
                "complete_output": item.get("complete_output") or [answer],
            }
        )
    return {
        "concept_id": concept_id,
        "concept_name": meta[concept_id]["concept_name"],
        "concept_description": meta[concept_id]["concept_description"],
        "generation_prompt": None,
        "generated_results": results,
    }


def main() -> None:
    os.chdir(EASYEDIT_ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--tag", type=str, default=None, help="Output subdir regen_{tag}; default=max_new_tokens")
    parser.add_argument(
        "--multipliers",
        type=Path,
        default=None,
        help="Optional multipliers json (baseline/multipliers.json or sweep output)",
    )
    parser.add_argument(
        "--out-raw",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--out-export",
        type=Path,
        default=None,
    )
    parser.add_argument("--train", type=Path, default=PROJECT_ROOT / "train.json")
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument(
        "--vector-root",
        type=Path,
        default=None,
        help="Steering vector root dir (default: outputs/vectors/ccks_baseline_reps)",
    )
    args = parser.parse_args()

    vector_root = args.vector_root or DEFAULT_VECTOR_ROOT
    tag = args.tag or str(args.max_new_tokens)
    if args.out_raw is None:
        args.out_raw = ROOT / f"outputs/generation/regen_{tag}/all_generation_results_valid.json"
    if args.out_export is None:
        args.out_export = PROJECT_ROOT / f"绝地邮兵_result_regen_{tag}.json"

    multipliers = load_multipliers(args.multipliers)
    meta = train_meta(args.train)
    loader = DatasetLoader(config_path=str(EASYEDIT_ROOT / "hparams/Steer/dataset_format.yaml"))
    eval_datasets = loader.load_file("SteerEval/personality", "valid")

    submission: list[dict] = []
    for cid in ALL_CONCEPTS:
        mult = multipliers[cid]
        print(
            f"[regen] {cid} layer={args.layer} multiplier={mult} "
            f"max_new_tokens={args.max_new_tokens} tag={tag}"
        )
        generated = generate_concept(
            cid,
            mult,
            args.max_new_tokens,
            tag,
            eval_datasets[cid],
            layer=args.layer,
            vector_root=vector_root,
        )
        submission.append(to_submission_block(cid, generated, meta))

    args.out_raw.parent.mkdir(parents=True, exist_ok=True)
    args.out_raw.write_text(json.dumps(submission, ensure_ascii=False, indent=2), encoding="utf-8")
    args.out_export.write_text(json.dumps(submission, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(b["generated_results"]) for b in submission)
    print(f"Wrote {args.out_raw}")
    print(f"Wrote {args.out_export}  concepts={len(submission)} samples={n}")


if __name__ == "__main__":
    main()
