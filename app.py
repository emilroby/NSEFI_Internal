# app.py
# NSEFI dashboard — base look preserved; three floating update boxes on the left
# CTUIL (Latest News) scraper wired for October 2025 test run
from __future__ import annotations

import re
import base64
import calendar
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
TITLE = "NSEFI policy and regulatory monitoring dashboard"
DATA_DIR = Path("data")
NSEFI_LOGO_CANDIDATES = [
    "12th_year_anniversary_logo_transparent.png",
    "12th_year_anniversary_logo_transparent",
    "MNRE.png",
]
# Central/State/UT lists for the flyout menus (kept same structure you asked)
CENTRAL_ALL = ["MoP", "MNRE", "MoF", "CEA", "CTUIL", "CERC", "Grid India"]
STATES = sorted([
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
])
UTS = sorted([
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
])

st.set_page_config(
    page_title=TITLE,
    layout="wide",
    page_icon="🟩",
)

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────
def ist_now() -> datetime:
    # local machine time is fine for display
    return datetime.now()

def _find_logo_data_uri() -> str | None:
    for name in NSEFI_LOGO_CANDIDATES:
        p = DATA_DIR / name
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
            mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            return f"data:{mime};base64,{b64}"
    return None

def _month_year(dt: datetime) -> tuple[int, int]:
    return dt.year, dt.month

# ─────────────────────────────────────────────────────────────────────────────
# CSS (base appearance preserved) + nav flyouts + floating cards
# ─────────────────────────────────────────────────────────────────────────────
def css() -> str:
    return f"""
<style>
html, body, .stApp {{
  background:
    radial-gradient(1200px 700px at 12% -10%, #F3FAF6 0%, transparent 60%),
    radial-gradient(1200px 700px at 90% 0%, #E8F3EE 0%, transparent 65%),
    linear-gradient(180deg, #FFFFFF 0%, #F7FBF9 100%);
  font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}}
#MainMenu, footer, header {{ visibility: hidden; height: 0; }}
.block-container {{ padding-top: 0 !important; margin-top: 0 !important; }}

/* top bar */
.topbar {{ margin-top: 1.2rem; font-weight:700; color:#0F4237; font-size:14px; }}
.titlebar {{ display:flex; align-items:center; justify-content:center; gap:12px; }}
.pagetitle {{ font-weight:900; color:#0F4237; font-size: clamp(28px, 3.2vw, 40px); }}
.pagetitle-logo img {{ height: 60px; width:auto; }}

/* navbar */
.navbar {{ margin-top: 1.4rem; background:#165843; border-radius:12px; box-shadow:0 1px 6px rgba(0,0,0,.12); }}
.navbar > ul {{ list-style:none; margin:0; padding:0; display:flex; }}
.navbar > ul > li {{ position:relative; }}
.navbar a, .navbar span {{
  display:block; padding:10px 16px; color:#fff; text-decoration:none;
  font-weight:700; font-size:15px;
}}
.navbar > ul > li:hover {{ background:#0d3d30; border-radius:12px; }}

/* flyout menus for Policies/Regulations */
.navbar ul li .dropdown {{
  position:absolute; top:100%; left:0; background:#0d3d30;
  border-radius:10px; box-shadow:0 6px 16px rgba(0,0,0,0.25);
  z-index:10001; padding:8px; visibility:hidden; opacity:0; transition:opacity .12s;
  min-width: 220px;
}}
.navbar ul li:hover > .dropdown {{ visibility:visible; opacity:1; }}
.navbar .dropdown .root {{ list-style:none; margin:0; padding:0; }}
.navbar .dropdown .root > li {{ position:relative; }}
.navbar .dropdown .root > li > span {{
  display:flex; align-items:center; justify-content:space-between; color:#fff;
  font-weight:800; font-size:14px; padding:8px 12px; border-radius:8px; cursor:default;
}}
.navbar .dropdown .root > li > span::after {{ content:"›"; opacity:.8; margin-left:12px; }}
.navbar .dropdown .root > li:hover > span {{ background:rgba(255,255,255,.12); }}
.navbar .dropdown .flyout {{
  position:absolute; top:0; left:100%; background:#0d3d30; border-radius:10px;
  min-width:280px; max-height: 320px; overflow:auto; padding:8px;
  box-shadow:0 6px 16px rgba(0,0,0,.25); z-index:10002; visibility:hidden; opacity:0; transition:opacity .12s;
}}
.navbar .dropdown .root > li:hover > .flyout {{ visibility:visible; opacity:1; }}
.navbar .dropdown .flyout ul {{ list-style:none; margin:0; padding:0; }}
.navbar .dropdown .flyout li a {{
  display:block; padding:7px 10px; border-radius:8px; color:#fff; font-size:14px; text-decoration:none;
}}
.navbar .dropdown .flyout li a:hover {{ background:rgba(255,255,255,.12); }}

/* headings */
.section-title {{ font-size:18px; font-weight:900; color:#0F4237; margin: 1.0em 0 8px 0; }}

/* date badge + rows (card content) */
.date-badge {{
  min-width:48px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  border-radius:10px; background:#fff; color:#0F4237; font-weight:900; line-height:1;
  padding:8px 8px; margin-right:12px;
}}
.date-badge .day {{ font-size:18px; }}
.date-badge .mon {{ font-size:11px; text-transform:uppercase; opacity:.8; margin-top:2px; }}
.row {{ display:flex; gap:12px; align-items:flex-start; padding:12px 14px;
        border-bottom:1px solid rgba(255,255,255,.08); }}
.row-title a {{ color:#fff; font-weight:700; text-decoration:none; }}
.row-title a:hover {{ text-decoration:underline; }}
.row-meta {{ font-size:12px; opacity:.85; margin-top:6px; }}

/* floating panels (left side) */
.float-stack {{ position: fixed; left: 18px; top: 160px; width: 480px; z-index: 9998; }}
.float-card {{
  background:#0F4237; color:#fff; border-radius:12px; box-shadow:0 10px 22px rgba(16,40,32,0.18);
  margin-bottom:14px; overflow:hidden;
}}
.float-head {{ padding:12px 16px; font-weight:800; background:#0e3f34; font-size:20px; }}
.float-body {{ max-height: 38vh; overflow:auto; }}
.float-empty {{ padding:18px 16px; opacity:.95; }}

/* Streamlit decorator clean ups */
.stSelectbox label {{ display:none !important; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
"""

