from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import read_json, write_json
from ccks_steering.data import load_records


def build_official_submission(predictions: list[dict], valid_records: list[dict]) -> list[dict]:
    pred_map = {(item["concept_id"], item["question_id"]): item for item in predictions}

    groups: OrderedDict[str, dict] = OrderedDict()
    for record in valid_records:
        concept_id = record["concept_id"]
        if concept_id not in groups:
            groups[concept_id] = {
                "concept_id": concept_id,
                "concept_name": record["concept"],
                "concept_description": record["concept_description"],
                "generation_prompt": None,
                "generated_results": [],
            }

        key = (concept_id, record["question_id"])
        if key not in pred_map:
            raise KeyError(f"Missing prediction for concept_id={concept_id}, question_id={record['question_id']}")
        pred = pred_map[key]
        if pred["question"] != record["question"]:
            raise ValueError(
                f"Question mismatch for {key}: "
                f"pred={pred['question']!r} valid={record['question']!r}"
            )

        answer = pred["answer"]
        groups[concept_id]["generated_results"].append(
            {
                "input": record["question"],
                "orig_pred": [],
                "pred": [answer],
                "reference_response": None,
                "complete_output": [answer],
            }
        )

    return list(groups.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert predictions.json to official nested submission JSON.")
    parser.add_argument("--pred", default="runs/baseline_caa/predictions.json")
    parser.add_argument("--gold", default="valid.json")
    parser.add_argument("--out", default="绝地邮兵_result(MD).json")
    args = parser.parse_args()

    predictions = read_json(args.pred)
    valid_records = load_records(args.gold)
    submission = build_official_submission(predictions, valid_records)

    out_path = Path(args.out)
    write_json(out_path, submission)

    num_results = sum(len(group["generated_results"]) for group in submission)
    print(f"Wrote {out_path}")
    print(f"concepts={len(submission)} generated_results={num_results}")


if __name__ == "__main__":
    main()
