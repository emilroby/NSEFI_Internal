# backend/storage.py
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path("data")
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def ist_now() -> datetime:
    """Returns the current time in Indian Standard Time (IST)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(tz=ist)

def _month_path(year: int, month: int) -> Path:
    """Generates the path for a monthly cache file."""
    return CACHE_DIR / f"snapshot_{year:04d}_{month:02d}.json"

def read_month_snapshot(year: int, month: int) -> Dict[str, Any] | None:
    """Reads a snapshot from the cache."""
    p = _month_path(year, month)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def write_month_snapshot(year: int, month: int, data: Dict[str, Any]) -> None:
    """Writes a snapshot to the cache, marking the timestamp."""
    p = _month_path(year, month)
    data["_written_at_utc"] = datetime.utcnow().isoformat()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")