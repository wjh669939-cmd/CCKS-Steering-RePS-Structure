#!/usr/bin/env python3
"""将 EasyEdit all_generation_results_valid.json 转为 CCKS 官方提交格式。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def convert(raw: list[dict]) -> list[dict]:
    out = []
    for block in raw:
        concept_description = block.get("concept_description") or block.get("llm_description")
        generated = []
        for item in block.get("generated_results", []):
            pred = item.get("pred", [])
            if isinstance(pred, str):
                pred = [pred]
            answer = pred[0] if pred else ""
            generated.append(
                {
                    "input": item["input"],
                    "orig_pred": item.get("orig_pred", []),
                    "pred": [answer],
                    "reference_response": item.get("reference_response"),
                    "complete_output": item.get("complete_output") or [answer],
                }
            )
        out.append(
            {
                "concept_id": block["concept_id"],
                "concept_name": block["concept_name"],
                "concept_description": concept_description,
                "generation_prompt": block.get("generation_prompt"),
                "generated_results": generated,
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--in",
        dest="inp",
        default="/root/CCKS2026-Steering/easyedit_reps/outputs/generation/ccks_baseline_reps/reps/all_generation_results_valid.json",
    )
    parser.add_argument(
        "--out",
        default="/root/CCKS2026-Steering/绝地邮兵_result.json",
    )
    args = parser.parse_args()
    raw = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    submission = convert(raw)
    Path(args.out).write_text(json.dumps(submission, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(x["generated_results"]) for x in submission)
    print(f"Wrote {args.out}  concepts={len(submission)} samples={n}")


if __name__ == "__main__":
    main()
