#!/usr/bin/env python3
"""Check if a concept is allowed in experiment merges."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "baseline/concept_lock.json"


def load_allowed() -> set[str]:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    return {c["concept_id"] for c in data["stubborn_experiment_queue"]["concepts"]}


def load_forbidden() -> dict[str, str]:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for c in data.get("proven_optimized", []):
        out[c["concept_id"]] = "PROVEN — only L2_2 mult sweep allowed"
    for c in data.get("locked_good", []):
        out[c["concept_id"]] = "LOCKED — good enough, do not patch"
    for c in data.get("patch_forbidden", []):
        out[c["concept_id"]] = f"PATCH_FORBIDDEN — official patch failed ({c.get('official_patch_score', '?')})"
    return out


def main() -> None:
    if not LOCK.exists():
        print(f"Missing {LOCK}", file=sys.stderr)
        sys.exit(2)
    concepts = sys.argv[1:]
    if not concepts:
        data = json.loads(LOCK.read_text(encoding="utf-8"))
        print(json.dumps(data["counts"], indent=2))
        print("Usage: check_concept_lock.py L3_3 [L3_5 ...]")
        sys.exit(0)

    allowed = load_allowed()
    forbidden = load_forbidden()
    ok = True
    for cid in concepts:
        if cid in allowed:
            print(f"OK  {cid}: STUBBORN — experiment allowed")
        elif cid in forbidden:
            print(f"NO  {cid}: {forbidden[cid]}", file=sys.stderr)
            ok = False
        else:
            print(f"NO  {cid}: unknown concept", file=sys.stderr)
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
