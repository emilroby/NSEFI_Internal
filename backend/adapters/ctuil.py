# backend/adapters/ctuil.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Dict, Optional
from urllib.parse import urljoin

import re
import requests
from bs4 import BeautifulSoup

# The AJAX endpoint
CTUIL_LATEST_URL = "https://ctuil.in/latestnews?p=ajax"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://ctuil.in",
    "Referer": "https://ctuil.in/latestnews",
}


@dataclass
class CtuilItem:
    date: datetime
    title: str
    href: str
    type: str = "Update"

    def to_dict(self) -> Dict[str, str]:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "title": self.title.strip(),
            "url": self.href,
            "type": self.type,
        }


def _clean_text(s: str) -> str:
    """Standardizes whitespace to a single space and strips."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def _parse_date_ddmmyyyy(raw: str) -> Optional[datetime]:
    """Parses date strings like '14.10.2025'."""
    if not raw:
        return None
    raw = raw.strip().replace(".", "-").replace("/", "-")
    try:
        return datetime.strptime(raw, '%d-%m-%Y')
    except ValueError:
        print(f"WARN: Date parsing failed for: '{raw}'")
        return None


def _iter_latest_news_rows(soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
    """
    Finds the first table and directly iterates its rows (tr),
    bypassing the need for a <tbody> tag.
    """
    table = soup.find("table")
    if not table:
        print("DEBUG: Could not find any <table> element in the response.")
        return []

    # FIX: Search for <tr> directly within the table. This is more resilient
    # as some HTML tables omit the optional <tbody> tag.
    return table.find_all("tr")


def _row_to_item(base_url: str, tr: BeautifulSoup) -> Optional[CtuilItem]:
    """Extracts data from a single table row <tr> into a CtuilItem."""
    tds = tr.find_all("td")
    # We expect at least 3 cells: Sr.No., Date, Title.
    if len(tds) < 3:
        # This will safely skip the header row which uses <th> tags.
        return None

    date_text = _clean_text(tds[1].text)
    title_cell = tds[2]
    title_text = _clean_text(title_cell.text)

    a_tag = title_cell.find("a", href=True)
    if not a_tag:
        return None

    href = urljoin(base_url, a_tag["href"])
    dt = _parse_date_ddmmyyyy(date_text)
    if not dt:
        return None

    return CtuilItem(date=dt, title=title_text, href=href)


def _fetch_html(url: str, payload: dict) -> str:
    """Fetches HTML using a POST request."""
    with requests.Session() as s:
        s.headers.update(HEADERS)
        resp = s.post(url, data=payload, timeout=20)
        resp.raise_for_status()
        return resp.text


def harvest_ctuil_month(year: int, month: int) -> List[Dict[str, str]]:
    """Main function to scrape and filter CTUIL updates for a specific month."""
    payload = {
        'sort_field': 'LatestNews.news_date',
        'sort_type': 'DESC',
        'page': '1',
        'search_keyword': '',
        'from_date': '',
        'to_date': '',
    }

    try:
        html = _fetch_html(CTUIL_LATEST_URL, payload)
        print(f"DEBUG: Fetched HTML from {CTUIL_LATEST_URL} via POST. Size: {len(html)} bytes")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch URL {CTUIL_LATEST_URL}. Error: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    rows = list(_iter_latest_news_rows(soup))
    print(f"DEBUG: Found {len(rows)} total <tr> elements in the table.")

    items: List[CtuilItem] = []
    for tr in rows:
        item = _row_to_item(CTUIL_LATEST_URL, tr)
        if item and item.date.year == year and item.date.month == month:
            items.append(item)

    print(f"DEBUG: Filtered to {len(items)} items for {month:02d}/{year}.")
    items.sort(key=lambda x: x.date, reverse=True)
    return [it.to_dict() for it in items]


CTUIL_SOURCES = {
    "CTUIL": CTUIL_LATEST_URL,
}

__all__ = ["harvest_ctuil_month", "CTUIL_SOURCES"]