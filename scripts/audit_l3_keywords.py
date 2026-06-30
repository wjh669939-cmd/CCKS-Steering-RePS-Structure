#!/usr/bin/env python3
"""Audit L3 literal keyword hit rates in a submission file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "easyedit_reps" / "scripts"))

from l3_keyword_utils import score_block


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True)
    parser.add_argument("--label", default="submission")
    args = parser.parse_args()

    data = __import__("json").loads(Path(args.submission).read_text(encoding="utf-8"))
    blocks = {b["concept_id"]: b for b in data}
    total_hits = total_q = 0
    print(f"\n=== L3 keyword audit: {args.label} ===")
    for i in range(1, 9):
        cid = f"L3_{i}"
        block = blocks[cid]
        kw = score_block(cid, block["concept_name"], block)
        total_hits += kw["keyword_hits"]
        total_q += kw["keyword_total"]
        print(f"  {cid}: {kw['keyword_hits']}/{kw['keyword_total']}  ({block['concept_name'][:50]}…)")
    print(f"  TOTAL: {total_hits}/{total_q}")


if __name__ == "__main__":
    main()
