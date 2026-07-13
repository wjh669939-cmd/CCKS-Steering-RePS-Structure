#!/usr/bin/env python3
"""CCKS2026 提交 JSON 内容 + 格式验收。用法: python3 validate_submission.py <path.json>"""
import json
import sys

EXPECTED_CONCEPTS = 24
SAMPLES_PER_CONCEPT = 5


def validate(path: str) -> tuple[list[str], list[str]]:
    d = json.load(open(path, encoding="utf-8"))
    errors, warnings = [], []

    if len(d) != EXPECTED_CONCEPTS:
        errors.append(f"concept 数 {len(d)} != {EXPECTED_CONCEPTS}")

    total = 0
    for block in d:
        cid = block.get("concept_id", "?")
        results = block.get("generated_results", [])
        if len(results) != SAMPLES_PER_CONCEPT:
            errors.append(f"{cid}: 样本数 {len(results)} != {SAMPLES_PER_CONCEPT}")
        for j, r in enumerate(results):
            total += 1
            pred = (r.get("pred") or [""])[0]
            co = (r.get("complete_output") or [""])[0]
            if not pred.strip():
                errors.append(f"{cid} Q{j}: pred 为空")
            if "<|im_start|>" not in co:
                errors.append(f"{cid} Q{j}: complete_output 无 im_start")
            if "issue_comment" in co or "<issue>" in co:
                errors.append(f"{cid} Q{j}: 含 issue 崩坏标记")
            if co.count("<issue>") > 3:
                errors.append(f"{cid} Q{j}: issue token 复读")
            if r.get("input") and r["input"] not in co:
                warnings.append(f"{cid} Q{j}: complete_output 未包含原 question")

    return errors, warnings, total


def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_submission.py <path.json>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    errors, warnings, total = validate(path)
    print(f"文件: {path}")
    print(f"样本: {total}")
    if warnings:
        print("警告:")
        for w in warnings[:10]:
            print(f"  - {w}")
    if errors:
        print("❌ 未通过:")
        for e in errors[:15]:
            print(f"  - {e}")
        sys.exit(1)
    print("✅ 验收通过")


if __name__ == "__main__":
    main()
