import hashlib
import json
import os
import time
from typing import Any, Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def make_cache_key(*parts: Optional[str]) -> str:
    safe_parts = [p or "" for p in parts]
    raw = "|".join(safe_parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_cache(cache_dir: str, key: str, ttl_seconds: int) -> Optional[dict[str, Any]]:
    path = os.path.join(cache_dir, f"{key}.json")
    if not os.path.exists(path):
        return None
    if ttl_seconds > 0:
        age_seconds = time.time() - os.path.getmtime(path)
        if age_seconds > ttl_seconds:
            return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_cache(cache_dir: str, key: str, data: dict[str, Any]) -> None:
    _ensure_dir(cache_dir)
    path = os.path.join(cache_dir, f"{key}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
