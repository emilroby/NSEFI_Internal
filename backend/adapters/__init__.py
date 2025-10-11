# backend/adapters/__init__.py
"""
Namespace for data-source adapters.

For this CTUIL-only test build, we re-export the CTUIL adapter so it can be
imported as `from backend.adapters import harvest_ctuil_month, CTUIL_SOURCE`.
When you add more adapters (e.g., CERC, MNRE), import and include them in
__all__ below.
"""

from .ctuil import harvest_ctuil_month, CTUIL_SOURCE

__all__ = [
    "harvest_ctuil_month",
    "CTUIL_SOURCE",
]
