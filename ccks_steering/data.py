from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import read_json


REQUIRED_FIELDS = {
    "domain",
    "concept_id",
    "concept",
    "question_id",
    "question",
    "matching",
    "not_matching",
}


@dataclass(frozen=True)
class ConceptKey:
    domain: str
    concept_id: str
    concept: str

    @property
    def slug(self) -> str:
        return f"{self.domain}__{self.concept_id}"


def load_records(path: str | Path) -> list[dict]:
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def validate_records(records: Iterable[dict], *, name: str) -> dict:
    records = list(records)
    missing: Counter[str] = Counter()
    empty: Counter[str] = Counter()
    duplicate_ids: Counter[tuple[str, str, int]] = Counter()

    for record in records:
        missing.update(REQUIRED_FIELDS - set(record))
        for field in REQUIRED_FIELDS:
            if field in record and record[field] in ("", None):
                empty[field] += 1
        if {"domain", "concept_id", "question_id"} <= set(record):
            duplicate_ids[(record["domain"], record["concept_id"], record["question_id"])] += 1

    duplicates = {str(key): value for key, value in duplicate_ids.items() if value > 1}
    return {
        "name": name,
        "rows": len(records),
        "missing_fields": dict(missing),
        "empty_fields": dict(empty),
        "duplicate_domain_concept_question_ids": duplicates,
    }


def concept_key(record: dict) -> ConceptKey:
    return ConceptKey(
        domain=str(record["domain"]),
        concept_id=str(record["concept_id"]),
        concept=str(record["concept"]),
    )


def group_by_concept(records: Iterable[dict]) -> dict[ConceptKey, list[dict]]:
    groups: dict[ConceptKey, list[dict]] = defaultdict(list)
    for record in records:
        groups[concept_key(record)].append(record)
    return dict(groups)


def dataset_summary(records: list[dict], *, name: str) -> dict:
    groups = group_by_concept(records)
    domains = Counter(record["domain"] for record in records)
    concept_counts = [
        {
            "domain": key.domain,
            "concept_id": key.concept_id,
            "concept": key.concept,
            "count": len(items),
        }
        for key, items in sorted(groups.items(), key=lambda item: (item[0].domain, item[0].concept_id))
    ]
    return {
        "name": name,
        "rows": len(records),
        "domains": dict(domains),
        "num_concepts": len(groups),
        "concept_counts": concept_counts,
    }
