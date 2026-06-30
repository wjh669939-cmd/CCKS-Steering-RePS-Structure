#!/usr/bin/env python3
"""Baseline-Anchored Best-of-N: multi-candidate steer + pick only if beats baseline."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
EASYEDIT_ROOT = ROOT / "EasyEdit"
sys.path.insert(0, str(EASYEDIT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit_official_proxy import hm_3, load_gold, score_cs, score_is, score_fs
from l3_keyword_utils import checker_for_concept
from regen_mixed_layers import load_layer_map, vector_root_for
from regen_tuned_all import build_cfg, load_multipliers, to_submission_block, train_meta
from steer.datasets.dataset_loader import DatasetLoader
from steer.vector_appliers.vector_applier import BaseVectorApplier
from scripts.local_eval import f1_overlap, repetition_rate

DISCLAIMER = re.compile(
    r"I(?:'m| am) an AI|I don't have (?:a team|personal|emotions|feelings)|"
    r"However, I can help|As an AI|I cannot (?:feel|experience)",
    re.I,
)
WORD_RE = re.compile(r"[A-Za-z'?]+")


def is_truncated(text: str) -> bool:
    t = text.rstrip()
    return len(t) > 200 and t[-1] not in '.!?"\'」』）]'


def question_keywords(question: str) -> set[str]:
    stop = {
        "the", "a", "an", "to", "and", "or", "of", "in", "on", "for", "with",
        "how", "what", "when", "where", "why", "who", "do", "you", "your",
        "is", "are", "can", "would", "could", "should", "that", "this",
    }
    toks = {t.lower() for t in WORD_RE.findall(question)}
    return {t for t in toks if len(t) > 3 and t not in stop}


def question_coverage(answer: str, question: str) -> float:
    qk = question_keywords(question)
    if not qk:
        return 1.0
    ak = {t.lower() for t in WORD_RE.findall(answer)}
    return len(qk & ak) / len(qk)


def train_refs(train_path: Path) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"matching": [], "not_matching": []})
    for row in json.loads(train_path.read_text(encoding="utf-8")):
        cid = row["concept_id"]
        out[cid]["matching"].append(row["matching"])
        out[cid]["not_matching"].append(row["not_matching"])
    return dict(out)


def matching_margin(text: str, matchings: list[str], not_matchings: list[str]) -> float:
    if not text.strip():
        return -1.0
    pos = max(f1_overlap(text, m) for m in matchings)
    neg = max(f1_overlap(text, n) for n in not_matchings)
    return pos - neg


def length_penalty(text: str, baseline_len: int) -> int:
    if baseline_len <= 0:
        return 0
    ratio = len(text) / baseline_len
    if ratio < 0.75:
        return 2
    if ratio < 0.85:
        return 1
    if ratio > 1.25:
        return 1
    return 0


def concept_type(concept_id: str, lock_path: Path) -> str:
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    for c in data["stubborn_experiment_queue"]["concepts"]:
        if c["concept_id"] == concept_id:
            return c.get("type", "unknown")
    return "unknown"


def rank_tuple(
    text: str,
    *,
    concept_id: str,
    concept_name: str,
    question: str,
    baseline_text: str,
    matchings: list[str],
    not_matchings: list[str],
    gold: dict | None,
    ctype: str,
) -> tuple:
    """Higher is better."""
    if not text.strip():
        return (-999, 0, 0, 0, 0, 0, 0)

    kw_hit = 1 if concept_id.startswith("L3_") and checker_for_concept(concept_id, concept_name)(text) else 0
    disc = 1 if DISCLAIMER.search(text) else 0
    trunc = 1 if is_truncated(text) else 0
    rep = repetition_rate(text)
    margin = matching_margin(text, matchings, not_matchings)
    qcov = question_coverage(text, question)
    len_pen = length_penalty(text, len(baseline_text))

    cs = score_cs(concept_id, concept_name, text, gold)
    is_ = score_is(text, question)
    fs = score_fs(text)
    hm = hm_3(cs, is_, fs)

    if ctype.startswith("keyword"):
        # Hard: must contain keyword to beat baseline; else heavily penalize
        if not kw_hit:
            return (-50, 0, 0, 0, 0, 0, 0)
        return (kw_hit, hm, cs, is_, fs, qcov, -disc, -trunc, -rep, -len_pen)

    if ctype == "personality_weak":
        return (hm, margin, -len_pen, -disc, -trunc, -rep, qcov)

    if ctype == "antagonistic":
        return (margin, hm, cs, -disc, -trunc, -rep)

    # default
    return (hm, margin, kw_hit, -disc, -trunc, -rep, -len_pen)


def generate_one(
    concept_id: str,
    layer: int,
    multiplier: float,
    max_new_tokens: int,
    tag: str,
    eval_data: list,
    vector_root: Path,
    *,
    temperature: float = 0.0,
    do_sample: bool = False,
    num_responses: int = 1,
) -> list[list[str]]:
    cfg = build_cfg(multiplier, max_new_tokens, tag, layer, vector_root)
    cfg.num_responses = num_responses
    cfg.generation_params = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "do_sample": do_sample,
    }
    applier = BaseVectorApplier(cfg)
    applier._load_model()
    applier.hparams_dict["reps"].steer_vector_load_dir = str(
        vector_root / f"steer_eval_concept_{concept_id}" / "reps_vector"
    )
    applier.hparams_dict["reps"].multipliers = [multiplier]
    applier.apply_vectors()
    generated = applier.generate({"steer_eval_eval": eval_data}, save_results=False)
    applier.model.reset_all()
    del applier.model
    import torch

    torch.cuda.empty_cache()
    return [item.get("pred") or [""] for item in generated]


def mult_grid(base: float) -> list[float]:
    cands = sorted({round(x, 1) for x in (base - 1.0, base - 0.5, base, base + 0.5, base + 1.0, base + 1.5) if 1.5 <= x <= 6.0})
    return cands or [base]


def main() -> None:
    os.chdir(EASYEDIT_ROOT)
    parser = argparse.ArgumentParser(description="BA-BoN for one STUBBORN concept")
    parser.add_argument("--concept", required=True)
    parser.add_argument("--baseline", type=Path, default=PROJECT_ROOT / "baseline/submission.json")
    parser.add_argument("--layers-json", type=Path, default=PROJECT_ROOT / "baseline/layers.json")
    parser.add_argument("--multipliers", type=Path, default=PROJECT_ROOT / "baseline/multipliers.json")
    parser.add_argument("--per-layer-base", type=Path, default=ROOT / "outputs/vectors/per_layer")
    parser.add_argument("--train", type=Path, default=PROJECT_ROOT / "train.json")
    parser.add_argument("--gold", type=Path, default=PROJECT_ROOT / "valid.json")
    parser.add_argument("--lock", type=Path, default=PROJECT_ROOT / "baseline/concept_lock.json")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--num-samples", type=int, default=3, help="stochastic samples per question at base mult")
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--tag", default="ba_bon")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--out-export", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="score only using precomputed sweep if present")
    args = parser.parse_args()

    cid = args.concept
    allowed = {c["concept_id"] for c in json.loads(args.lock.read_text())["stubborn_experiment_queue"]["concepts"]}
    if cid not in allowed:
        raise SystemExit(f"{cid} not in STUBBORN queue — see baseline/concept_lock.json")

    layer_map = load_layer_map(args.layers_json)
    mults_map = load_multipliers(args.multipliers)
    meta = train_meta(args.train)
    refs = train_refs(args.train)
    gold_map = load_gold(args.gold)
    ctype = concept_type(cid, args.lock)

    base_sub = json.loads(args.baseline.read_text(encoding="utf-8"))
    base_block = next(b for b in base_sub if b["concept_id"] == cid)
    concept_name = base_block["concept_name"]

    layer = layer_map[cid]
    base_mult = mults_map[cid]
    vroot = vector_root_for(cid, layer, args.per_layer_base)

    out_dir = args.out_dir or (PROJECT_ROOT / f"runs/ba_bon_{cid.lower()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    loader = DatasetLoader(config_path=str(EASYEDIT_ROOT / "hparams/Steer/dataset_format.yaml"))
    eval_data = loader.load_file("SteerEval/personality", "valid")[cid]

    print(f"=== BA-BoN {cid} ({ctype}) L{layer} base_m={base_mult} ===")

    # Collect deterministic candidates per mult (batch generate per mult)
    mults = mult_grid(base_mult)
    cand_by_q: list[list[tuple[str, str]]] = [[] for _ in range(len(eval_data))]

    for m in mults:
        print(f"  generate m={m} (deterministic)...")
        preds = generate_one(
            cid, layer, m, args.max_new_tokens, f"{args.tag}_m{m}",
            eval_data, vroot, temperature=0.0, do_sample=False, num_responses=1,
        )
        for i, pred_list in enumerate(preds):
            for ans in pred_list:
                if ans:
                    cand_by_q[i].append((ans, f"m={m}"))

    if args.num_samples > 0:
        print(f"  generate base_m={base_mult} x{args.num_samples} @ temp={args.temperature}...")
        preds = generate_one(
            cid, layer, base_mult, args.max_new_tokens, f"{args.tag}_sample",
            eval_data, vroot,
            temperature=args.temperature, do_sample=True, num_responses=args.num_samples,
        )
        for i, pred_list in enumerate(preds):
            for j, ans in enumerate(pred_list):
                if ans:
                    cand_by_q[i].append((ans, f"sample{j}@m={base_mult}"))

    picked_rows = []
    log_rows = []
    changed = 0
    kw_before = kw_after = 0
    checker = checker_for_concept(cid, concept_name) if cid.startswith("L3_") else None

    for i, (item, base_row) in enumerate(zip(eval_data, base_block["generated_results"])):
        baseline_ans = base_row["pred"][0]
        question = item["input"]
        gold = gold_map.get((cid, question))
        if checker:
            kw_before += int(checker(baseline_ans))

        pool: list[tuple[str, str]] = [(baseline_ans, "baseline")]
        seen = {baseline_ans}
        for ans, src in cand_by_q[i]:
            if ans not in seen:
                pool.append((ans, src))
                seen.add(ans)

        scored = []
        base_rank = rank_tuple(
            baseline_ans,
            concept_id=cid,
            concept_name=concept_name,
            question=question,
            baseline_text=baseline_ans,
            matchings=refs[cid]["matching"],
            not_matchings=refs[cid]["not_matching"],
            gold=gold,
            ctype=ctype,
        )
        for ans, src in pool:
            r = rank_tuple(
                ans,
                concept_id=cid,
                concept_name=concept_name,
                question=question,
                baseline_text=baseline_ans,
                matchings=refs[cid]["matching"],
                not_matchings=refs[cid]["not_matching"],
                gold=gold,
                ctype=ctype,
            )
            scored.append((r, ans, src))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_rank, best_ans, best_src = scored[0]

        # Anchor: only replace if strictly beats baseline rank
        if best_ans != baseline_ans and best_rank > base_rank:
            final = best_ans
            changed += 1
        else:
            final = baseline_ans
            best_src = "baseline_kept"

        if checker:
            kw_after += int(checker(final))

        picked_rows.append({
            "input": question,
            "orig_pred": [],
            "pred": [final],
            "reference_response": item.get("reference_response"),
            "complete_output": [final],
        })

        log_rows.append({
            "q": i + 1,
            "question": question[:100],
            "baseline_len": len(baseline_ans),
            "picked_src": best_src,
            "changed": final != baseline_ans,
            "baseline_kw": bool(checker(baseline_ans)) if checker else None,
            "final_kw": bool(checker(final)) if checker else None,
            "pool_size": len(pool),
            "top3": [
                {"src": src, "rank": list(rank), "len": len(ans), "preview": ans[:120]}
                for rank, ans, src in scored[:3]
            ],
        })

        print(f"\nQ{i+1} {'CHANGED' if final != baseline_ans else 'KEEP'} src={best_src} ({len(baseline_ans)}c->{len(final)}c)")
        if final != baseline_ans:
            print(f"  > {final[:220]}{'...' if len(final) > 220 else ''}")

    block = to_submission_block(cid, picked_rows, meta)
    patch_path = out_dir / f"{cid}_ba_bon.json"
    patch_path.write_text(json.dumps(block, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "concept_id": cid,
        "type": ctype,
        "layer": layer,
        "base_mult": base_mult,
        "mults_tried": mults,
        "changed": changed,
        "l3_keyword_before": f"{kw_before}/5" if checker else None,
        "l3_keyword_after": f"{kw_after}/5" if checker else None,
        "questions": log_rows,
    }
    (out_dir / f"{cid}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    out_export = args.out_export or (PROJECT_ROOT / f"绝地邮兵_result_ba_bon_{cid}.json")
    patch_map = {cid: block}
    merged = [patch_map.get(b["concept_id"], b) for b in base_sub]

    out_export.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== {cid}: changed {changed}/5 | kw {summary.get('l3_keyword_before')} -> {summary.get('l3_keyword_after')} ===")
    print(f"Patch: {patch_path}")
    print(f"Submit candidate: {out_export}")


if __name__ == "__main__":
    main()
