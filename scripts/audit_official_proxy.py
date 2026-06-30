#!/usr/bin/env python3
"""Official-aligned heuristic judge proxy (CS/IS/FS 0-2 + HM) for submission audit.

Not a replacement for LLM judge — uses rules aligned with SteerEval prompt_templates.py
when API_KEY is unavailable. Scale matches competition docs (0-2 per dim, HM aggregate).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "easyedit_reps" / "scripts"))

from l3_keyword_utils import checker_for_concept, score_block

WORD_RE = re.compile(r"[A-Za-z'?]+")
DISC = re.compile(
    r"I(?:'m| am) an AI|As an AI|I don't have (?:a team|personal|emotions|feelings)|"
    r"However, I can help|I cannot (?:feel|experience)",
    re.I,
)


def tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def f1(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    from collections import Counter

    ca, cb = Counter(ta), Counter(tb)
    overlap = sum((ca & cb).values())
    p, r = overlap / len(ta), overlap / len(tb)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def hm_3(a: float, b: float, c: float) -> float:
    if a <= 0 or b <= 0 or c <= 0:
        return 0.0
    return 3.0 / (1.0 / a + 1.0 / b + 1.0 / c)


def is_truncated(text: str) -> bool:
    t = text.rstrip()
    return len(t) > 200 and t[-1] not in ".!?\"'」』）]"


def repetition_bad(text: str) -> bool:
    toks = tokens(text)
    if len(toks) < 12:
        return False
    from collections import Counter

    grams = [tuple(toks[i : i + 4]) for i in range(len(toks) - 3)]
    counts = Counter(grams)
    rep = sum(c - 1 for c in counts.values() if c > 1)
    return rep / max(len(grams), 1) > 0.15


def score_cs(concept_id: str, concept_name: str, answer: str, gold: dict | None) -> float:
    if concept_id.startswith("L3_"):
        check = checker_for_concept(concept_id, concept_name)
        if check(answer):
            # Penalize mechanical tail-insertion (keyword only in last 15% of text)
            lower = answer.lower()
            phrase = concept_name
            m = re.search(r'"([^"]+)"', concept_name)
            key = m.group(1).lower() if m else ""
            if key and lower.rfind(key) > len(lower) * 0.85 and lower.count(key) == 1:
                return 1.0
            return 2.0
        return 0.0
    if gold is None:
        return 1.0
    margin = f1(answer, gold["matching"]) - f1(answer, gold["not_matching"])
    if margin >= 0.25:
        return 2.0
    if margin >= 0.08:
        return 1.0
    return 0.0


def score_is(answer: str, question: str) -> float:
    if not answer.strip():
        return 0.0
    toks = tokens(answer)
    if len(toks) < 6:
        return 0.0
    q_overlap = f1(answer, question)
    if q_overlap < 0.05 and len(toks) < 20:
        return 0.0
    if q_overlap < 0.12 or len(toks) < 12:
        return 1.0
    return 2.0


def score_fs(answer: str) -> float:
    if not answer.strip():
        return 0.0
    if DISC.search(answer):
        return 0.0
    if is_truncated(answer) or repetition_bad(answer):
        return 0.0
    if len(answer) > 900 or answer.count("\n\n") > 8:
        return 1.0
    t = answer.rstrip()
    if len(t) > 150 and t[-1] not in ".!?\"'":
        return 1.0
    return 2.0


def load_gold(path: Path) -> dict[tuple[str, str], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(r["concept_id"], r["question"]): r for r in data}


def audit_submission(submission_path: Path, gold_path: Path, label: str) -> dict:
    sub = json.loads(submission_path.read_text(encoding="utf-8"))
    gold_map = load_gold(gold_path)
    rows = []
    by_concept: dict[str, list] = defaultdict(list)
    by_level: dict[str, list] = defaultdict(list)

    for block in sub:
        cid = block["concept_id"]
        level = cid.split("_")[0]
        cname = block["concept_name"]
        for g in block["generated_results"]:
            q = g["input"]
            ans = (g.get("pred") or [""])[0]
            gold = gold_map.get((cid, q))
            cs = score_cs(cid, cname, ans, gold)
            is_ = score_is(ans, q)
            fs = score_fs(ans)
            hm = hm_3(cs, is_, fs)
            row = {
                "concept_id": cid,
                "input": q[:80],
                "cs": cs,
                "is": is_,
                "fs": fs,
                "hm": hm,
            }
            rows.append(row)
            by_concept[cid].append(row)
            by_level[level].append(row)

    def agg(items: list[dict]) -> dict:
        n = len(items)
        return {
            "n": n,
            "cs": sum(x["cs"] for x in items) / n,
            "is": sum(x["is"] for x in items) / n,
            "fs": sum(x["fs"] for x in items) / n,
            "hm": sum(x["hm"] for x in items) / n,
        }

    report = {
        "label": label,
        "submission": str(submission_path),
        "overall": agg(rows),
        "by_level": {k: agg(v) for k, v in sorted(by_level.items())},
        "by_concept": {k: agg(v) for k, v in sorted(by_concept.items())},
        "weak_samples": sorted(
            [r for r in rows if r["hm"] < 1.0],
            key=lambda x: x["hm"],
        )[:20],
        "rows": rows,
    }
    return report


def print_report(report: dict) -> None:
    o = report["overall"]
    print(f"\n=== Official proxy audit: {report['label']} ===")
    print(f"  Overall (120): CS={o['cs']:.3f} IS={o['is']:.3f} FS={o['fs']:.3f} HM={o['hm']:.3f}")
    for lvl in ["L1", "L2", "L3"]:
        if lvl in report["by_level"]:
            s = report["by_level"][lvl]
            print(
                f"  {lvl} ({s['n']:3d}): CS={s['cs']:.3f} IS={s['is']:.3f} "
                f"FS={s['fs']:.3f} HM={s['hm']:.3f}"
            )
    print("\n  Weakest concepts (by HM):")
    concepts = sorted(report["by_concept"].items(), key=lambda x: x[1]["hm"])[:8]
    for cid, s in concepts:
        print(f"    {cid}: HM={s['hm']:.3f} CS={s['cs']:.3f} IS={s['is']:.3f} FS={s['fs']:.3f}")
    if report["weak_samples"]:
        print(f"\n  Lowest HM samples ({len(report['weak_samples'])} shown):")
        for r in report["weak_samples"][:8]:
            print(
                f"    {r['concept_id']} HM={r['hm']:.2f} "
                f"CS={r['cs']:.0f} IS={r['is']:.0f} FS={r['fs']:.0f} | {r['input']}…"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True)
    parser.add_argument("--gold", type=Path, default=ROOT / "valid.json")
    parser.add_argument("--label", default="submission")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    report = audit_submission(Path(args.submission), args.gold, args.label)
    print_report(report)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # drop full rows in saved json if huge — keep summary + weak
        save = {k: v for k, v in report.items() if k != "rows"}
        save["num_rows"] = len(report["rows"])
        args.out.write_text(json.dumps(save, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
