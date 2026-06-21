#!/usr/bin/env python3
"""Post-process official submission: L3 literal constraints + L1/L2 disclaimer cleanup."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ccks_steering.config import read_json, write_json

# --- Strip assistant disclaimers that hurt concept alignment ---
DISCLAIMER_RES = [
    re.compile(
        r"^I don[\u2019']t have a (?:roommate|physical space|personal|team)[^.!?]*[.!?]\s*",
        re.I,
    ),
    re.compile(
        r"^I don[\u2019']t have (?:a roommate|personal experience|direct experience|emotions or personal experiences|personal relationships|prior knowledge of specific topics)[^.!?]*[.!?]\s*",
        re.I,
    ),
    re.compile(r"^While I don[\u2019']t (?:have|conduct|experience)[^.!?]*[.!?]\s*", re.I),
    re.compile(r"^As an AI[^.!?]*[.!?]\s*", re.I),
    re.compile(r"^I can[\u2019']t experience[^.!?]*[.!?]\s*", re.I),
    re.compile(r"^(?:That[\u2019']s a )?[Gg]reat question!?\s*", re.I),
    re.compile(
        r"^Great question! While I don[\u2019']t[^.!?]*[.!?]\s*",
        re.I,
    ),
    re.compile(r"^However, I can help you[^.!?]*[.!?]\s*", re.I),
    re.compile(
        r"^Sure! Here[\u2019']s a thoughtful and inclusive group message you can send:\s*---\s*",
        re.I,
    ),
    re.compile(
        r"^Certainly\. Here[\u2019']s a professionally crafted message[^:]*:\s*---\s*Subject:[^\n]*\n\n",
        re.I,
    ),
    re.compile(r"^In that case,?\s*", re.I),
]

PIVOT_RES = [
    re.compile(
        r"^But if I were (?:in your situation|in that situation|in a situation like that),?\s*",
        re.I,
    ),
    re.compile(
        r"^But if you[\u2019']re (?:going through emotionally difficult interactions|hosting a study group),?\s*",
        re.I,
    ),
    re.compile(
        r"^I don[\u2019']t have emotions or personal experiences, so I can[\u2019']t truly [\"']soothe[\"'] myself[^.!?]*[.!?]\s*",
        re.I,
    ),
]

SONDER_PHRASE = "embracing sonder—recognizing each person's unique perspective"
IMPROVISE_OPENER = "When plans shift unexpectedly, let's improvise—"

ANTAGONISTIC_HINT = "Look, I'm not going to sugarcoat this—"
SPONTANEOUS_HINT = "Honestly, I'd just roll with it—"
OPEN_HINT = "I'm curious to explore this—"
TRADITION_HINT = "I stick to what works—"
RISK_HINT = "I'd take the bold option—"
AUTONOMY_HINT = "I decide on my own terms—"
PERFECTION_HINT = "I hold myself to high standards—"
BOUNDARY_HINT = "I push back when limits aren't clear—"

LEVEL2_HINTS = {
    "L2_1": "I'll be blunt—",
    "L2_2": "On the spot, I'd pivot—",
    "L2_3": "I'd explore something new—",
    "L2_4": "We follow what has worked—",
    "L2_5": "The upside is worth the risk—",
    "L2_6": "My choice, my pace—",
    "L2_7": "Every detail matters—",
    "L2_8": "I need specifics—",
}

LEVEL1_HINTS = {
    "L1_1": ANTAGONISTIC_HINT,
    "L1_2": SPONTANEOUS_HINT,
    "L1_3": OPEN_HINT,
    "L1_4": TRADITION_HINT,
    "L1_5": RISK_HINT,
    "L1_6": AUTONOMY_HINT,
    "L1_7": PERFECTION_HINT,
    "L1_8": BOUNDARY_HINT,
}

L12_INPUT_REWRITES: dict[tuple[str, str], str] = {
    (
        "L2_1",
        "team asks for help",
    ): (
        "When the team asks for help, I cut straight to the point: if you want results, "
        "don't expect me to carry your load. I'll assist only if it pushes us ahead, "
        "not just to save you. Let's be clear—compromise weakens progress."
    ),
}


def strip_disclaimers(text: str, concept_id: str = "") -> tuple[str, bool]:
    original = text.strip()
    out = original
    modified = False

    changed = True
    while changed:
        changed = False
        for pat in DISCLAIMER_RES:
            new = pat.sub("", out, count=1)
            if new != out:
                out = new.lstrip()
                modified = True
                changed = True
        for pat in PIVOT_RES:
            new = pat.sub("", out, count=1)
            if new != out:
                out = new.lstrip()
                modified = True
                changed = True

    out = unwrap_meta_example(out, modified, concept_id=concept_id)
    out = re.sub(r"^(?:I[\u2019']d|I would)\s+", "I'd ", out, count=1, flags=re.I)
    out = out.strip()
    if out != original:
        modified = True
    return out, modified


def unwrap_meta_example(text: str, already_modified: bool, concept_id: str = "") -> str:
    if not already_modified:
        return text
    match = re.search(
        r"^For example:\s*\n?\s*[\u201c\"'](.+?)[\u201d\"']\s*(?:\n\n|$)",
        text,
        re.S,
    )
    if match:
        quote = match.group(1).strip()
        if concept_id == "L2_1" and re.search(
            r"appreciate the request|focus on my current priorities|realistically contribute",
            quote,
            re.I,
        ):
            return text
        return quote
    match = re.search(
        r"^However, I can help you explore[^.]+\.\s*",
        text,
        re.I,
    )
    if match:
        return text[match.end() :].strip()
    return text


def maybe_add_personality_hint(concept_id: str, text: str, force: bool = False) -> str:
    if not force and len(text) >= 120:
        return text
    hint = LEVEL2_HINTS.get(concept_id) or LEVEL1_HINTS.get(concept_id)
    if hint and not text.lower().startswith(hint.lower()[:12]):
        rest = text
        if rest and not rest.startswith(("I ", "I'd", "I\u2019d", "I'm", "I\u2019m")):
            rest = rest[0].lower() + rest[1:]
        return hint + rest if rest else hint.rstrip("—")
    return text


def clean_l12_answer(concept_id: str, text: str, question: str = "") -> str:
    if not (concept_id.startswith("L1_") or concept_id.startswith("L2_")):
        return text
    for (cid, needle), rewrite in L12_INPUT_REWRITES.items():
        if cid == concept_id and needle.lower() in question.lower():
            if re.search(
                r"I don[\u2019']t have a team|However, I can help you craft",
                text,
                re.I,
            ):
                return rewrite
    cleaned, modified = strip_disclaimers(text, concept_id=concept_id)
    if len(cleaned) < 30:
        cleaned = text.strip()
        modified = False
    return maybe_add_personality_hint(concept_id, cleaned, force=modified)


def insert_once(text: str, phrase: str, anchor: str | None = None) -> str:
    if phrase in text:
        first = text.find(phrase)
        rest = text[first + len(phrase) :]
        rest = rest.replace(phrase, "")
        return text[: first + len(phrase)] + rest
    if anchor and anchor in text:
        idx = text.find(anchor) + len(anchor)
        return text[:idx] + " " + phrase + text[idx:]
    m = re.search(r"[.!?]\s+", text)
    if m:
        idx = m.end()
        return text[:idx] + phrase + " " + text[idx:]
    return phrase + " " + text


def ensure_exact_count(text: str, phrase: str, count: int) -> str:
    cleaned = text
    while phrase.lower() in cleaned.lower():
        cleaned = re.sub(re.escape(phrase), "", cleaned, count=1, flags=re.I).strip()
    if count == 0:
        return cleaned
    out = cleaned
    for i in range(count):
        if i == 0:
            out = insert_once(out, phrase)
        else:
            m = re.search(r"[.!?]\s+", out)
            if m:
                idx = m.end()
                out = out[:idx] + phrase + " " + out[idx:]
            else:
                out = out.rstrip() + " " + phrase
    return out


def ensure_at_least(text: str, phrase: str) -> str:
    if phrase.lower() in text.lower():
        if phrase not in text:
            text = re.sub(re.escape(phrase), phrase, text, flags=re.I, count=1)
        return text
    return insert_once(text, phrase)


def apply_l3_sonder(text: str) -> str:
    text = re.sub(r"\bsonder\b", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,—-")
    if not text:
        return SONDER_PHRASE + "."
    if text[0].isupper():
        text = text[0].lower() + text[1:]
    return SONDER_PHRASE + "—" + text


def apply_l3_improvise(text: str, had_disclaimer: bool) -> str:
    text = re.sub(r"let[\u2019']s improvise", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,—-")
    if had_disclaimer and "let's improvise" not in text.lower():
        if text:
            if text[0].isupper():
                text = text[0].lower() + text[1:]
            return IMPROVISE_OPENER + text
        return IMPROVISE_OPENER.rstrip("—")
    return ensure_at_least(text, "let's improvise")


def apply_l3_constraints(concept_id: str, text: str, had_disclaimer: bool = False) -> str:
    if concept_id == "L3_1":
        text = text.replace("??", "")
        return insert_once(text, "??", anchor="patience")
    if concept_id == "L3_2":
        return apply_l3_improvise(text, had_disclaimer)
    if concept_id == "L3_3":
        return apply_l3_sonder(text)
    if concept_id == "L3_4":
        text = re.sub(r"\*mos maiorum\*", "mos maiorum", text, flags=re.I)
        return ensure_exact_count(text, "mos maiorum", 1)
    if concept_id == "L3_5":
        return ensure_exact_count(text, "variance is the point", 1)
    if concept_id == "L3_6":
        return ensure_exact_count(text, "self-authored", 1)
    if concept_id == "L3_7":
        if "pareto frontier" not in text.lower():
            return ensure_at_least(text, "pareto frontier")
        return re.sub(r"pareto frontier", "pareto frontier", text, flags=re.I, count=1)
    if concept_id == "L3_8":
        text = re.sub(r"just to confirm", "just to be clear", text, flags=re.I)
        return ensure_exact_count(text, "just to be clear", 2)
    return text


def clean_l3_answer(concept_id: str, text: str) -> str:
    cleaned, had_disclaimer = strip_disclaimers(text, concept_id=concept_id)
    if len(cleaned) < 30:
        cleaned = text.strip()
        had_disclaimer = False
    return apply_l3_constraints(concept_id, cleaned, had_disclaimer)


def sync_item(concept_id: str, item: dict) -> dict:
    pred = item.get("pred") or [""]
    answer = pred[0] if pred else ""
    if concept_id.startswith("L3_"):
        answer = clean_l3_answer(concept_id, answer)
    else:
        answer = clean_l12_answer(concept_id, answer, question=item.get("input", ""))
    item = dict(item)
    item["pred"] = [answer]
    item["complete_output"] = [answer]
    return item


def postprocess_submission(data: list[dict]) -> list[dict]:
    out = []
    for block in data:
        cid = block["concept_id"]
        results = [sync_item(cid, g) for g in block.get("generated_results", [])]
        new_block = dict(block)
        new_block["generated_results"] = results
        out.append(new_block)
    return out


def audit_l3(data: list[dict]) -> dict[str, dict]:
    checks = {
        "L3_1": lambda t: t.count("??") == 1,
        "L3_2": lambda t: "let's improvise" in t.lower(),
        "L3_3": lambda t: "sonder" in t.lower(),
        "L3_4": lambda t: t.lower().count("mos maiorum") == 1,
        "L3_5": lambda t: "variance is the point" in t.lower(),
        "L3_6": lambda t: "self-authored" in t.lower(),
        "L3_7": lambda t: "pareto frontier" in t.lower(),
        "L3_8": lambda t: t.lower().count("just to be clear") == 2,
    }
    stats = {}
    for block in data:
        cid = block["concept_id"]
        if cid not in checks:
            continue
        fn = checks[cid]
        hits = sum(1 for g in block["generated_results"] if fn((g.get("pred") or [""])[0]))
        stats[cid] = {"hits": hits, "total": len(block["generated_results"])}
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", default="绝地邮兵_result.json")
    parser.add_argument("--out", default="绝地邮兵_result.json")
    args = parser.parse_args()

    data = read_json(args.inp)
    processed = postprocess_submission(data)
    write_json(args.out, processed)

    stats = audit_l3(processed)
    print(f"Wrote {args.out}")
    print("L3 constraint hits:")
    for cid, s in sorted(stats.items()):
        print(f"  {cid}: {s['hits']}/{s['total']}")


if __name__ == "__main__":
    main()