def _links_list(page: str, level: str, names: list[str]) -> str:
    return "".join(
        f'<li><a target="_self" href="?page={page}&level={level}&entity={name.replace(" ", "%20")}">{name}</a></li>'
        for name in names
    )

def dropdown_html(page: str) -> str:
    central_links = _links_list(page, "central", CENTRAL_ALL)
    states_links  = _links_list(page, "state", STATES)
    uts_links     = _links_list(page, "state", UTS)
    return f"""
<div class="dropdown">
  <ul class="root">
    <li class="has-fly"><span>Central</span><div class="flyout"><ul>{central_links}</ul></div></li>
    <li class="has-fly"><span>States</span><div class="flyout"><ul>{states_links}</ul></div></li>
    <li class="has-fly"><span>Union Territories</span><div class="flyout"><ul>{uts_links}</ul></div></li>
  </ul>
</div>
"""

def navbar_html() -> str:
    return f"""
<nav class="navbar">
  <ul>
    <li><a target="_self" href="?page=home">Home</a></li>
    <li><a target="_self" href="?page=representations">Representations</a></li>
    <li><span>Policies</span>{dropdown_html("policies")}</li>
    <li><span>Regulations</span>{dropdown_html("regulations")}</li>
  </ul>
</nav>
"""

def render_header():
    now = ist_now()
    date_str = f"{now.strftime('%d')} - {now.strftime('%B').lower()} - {now.strftime('%Y')}"
    time_str = f"{now.strftime('%H:%M:%S')} IST"
    logo_uri = _find_logo_data_uri()

    st.markdown(
        f"""
        <div class="topbar">
            <span>{date_str}</span>
            <span style="opacity:.5">|</span>
            <span>{time_str}</span>
        </div>
        <div class="titlebar">
            <h1 class="pagetitle">{TITLE}</h1>
            {f'<div class="pagetitle-logo"><img src="{logo_uri}" alt="NSEFI logo"/></div>' if logo_uri else ''}
        </div>
        {navbar_html()}
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# CTUIL scraper (Latest News) — October 2025 test
# ─────────────────────────────────────────────────────────────────────────────
CTUIL_BASE = "https://ctuil.in"
CTUIL_LATEST = "https://ctuil.in/latestnews"

DATE_PATTERNS = [
    r"(\d{2})\.(\d{2})\.(\d{4})",      # 08.10.2025
    r"(\d{2})[/-](\d{2})[/-](\d{4})",  # 08/10/2025 or 08-10-2025
    r"(\d{2})\s+([A-Za-z]+)\s+(\d{4})" # 08 Oct 2025
]

def _parse_date(text: str) -> datetime | None:
    t = text.strip()
    for pat in DATE_PATTERNS:
        m = re.search(pat, t)
        if not m:
            continue
        if len(m.groups()) == 3:
            d, b, y = m.groups()
            try:
                if b.isalpha():
                    # e.g., 08 Oct 2025
                    return datetime.strptime(" ".join([d, b[:3], y]), "%d %b %Y")
                else:
                    # e.g., 08.10.2025 or 08/10/2025
                    return datetime(int(y), int(b), int(d))
            except Exception:
                pass
    return None

def harvest_ctuil_month(year: int, month: int) -> list[dict]:
    """
    Return a list of items: [{date:'YYYY-MM-DD', title:'...', url:'...', type:'CTUIL'}]
    filtered for given year/month (e.g. October 2025).
    """
    try:
        r = requests.get(CTUIL_LATEST, timeout=20)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # The page has a table-like list (Sr. No / Date / Title).
    # We'll search rows that contain a date cell and a title link.
    items: list[dict] = []

    # Find all rows that could contain date+title.
    # Strategy: look for any element whose text matches a date and has a link in the same row/parent.
    for row in soup.find_all(["tr", "div", "li", "article", "section"]):
        txt = row.get_text(" ", strip=True)
        dt = _parse_date(txt)
        if not dt:
            continue

        if dt.year != year or dt.month != month:
            continue

        # Find the first meaningful title link inside this row
        a = row.find("a", href=True)
        if not a:
            continue

        title = a.get_text(" ", strip=True)
        href = urljoin(CTUIL_BASE, a["href"])

        items.append({
            "date": dt.strftime("%Y-%m-%d"),
            "title": title,
            "url": href,
            "type": "CTUIL",
        })

    # Sort by date desc, then title
    items.sort(key=lambda x: (x["date"], x["title"]), reverse=True)
    return items

# ─────────────────────────────────────────────────────────────────────────────
# Render helpers (floating cards)
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_badge(iso_date: str) -> str:
    try:
        y, m, d = map(int, iso_date.split("-"))
        dt = datetime(y, m, d)
        return f"<div class='date-badge'><div class='day'>{dt.strftime('%d')}</div><div class='mon'>{dt.strftime('%b').upper()}</div></div>"
    except Exception:
        return "<div class='date-badge'><div class='day'>—</div><div class='mon'></div></div>"

def _items_html(items: list[dict]) -> str:
    rows = []
    for it in items:
        badge = _fmt_badge(it.get("date", ""))
        title = (it.get("title", "") or "").replace("<", "&lt;").replace(">", "&gt;")
        url = it.get("url")
        link = f"<a href='{url}' target='_blank' rel='noopener'>{title}</a>" if url else title
        rows.append(f"<div class='row'>{badge}<div class='row-main'><div class='row-title'>{link}</div><div class='row-meta'>CTUIL</div></div></div>")
    return "".join(rows)

def floating_tripanel(ctuil_items: list[dict]):
    # three stacked floating panels (left side)
    st.markdown("<div class='float-stack'>", unsafe_allow_html=True)

    # Central (CTUIL) — bold & larger as requested
    st.markdown("<div class='float-card'><div class='float-head'>Central</div>", unsafe_allow_html=True)
    if ctuil_items:
        st.markdown(f"<div class='float-body'>{_items_html(ctuil_items)}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='float-empty'>No updates found.</div></div>", unsafe_allow_html=True)

    # States
    st.markdown("<div class='float-card'><div class='float-head'>States</div><div class='float-empty'>No updates found.</div></div>", unsafe_allow_html=True)

    # UTs
    st.markdown("<div class='float-card'><div class='float-head'>UTs</div><div class='float-empty'>No updates found.</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────────────────────────────────
def page_home():
    # Only October 2025 for the test run you asked
    year, month = 2025, 10

    ctuil_items = harvest_ctuil_month(year, month)

    # Heading (kept your semantics)
    st.markdown(f"<div class='section-title'>Latest updates — {calendar.month_name[month]} {year}</div>",
                unsafe_allow_html=True)

    # Show the three floating boxes on the left
    floating_tripanel(ctuil_items)

    # Keep the center page empty (as per your base); floating panels carry the feed
    st.write("")  # spacer

def page_policies():
    st.subheader("Policies")
    st.info("Hover the menu (top) to pick Central / States / UTs. (Base retained)")

def page_regulations():
    st.subheader("Regulations")
    st.info("Hover the menu (top) to pick Central / States / UTs. (Base retained)")

# ─────────────────────────────────────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown(css(), unsafe_allow_html=True)
    render_header()

    page = st.query_params.get("page", "home")
    if isinstance(page, list):  # just to be safe
        page = page[0]

    if page == "home":
        page_home()
    elif page == "policies":
        page_policies()
    elif page == "regulations":
        page_regulations()
    elif page == "representations":
        st.subheader("Representations")
        st.info("This section remains from your base. (No changes requested.)")
    else:
        page_home()

if __name__ == "__main__":
    main()
