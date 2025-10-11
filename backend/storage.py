# backend/storage.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

CACHE_DIR = Path("data") / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Stale window: re-fetch if older than 3 hours (your cadence)
STALE_AFTER = timedelta(hours=3)

# ---- time helpers (IST safe) -------------------------------------------------
try:
    # Python 3.9+: zoneinfo
    from zoneinfo import ZoneInfo

    _IST = ZoneInfo("Asia/Kolkata")
except Exception:
    # Fallback: fixed offset
    _IST = timezone(timedelta(hours=5, minutes=30))


def ist_now() -> datetime:
    """Timezone-aware 'now' in IST."""
    return datetime.now(tz=_IST)


def _parse_aware(dt_str: str) -> datetime:
    """Parse ISO 8601 (aware or naive); coerce to aware IST."""
    try:
        dt = datetime.fromisoformat(dt_str)
    except Exception:
        return ist_now()
    if dt.tzinfo is None:
        # treat as IST if stored naive by older builds
        return dt.replace(tzinfo=_IST)
    return dt.astimezone(_IST)


def is_snapshot_stale(last_updated_iso: str) -> bool:
    """Return True if the snapshot is older than our allowed window."""
    dt = _parse_aware(last_updated_iso)
    return (ist_now() - dt) > STALE_AFTER


# ---- file helpers ------------------------------------------------------------
def _month_key(prefix: str, year: int, month: int) -> Path:
    return CACHE_DIR / f"{prefix}_{year:04d}_{month:02d}.json"


def read_month_snapshot(year: int, month: int, prefix: str = "ctuil"):
    """Read snapshot; returns (json_obj, last_updated_iso_str) or None."""
    fp = _month_key(prefix, year, month)
    if not fp.exists():
        return None
    try:
        blob = json.loads(fp.read_text(encoding="utf-8"))
        return blob.get("payload", {}), blob.get("last_updated", "")
    except Exception:
        return None


def write_month_snapshot(
    year: int,
    month: int,
    payload: dict | list,
    prefix: str = "ctuil",
) -> None:
    fp = _month_key(prefix, year, month)
    data = {
        "last_updated": ist_now().isoformat(),
        "payload": payload,
    }
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
