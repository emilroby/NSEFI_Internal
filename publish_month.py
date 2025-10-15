# publish_month.py (Root Directory)
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the parent directory of backend to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.storage import (
    read_month_snapshot,
    write_month_snapshot,
    ist_now,
    CACHE_DIR
)
from backend.adapters import harvest_ctuil_month

def run_scraper_job():
    # 1. Determine current month
    now = ist_now()
    yyyy, mm = now.year, now.month

    # 2. Read existing cache (if any)
    snap = read_month_snapshot(yyyy, mm) or {}

    # 3. Harvest CTUIL data (the key step)
    print(f"--- Starting CTUIL harvest for {mm:02d}/{yyyy} ---")
    ctuil_items = harvest_ctuil_month(yyyy, mm)
    print(f"--- Completed. Found {len(ctuil_items)} final items. ---")

    # 4. Update the snapshot structure
    snap.setdefault("central", {})["CTUIL"] = ctuil_items

    # 5. Write the updated snapshot back
    write_month_snapshot(yyyy, mm, snap)
    print(f"Successfully updated cache file at: {CACHE_DIR.name}/snapshot_{yyyy:04d}_{mm:02d}.json")

if __name__ == "__main__":
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        run_scraper_job()
    except Exception as e:
        print(f"FATAL ERROR during scheduled job: {e}")
        sys.exit(1)