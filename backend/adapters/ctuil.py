# backend/adapters/ctuil.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CTUIL_NEWS_URL = "https://ctuil.in/latestnews"
CTUIL_SOURCE = "CTUIL"

# Robust month map (short and long)
_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_date_cleaner = re.compile(r"\s+")


@dataclass
class UpdateItem:
    date: str    # YYYY-MM-DD
    title: str
    url: str
    type: str = "Update"   # keep the same shape as your other sources
    source: str = CTUIL_SOURCE


def _mk_abs(href: str) -> str:
    if not href:
        return CTUIL_NEWS_URL
    return urljoin(CTUIL_NEWS_URL, href)


def _coerce_date(day_text: str, mon_text: str, year: int) -> str | None:
    day_text = day_text.strip()
    mon_text = mon_text.strip().lower()
    try:
        d = int(re.sub(r"[^\d]", "", day_text) or "1")
        m = _MONTHS.get(mon_text[:3], None)
        if m is None:
            # try exact (e.g., 'sept')
            m = _MONTHS.get(mon_text, None)
        if not m:
            return None
        dt = datetime(year, m, d)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _extract_items(html: str, year: int, month: int) -> List[UpdateItem]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[UpdateItem] = []

    # The CTUIL "WHAT's NEW" widget is a list with date badges and anchor titles.
    # We'll try a few common patterns – and fall back to anchors if needed.

    # 1) Look for obvious repeated rows
    rows = []

    # Pattern A: <div class="views-row">...</div>
    rows.extend(soup.select("div.views-row"))

    # Pattern B: list items inside a widget region
    if not rows:
        rows.extend(soup.select("ul li"))

    # Pattern C: generic cards in the main container
    if not rows:
        rows.extend(soup.select("div.card, div.row, li"))

    for r in rows:
        # try to find date day/month like the site badges
        # common patterns:
        #  <div class="date"> <span class="day">10</span> <span class="mon">Oct</span> </div>
        day_el = r.select_one(".day, .date .day, .dateday, .date-day")
        mon_el = r.select_one(".mon, .date .mon, .datemon, .date-mon, .month, .date-month")
        title_a = r.select_one("a")

        if not title_a:
            # sometimes text-only
            title_el = r.select_one("h3, h4, .title")
            if title_el:
                # create a dummy anchor to the news page
                class Dummy: href = CTUIL_NEWS_URL; text = title_el.get_text(" ", strip=True)
                title_a = Dummy()  # type: ignore

        if not title_a:
            continue

        title = title_a.get_text(" ", strip=True)
        href = _mk_abs(getattr(title_a, "href", None))

        # If day/month elements exist, coerce; else try to parse from adjacent text
        date_iso = None
        if day_el and mon_el:
            date_iso = _coerce_date(day_el.get_text(strip=True), mon_el.get_text(strip=True), year)
        else:
            # Try to sniff "dd Mon" around the node text
            neighbor_txt = _date_cleaner.sub(" ", r.get_text(" ", strip=True))
            m = re.search(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", neighbor_txt, re.I)
            if m:
                date_iso = _coerce_date(m.group(1), m.group(2), year)

        # Fallback to first day of month if nothing found (still useful for QA)
        if not date_iso:
            date_iso = f"{year:04d}-{month:02d}-01"

        # filter to target month
        if date_iso[:7] != f"{year:04d}-{month:02d}":
            continue

        out.append(UpdateItem(date=date_iso, title=title, url=href))

    # If we couldn't detect rows with selectors above, last fallback:
    if not out:
        for a in soup.select("a[href]"):
            t = a.get_text(" ", strip=True)
            if not t:
                continue
            out.append(UpdateItem(
                date=f"{year:04d}-{month:02d}-01",
                title=t,
                url=_mk_abs(a.get("href")),
            ))

        # keep only a manageable first page sized chunk
        out = out[:20]

    # de-dup by (title, url)
    seen = set()
    unique: List[UpdateItem] = []
    for it in out:
        key = (it.title, it.url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)
    return unique


def harvest_ctuil_month(year: int, month: int) -> List[Dict]:
    """
    Fetch CTUIL latest news page and return a list of dicts:
      { date:'YYYY-MM-DD', title:'...', url:'...', type:'Update', source:'CTUIL' }
    """
    resp = requests.get(CTUIL_NEWS_URL, timeout=30)
    resp.raise_for_status()
    items = _extract_items(resp.text, year, month)
    return [it.__dict__ for it in items]
