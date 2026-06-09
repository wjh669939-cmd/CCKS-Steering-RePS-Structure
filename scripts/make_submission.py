from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", default="runs/baseline_caa/predictions.json")
    parser.add_argument("--out-dir", default="runs/baseline_caa/submission")
    args = parser.parse_args()

    predictions = read_json(args.pred)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "domain": item["domain"],
            "concept_id": item["concept_id"],
            "question_id": item["question_id"],
            "answer": item["answer"],
        }
        for item in predictions
    ]

    write_json(out_dir / "submission.json", rows)
    with (out_dir / "submission.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out_dir / "submission.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain", "concept_id", "question_id", "answer"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote submission variants to {out_dir}")


if __name__ == "__main__":
    main()
