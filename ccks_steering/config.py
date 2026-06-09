from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: str | Path) -> dict[str, Any]:
    config = read_json(path)
    config["_config_path"] = str(path)
    return config


def resolve_output_dir(config: dict[str, Any]) -> Path:
    out = Path(config.get("output_dir", "runs/baseline_caa"))
    out.mkdir(parents=True, exist_ok=True)
    return out
