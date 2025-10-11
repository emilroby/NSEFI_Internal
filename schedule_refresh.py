# schedule_refresh.py
from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo  # Py 3.9+
except Exception:
    ZoneInfo = None


PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_EXE   = sys.executable                     # venv python
PUBLISH_CMD  = f'"{PYTHON_EXE}" "{PROJECT_ROOT / "publish_month.py"}"'
TASK_NAME    = "NSEFI_CERC_Oct2025_3h"

def local_time_for_midnight_IST() -> str:
    """
    Returns the *local* HH:MM string that corresponds to 00:00 in Asia/Kolkata *today*.
    If that local time is already past for today, it returns tomorrow's equivalent.
    """
    # If zoneinfo is unavailable, fall back to local midnight
    if ZoneInfo is None:
        now_local = datetime.now()
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        if start_local <= now_local:
            start_local += timedelta(days=1)
        return start_local.strftime("%H:%M")

    ist = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ZoneInfo(datetime.now().astimezone().tzinfo.key)) if hasattr(datetime.now().astimezone().tzinfo, "key") else datetime.now()
    # Build today 00:00 IST
    today_ist = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
    # Convert to local wall time
    local = today_ist.astimezone()
    # If already passed, use tomorrow 00:00 IST
    if local <= datetime.now().astimezone():
        local = (today_ist + timedelta(days=1)).astimezone()
    return local.strftime("%H:%M")


def on_windows() -> bool:
    return os.name == "nt"


def ensure_windows_task():
    """
    Creates (or replaces) a Windows Task Scheduler job that:
      - starts at local time equivalent to 00:00 IST
      - repeats every 180 minutes for 24 hours
      - runs with the current user's credentials
    """
    start_time = local_time_for_midnight_IST()  # HH:MM local
    # Build schtasks command
    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", PUBLISH_CMD,
        "/SC", "DAILY",
        "/ST", start_time,
        "/RI", "180",                # Repeat every 180 minutes
        "/DU", "24:00",              # Repeat for 24 hours
        "/F"                         # Force overwrite if exists
    ]
    # Tip: If you need highest privileges, append: ["/RL", "HIGHEST"]
    print("Creating/Updating Task Scheduler job:")
    print(" ", " ".join(cmd))
    subprocess.check_call(cmd)
    print(f"✅ Task '{TASK_NAME}' installed. First run at local {start_time} and then every 3 hours.")


def ensure_cron_job():
    """
    Installs a crontab entry that runs every 3 hours:
      0 */3 * * *  <python> <project>/publish_month.py
    Note: Cron uses system local time. If your host is not set to IST and you
    require exact 00:00 IST alignment, run this on a host set to IST.
    """
    cron_line = f'0 */3 * * * {shutil.which("python3") or shutil.which("python") or PYTHON_EXE} {PROJECT_ROOT / "publish_month.py"} >/dev/null 2>&1'
    print("Ensuring cron entry:", cron_line)
    try:
        # Read existing crontab
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = res.stdout if res.returncode == 0 else ""
    except FileNotFoundError:
        raise RuntimeError("`crontab` not found. Install cron or use another scheduler.")

    if TASK_NAME in existing or cron_line in existing:
        # Replace old lines for idempotency
        new = []
        for ln in existing.splitlines():
            if TASK_NAME in ln or "publish_month.py" in ln:
                continue
            new.append(ln)
        new.append(f"# {TASK_NAME}")
        new.append(cron_line)
        new_text = "\n".join([ln for ln in new if ln.strip()]) + "\n"
    else:
        new_text = existing + ("" if existing.endswith("\n") else "\n")
        new_text += f"# {TASK_NAME}\n{cron_line}\n"

    p = subprocess.run(["crontab", "-"], input=new_text, text=True)
    if p.returncode != 0:
        raise RuntimeError("Failed to write crontab.")
    print("✅ Cron installed/updated. Runs every 3 hours.")


def main():
    if on_windows():
        ensure_windows_task()
    else:
        ensure_cron_job()


if __name__ == "__main__":
    main()
