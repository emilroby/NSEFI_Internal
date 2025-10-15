# backend/adapters/__init__.py
from .ctuil import harvest_ctuil_month, CTUIL_SOURCES

__all__ = [
    "harvest_ctuil_month",
    "CTUIL_SOURCES",
    # Add other scrapers/sources here as you build them
]