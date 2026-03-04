import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def default_output_path(output_dir: str) -> str:
    date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"runs-{date_stamp}.jsonl"
    return os.path.join(output_dir, filename)


def save_run(
    output_dir: str,
    data: dict[str, Any],
    output_path: Optional[str] = None,
) -> dict[str, str]:
    _ensure_dir(output_dir)
    path = output_path or default_output_path(output_dir)
    run_id = uuid.uuid4().hex
    payload = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return {"path": path, "run_id": run_id}


def save_metrics(
    output_dir: str,
    data: dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    _ensure_dir(output_dir)
    path = output_path or os.path.join(output_dir, "metrics.jsonl")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path
