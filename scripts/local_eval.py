from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import read_json, write_json


WORD_RE = re.compile(r"[A-Za-z']+")


def tokens(text: str) -> list[str]:
    return [token.lower() for token in WORD_RE.findall(text)]


def f1_overlap(a: str, b: str) -> float:
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return 0.0
    ca = Counter(ta)
    cb = Counter(tb)
    overlap = sum((ca & cb).values())
    precision = overlap / len(ta)
    recall = overlap / len(tb)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def repetition_rate(text: str, n: int = 4) -> float:
    toks = tokens(text)
    if len(toks) < n:
        return 0.0
    grams = [tuple(toks[i : i + n]) for i in range(len(toks) - n + 1)]
    counts = Counter(grams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / max(len(grams), 1)


def clamp_0_4(value: float) -> float:
    return max(0.0, min(4.0, value))


def harmonic_mean(values: list[float]) -> float:
    if any(value <= 0 for value in values):
        return 0.0
    return len(values) / sum(1.0 / value for value in values)


def score_item(gold: dict, pred: dict) -> dict:
    answer = pred.get("answer", "")
    pos_sim = f1_overlap(answer, gold["matching"])
    neg_sim = f1_overlap(answer, gold["not_matching"])
    question_sim = f1_overlap(answer, gold["question"])
    margin = pos_sim - neg_sim

    concept_score = clamp_0_4(2.0 + 8.0 * margin)
    instruction_score = 4.0
    if len(tokens(answer)) < 8:
        instruction_score -= 1.5
    if question_sim > 0.7:
        instruction_score -= 1.0
    if not answer.strip():
        instruction_score = 0.0
    instruction_score = clamp_0_4(instruction_score)

    rep = repetition_rate(answer)
    fluency_score = clamp_0_4(4.0 - 8.0 * rep)
    if len(answer) > 1200:
        fluency_score -= 0.75
    if not answer.strip():
        fluency_score = 0.0
    fluency_score = clamp_0_4(fluency_score)

    hm = harmonic_mean([concept_score, instruction_score, fluency_score])
    return {
        "domain": gold["domain"],
        "concept_id": gold["concept_id"],
        "question_id": gold["question_id"],
        "concept_score_proxy": concept_score,
        "instruction_score_proxy": instruction_score,
        "fluency_score_proxy": fluency_score,
        "hm_proxy": hm,
        "matching_similarity": pos_sim,
        "not_matching_similarity": neg_sim,
        "answer_length": len(answer),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default="valid.json")
    parser.add_argument("--pred", default="runs/baseline_caa/predictions.json")
    parser.add_argument("--out", default="runs/baseline_caa/local_eval.json")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    gold = read_json(args.gold)
    pred = read_json(args.pred)
    pred_map = {(x["domain"], x["concept_id"], x["question_id"]): x for x in pred}
    rows = []
    for item in gold:
        key = (item["domain"], item["concept_id"], item["question_id"])
        if key not in pred_map:
            if args.allow_partial:
                continue
            raise KeyError(f"Missing prediction for {key}")
        rows.append(score_item(item, pred_map[key]))
    if not rows:
        raise ValueError("No overlapping gold/prediction rows found")

    by_concept = defaultdict(list)
    for row in rows:
        by_concept[row["concept_id"]].append(row["hm_proxy"])
    report = {
        "note": "Proxy scores are for local debugging only and are not equivalent to the official LLM judge.",
        "num_items": len(rows),
        "mean_hm_proxy": sum(row["hm_proxy"] for row in rows) / len(rows),
        "by_concept_hm_proxy": {
            concept_id: sum(values) / len(values) for concept_id, values in sorted(by_concept.items())
        },
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
    print(f"mean_hm_proxy={report['mean_hm_proxy']:.4f}")


if __name__ == "__main__":
    main()
