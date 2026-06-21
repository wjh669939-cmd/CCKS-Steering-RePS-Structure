#!/usr/bin/env python3
"""Sweep RePS multipliers for L1/L2 concepts, merge with tuned L3 results."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
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

L12_CONCEPTS = [f"L1_{i}" for i in range(1, 9)] + [f"L2_{i}" for i in range(1, 9)]
VECTOR_ROOT = ROOT / "outputs/vectors/ccks_baseline_reps"
BASE_GENERATION = ROOT / "outputs/generation/l3_tuned/all_generation_results_valid.json"
DEFAULT_GOLD = PROJECT_ROOT / "valid.json"


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
            "generation_output_dir": str(ROOT / "outputs/generation/l12_sweep"),
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


def load_gold(path: Path) -> dict[tuple[str, str], dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return {
        (r["concept_id"], r["question"]): r
        for r in records
        if r["concept_id"].startswith("L1_") or r["concept_id"].startswith("L2_")
    }


def mean_hm(rows: list[dict]) -> float:
    return sum(r["hm_proxy"] for r in rows) / max(len(rows), 1)


def generate_concept(applier: BaseVectorApplier, concept_id: str, eval_data: list[dict]) -> list[dict]:
    applier.hparams_dict["reps"].steer_vector_load_dir = str(
        VECTOR_ROOT / f"steer_eval_concept_{concept_id}" / "reps_vector"
    )
    applier.hparams_dict["reps"].multipliers = [float(applier.config.multipliers[0])]
    applier.apply_vectors()
    results = applier.generate({"steer_eval_eval": eval_data}, save_results=False)
    applier.model.reset_all()
    return results


def sweep(multipliers: list[float], gold_map: dict) -> tuple[dict, dict]:
    loader = DatasetLoader(config_path=str(EASYEDIT_ROOT / "hparams/Steer/dataset_format.yaml"))
    eval_datasets = loader.load_file(dataset_name="SteerEval/personality", split="valid")

    best_by_concept: dict[str, dict] = {}
    all_runs: dict[str, list[dict]] = defaultdict(list)

    for multiplier in multipliers:
        print(f"\n=== multiplier={multiplier} ===")
        cfg = build_cfg(multiplier)
        applier = BaseVectorApplier(cfg)
        applier._load_model()

        for concept_id in L12_CONCEPTS:
            eval_data = eval_datasets[concept_id]
            generated = generate_concept(applier, concept_id, eval_data)
            rows = []
            for item in generated:
                gold = gold_map[(concept_id, item["input"])]
                answer = item["pred"][0] if item.get("pred") else ""
                rows.append(score_item(gold, {"answer": answer}))
            hm = mean_hm(rows)
            zero_fluency = sum(1 for r in rows if r["fluency_score_proxy"] <= 0)
            print(f"  {concept_id}: hm={hm:.3f} fluency_zero={zero_fluency}")
            all_runs[concept_id].append(
                {
                    "multiplier": multiplier,
                    "hm_proxy": hm,
                    "rows": rows,
                    "generated_results": generated,
                }
            )

            prev = best_by_concept.get(concept_id)
            if prev is None or hm > prev["hm_proxy"] or (
                hm == prev["hm_proxy"] and multiplier < prev["multiplier"]
            ):
                best_by_concept[concept_id] = all_runs[concept_id][-1]

        del applier.model
        import torch

        torch.cuda.empty_cache()

    return best_by_concept, all_runs


def merge_submission(best_by_concept: dict[str, dict], base_path: Path, train_path: Path) -> list[dict]:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    train_records = json.loads(train_path.read_text(encoding="utf-8"))
    train_meta = {}
    for rec in train_records:
        cid = rec["concept_id"]
        if cid not in train_meta:
            train_meta[cid] = {
                "concept_name": rec["concept"],
                "concept_description": rec.get("concept_description") or rec.get("llm_description"),
            }

    best_map = {cid: data["generated_results"] for cid, data in best_by_concept.items()}
    merged = []
    for block in base:
        cid = block["concept_id"]
        if cid.startswith("L1_") or cid.startswith("L2_"):
            merged.append(
                {
                    "concept_id": cid,
                    "concept_name": train_meta[cid]["concept_name"],
                    "llm_description": train_meta[cid]["concept_description"],
                    "generation_prompt": None,
                    "generated_results": best_map[cid],
                }
            )
        else:
            merged.append(block)
    return merged


def main() -> None:
    os.chdir(EASYEDIT_ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--base", type=Path, default=BASE_GENERATION)
    parser.add_argument("--train", type=Path, default=PROJECT_ROOT / "train.json")
    parser.add_argument(
        "--multipliers",
        default="0.5,1.0,1.5,2.0,2.5,3.0",
        help="Comma-separated multipliers to sweep",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs/generation/l12_tuned",
    )
    args = parser.parse_args()

    multipliers = [float(x.strip()) for x in args.multipliers.split(",") if x.strip()]
    gold_map = load_gold(args.gold)

    best_by_concept, all_runs = sweep(multipliers, gold_map)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        concept_id: {
            "best_multiplier": data["multiplier"],
            "hm_proxy": data["hm_proxy"],
        }
        for concept_id, data in sorted(best_by_concept.items())
    }
    (args.out_dir / "best_l12_multipliers.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.out_dir / "all_l12_sweep_runs.json").write_text(
        json.dumps(
            {
                cid: [{"multiplier": r["multiplier"], "hm_proxy": r["hm_proxy"]} for r in runs]
                for cid, runs in all_runs.items()
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    merged_raw = merge_submission(best_by_concept, args.base, args.train)
    merged_path = args.out_dir / "all_generation_results_valid.json"
    merged_path.write_text(json.dumps(merged_raw, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Best L1/L2 multipliers ===")
    for cid, info in summary.items():
        print(f"  {cid}: multiplier={info['best_multiplier']} hm={info['hm_proxy']:.3f}")
    print(f"\nWrote {merged_path}")


if __name__ == "__main__":
    main()
