from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ccks_steering.config import read_json, write_json
from local_eval import score_item


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def prediction_map(records: list[dict]) -> dict[tuple[str, str, int], dict]:
    return {(item["domain"], item["concept_id"], int(item["question_id"])): item for item in records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default="valid.json")
    parser.add_argument("--baseline", required=True, help="No-steering predictions JSON")
    parser.add_argument("--candidate", required=True, help="Steered predictions JSON")
    parser.add_argument("--out", default="runs/compare_no_steering_vs_caa.json")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    gold = read_json(args.gold)
    baseline = prediction_map(read_json(args.baseline))
    candidate = prediction_map(read_json(args.candidate))

    rows = []
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for item in gold:
        key = (item["domain"], item["concept_id"], int(item["question_id"]))
        if key not in baseline:
            if args.allow_partial:
                continue
            raise KeyError(f"Missing baseline prediction for {key}")
        if key not in candidate:
            if args.allow_partial:
                continue
            raise KeyError(f"Missing candidate prediction for {key}")

        baseline_score = score_item(item, baseline[key])
        candidate_score = score_item(item, candidate[key])
        row = {
            "domain": item["domain"],
            "concept_id": item["concept_id"],
            "question_id": item["question_id"],
            "baseline_hm_proxy": baseline_score["hm_proxy"],
            "candidate_hm_proxy": candidate_score["hm_proxy"],
            "delta_hm_proxy": candidate_score["hm_proxy"] - baseline_score["hm_proxy"],
            "baseline_concept_score_proxy": baseline_score["concept_score_proxy"],
            "candidate_concept_score_proxy": candidate_score["concept_score_proxy"],
            "delta_concept_score_proxy": candidate_score["concept_score_proxy"]
            - baseline_score["concept_score_proxy"],
            "baseline_instruction_score_proxy": baseline_score["instruction_score_proxy"],
            "candidate_instruction_score_proxy": candidate_score["instruction_score_proxy"],
            "baseline_fluency_score_proxy": baseline_score["fluency_score_proxy"],
            "candidate_fluency_score_proxy": candidate_score["fluency_score_proxy"],
        }
        rows.append(row)
        by_concept[item["concept_id"]].append(row)

    if not rows:
        raise ValueError("No overlapping gold/baseline/candidate rows found")

    concept_rows = []
    for concept_id, concept_items in sorted(by_concept.items()):
        concept_rows.append(
            {
                "concept_id": concept_id,
                "items": len(concept_items),
                "baseline_hm_proxy": mean([item["baseline_hm_proxy"] for item in concept_items]),
                "candidate_hm_proxy": mean([item["candidate_hm_proxy"] for item in concept_items]),
                "delta_hm_proxy": mean([item["delta_hm_proxy"] for item in concept_items]),
                "delta_concept_score_proxy": mean(
                    [item["delta_concept_score_proxy"] for item in concept_items]
                ),
            }
        )

    report = {
        "note": "Proxy scores are for local debugging only and are not equivalent to the official LLM judge.",
        "gold": args.gold,
        "baseline": args.baseline,
        "candidate": args.candidate,
        "num_items": len(rows),
        "baseline_mean_hm_proxy": mean([row["baseline_hm_proxy"] for row in rows]),
        "candidate_mean_hm_proxy": mean([row["candidate_hm_proxy"] for row in rows]),
        "delta_mean_hm_proxy": mean([row["delta_hm_proxy"] for row in rows]),
        "by_concept": concept_rows,
        "items": rows,
    }
    write_json(args.out, report)

    csv_path = Path(args.out).with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {args.out}")
    print(f"Wrote {csv_path}")
    print(f"delta_mean_hm_proxy={report['delta_mean_hm_proxy']:.4f}")


if __name__ == "__main__":
    main()
