from __future__ import annotations
import base64
import os
from pathlib import Path
from typing import Optional

def push_month_to_cloud(local: Path,
                        repo: Optional[str] = None,
                        out_path: Optional[str] = None,
                        branch: Optional[str] = None) -> bool:
    """
    Push a single JSON (month snapshot) to GitHub via REST.
    ENV:
      GITHUB_TOKEN  (required)
      GITHUB_REPO   e.g. emilroby/NSEFI_Internal
      GITHUB_PATH   e.g. nsefi/cerc_YYYY_MM.json  (if omitted, we push with same filename at repo root)
      GITHUB_BRANCH main
    """
    import requests

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return False

    repo = repo or os.getenv("GITHUB_REPO")
    if not repo:
        return False

    branch = branch or os.getenv("GITHUB_BRANCH", "main")
    out_path = out_path or os.getenv("GITHUB_PATH", local.name)

    api = f"https://api.github.com/repos/{repo}/contents/{out_path}"
    content_b64 = base64.b64encode(local.read_bytes()).decode("utf-8")
    msg = f"update {out_path}"

    # Try to read sha (update vs create)
    sha = None
    r0 = requests.get(api, headers={"Authorization": f"token {token}"})
    if r0.status_code == 200 and r0.json().get("sha"):
        sha = r0.json()["sha"]

    body = {"message": msg, "content": content_b64, "branch": branch}
    if sha:
        body["sha"] = sha

    r = requests.put(api, json=body, headers={"Authorization": f"token {token}",
                                              "Accept": "application/vnd.github+json"})
    return r.status_code in (200, 201)
