from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Iterable, Tuple, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# PDF parsing is optional but used for hearing schedule
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# ---- sources you asked us to comb
CERC_BASE = "https://cercind.gov.in/"
CERC_SOURCES = {
    "whats_new": urljoin(CERC_BASE, "viewall.html"),
    "notices": urljoin(CERC_BASE, "notice-letter.html"),
    "discussion": urljoin(CERC_BASE, "Disc_Paper.html"),
    "working": urljoin(CERC_BASE, "Work_Paper.html"),
    "draft_reg": urljoin(CERC_BASE, "Draft_reg.html"),
    "current_reg": urljoin(CERC_BASE, "Current_reg.html"),
    "repealed_reg": urljoin(CERC_BASE, "Repeal_reg.html"),
    "orders": urljoin(CERC_BASE, "recent_orders.html"),
    "rops": urljoin(CERC_BASE, "recent_rops.html"),
}

# simple relevance pre-filter to keep NSEFI topics
RELEVANCE = re.compile(
    r"\b(solar|wind|renewable|RE|open\s*access|OA|IST[st]|DSM|GNA|REC|hydrogen|battery|storage|grid|transmission|CTU|trading\s+license|banking|wheeling|tariff)\b",
    re.I,
)

DATE_PAT = re.compile(r"(?P<d>\d{1,2})[./-](?P<m>\d{1,2})[./-](?P<y>\d{2,4})")

def _req(url: str) -> BeautifulSoup:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def _norm_date(text: str, fallback: str) -> str:
    """
    Pick first d.m.y or d/m/y in text; fallback is ISO (YYYY-MM-DD)
    """
    m = DATE_PAT.search(text or "")
    if not m:
        return fallback
    d = int(m.group("d")); m_ = int(m.group("m")); y = int(m.group("y"))
    if y < 100:
        y = 2000 + y
    try:
        return datetime(y, m_, d).strftime("%Y-%m-%d")
    except Exception:
        return fallback

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _doc_link(a) -> Tuple[str, str]:
    """Return (title, href) attempting to link to the actual document/PDF if present."""
    title = _clean(a.get_text(" "))
    href = a.get("href") or ""
    href = urljoin(CERC_BASE, href)
    return title, href

def _collect_listpage(url: str, year: int, month: int, tag_selector: str = "a") -> List[Dict]:
    """Generic: scan anchors; extract title & url; guess date from nearby text or filename."""
    soup = _req(url)
    items: List[Dict] = []

    # Look inside main content; CERC pages are simple tables/lists of <a> + trailing text
    for a in soup.select(tag_selector):
        title, href = _doc_link(a)
        if not title or not href:
            continue
        # must look relevant for NSEFI
        if not RELEVANCE.search(title):
            continue

        # date from sibling/parent text, else from href/filename
        context = _clean((a.find_parent().get_text(" ") if a.find_parent() else "") or "")
        date_iso = _norm_date(context + " " + href, f"{year:04d}-{month:02d}-01")

        # only keep for the requested month/year
        try:
            dt = datetime.fromisoformat(date_iso)
            if not (dt.year == year and dt.month == month):
                continue
        except Exception:
            pass

        items.append({
            "type": "Orders" if "order" in url.lower() else
                    "ROP" if "rop" in url.lower() else
                    "Draft Regulation" if "draft" in url.lower() else
                    "Regulation",
            "title": title,
            "date": date_iso,
            "url": href,
        })
    return items

def _dedupe(items: Iterable[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for it in items:
        key = (it.get("title", "").lower(), it.get("date", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    # newest first
    return sorted(out, key=lambda x: x.get("date", ""), reverse=True)

def _parse_hearing_pdf(pdf_url: str, year: int, month: int) -> List[Dict]:
    if not pdfplumber:
        return []
    try:
        r = requests.get(pdf_url, timeout=40)
        r.raise_for_status()
    except Exception:
        return []
    items: List[Dict] = []
    with pdfplumber.open(BytesIO(r.content)) as pdf:  # type: ignore[name-defined]
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                # expect "08.10.2025 ..." at line start sometimes
                m = DATE_PAT.match(line.strip())
                if not m:
                    continue
                d = int(m.group("d")); m_ = int(m.group("m")); y = int(m.group("y"))
                if y < 100: y = 2000 + y
                if y != year or m_ != month:
                    continue
                # rest of line is subject; filter for NSEFI topics
                subject = _clean(line[m.end():])
                if not RELEVANCE.search(subject):
                    continue
                items.append({
                    "type": "Schedule of Hearing",
                    "title": subject,
                    "date": f"{y:04d}-{m_:02d}-{d:02d}",
                    "url": pdf_url,
                })
    return items

# pdf utils (import BytesIO locally to avoid global import on machines without pdf)
from io import BytesIO  # after function def

def harvest_cerc_month(year: int, month: int, hearing_pdf_url: Optional[str] = None
                      ) -> Tuple[Dict[str, List[Dict]], Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """
    Build three maps (central_map, state_map, ut_map). For now we only fill CERC in central_map, as requested.
    """
    central_map: Dict[str, List[Dict]] = {"CERC": []}
    state_map: Dict[str, List[Dict]] = {}
    ut_map: Dict[str, List[Dict]] = {}

    all_items: List[Dict] = []
    # comb through the CERC pages you listed
    for key, url in CERC_SOURCES.items():
        try:
            all_items.extend(_collect_listpage(url, year, month))
        except Exception:
            continue

    # hearing schedule (PDF table)
    if hearing_pdf_url:
        try:
            all_items.extend(_parse_hearing_pdf(hearing_pdf_url, year, month))
        except Exception:
            pass

    central_map["CERC"] = _dedupe(all_items)
    return central_map, state_map, ut_map
