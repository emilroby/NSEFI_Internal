# backend/__init__.py
"""
Export storage helpers and the CTUIL adapter (CTUIL-only test build).
"""

from .storage import (
    ist_now,
    is_snapshot_stale,
    read_month_snapshot,
    write_month_snapshot,
)

from .adapters.ctuil import harvest_ctuil_month, CTUIL_SOURCE

__all__ = [
    # storage
    "ist_now",
    "is_snapshot_stale",
    "read_month_snapshot",
    "write_month_snapshot",
    # ctuil
    "harvest_ctuil_month",
    "CTUIL_SOURCE",
]
