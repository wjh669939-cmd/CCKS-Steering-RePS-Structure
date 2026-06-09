from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import write_json
from ccks_steering.data import dataset_summary, load_records, validate_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="train.json")
    parser.add_argument("--valid", default="valid.json")
    parser.add_argument("--out", default="runs/data_report.json")
    args = parser.parse_args()

    train = load_records(args.train)
    valid = load_records(args.valid)
    report = {
        "validation": [
            validate_records(train, name="train"),
            validate_records(valid, name="valid"),
        ],
        "summary": [
            dataset_summary(train, name="train"),
            dataset_summary(valid, name="valid"),
        ],
    }
    write_json(args.out, report)
    print(f"Wrote {args.out}")
    for item in report["summary"]:
        print(f"{item['name']}: rows={item['rows']} domains={item['domains']} concepts={item['num_concepts']}")


if __name__ == "__main__":
    main()
