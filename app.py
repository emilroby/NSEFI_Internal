# app.py
from __future__ import annotations
import base64
from pathlib import Path
from datetime import datetime

import streamlit as st

# storage + adapters
from backend.storage import (
    read_month_snapshot,
    ist_now,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config & Constants
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSEFI policy and regulatory monitoring dashboard",
    layout="wide",
    page_icon="🟩",
)

TITLE = "NSEFI policy and regulatory monitoring dashboard"
DATA_DIR = Path("data")

# Canonical lists
CENTRAL_ALL = ["MoP", "MNRE", "MoF", "CEA", "CTUIL", "CERC", "Grid India"]
STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]
UTS = [
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]


# ─────────────────────────────────────────────────────────────────────────────
# Utilities (Image loading)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def find_asset(prefix_or_exact: str) -> Path | None:
    """Finds an asset file in the data directory."""
    if not DATA_DIR.exists(): return None
    p = DATA_DIR / prefix_or_exact
    if p.exists(): return p
    for ext in ("png", "jpg", "jpeg", "svg", "webp"):
        q = DATA_DIR / f"{prefix_or_exact}.{ext}"
        if q.exists(): return q
    for q in DATA_DIR.iterdir():
        if q.is_file() and q.stem.lower() == prefix_or_exact.lower(): return q
    return None


@st.cache_data
def image_to_data_uri(path: Path | None) -> str | None:
    """Converts an image file to a data URI for embedding in HTML."""
    if not path or not path.exists(): return None
    ext = path.suffix.lower()
    if ext == ".svg": return f"data:image/svg+xml;utf8,{path.read_text(encoding='utf-8')}"
    mime = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg", ".jpeg") else "image/webp")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


# Corrected Logo Loading Logic
NSEFI_URI = image_to_data_uri(find_asset("12th_year_anniversary_logo_transparent")) \
            or image_to_data_uri(find_asset("NSEFI")) \
            or image_to_data_uri(find_asset("MNRE")) \
            or "https://nsefi.in/wp-content/uploads/2023/02/NSEFI-Logo-1.png"


# ─────────────────────────────────────────────────────────────────────────────
# CSS & JavaScript Injection
# ─────────────────────────────────────────────────────────────────────────────
def css() -> str:
    return f"""
<style>
/* remove default chrome */
#MainMenu {{ visibility:hidden; }}
footer {{ visibility:hidden; }}
header {{ visibility:hidden; }}
.block-container {{ padding-top: 1rem !important; }}

/* background + font */
html, body, .stApp {{
  background:
    radial-gradient(1200px 700px at 12% -10%, #F3FAF6 0%, transparent 60%),
    radial-gradient(1200px 700px at 90% 0%, #E8F3EE 0%, transparent 65%),
    linear-gradient(180deg, #FFFFFF 0%, #F7FBF9 100%);
  font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  color: #0F4237;
}}

.topbar {{
  display:flex; align-items:center; justify-content:space-between;
  margin: .4rem 0 1.0rem 0;
  font-weight:700; color:#0F4237; font-size: 14px;
}}
.topbar .brand img {{ height: 64px; width:auto; }}

.pagetitle {{
  font-weight:900; color:#1e2a2a; 
  font-size: clamp(28px, 4.2vw, 48px);
  margin: 0.4rem 0 1.0rem 0;
  text-align: center;
}}

/* navbar with hover flyouts */
.navbar {{
  margin-top: 0.4rem; background:#165843; border-radius:16px; 
  box-shadow:0 2px 10px rgba(0,0,0,.12);
}}
.navbar > ul {{ list-style:none; margin:0; padding:0; display:flex; gap:8px; }}
.navbar > ul > li {{ position:relative; }}
.navbar a, .navbar span {{
  display:block; padding:12px 22px; color:#fff; text-decoration:none; 
  font-weight:700; font-size:16px; border-radius:14px;
}}
.navbar > ul > li:hover {{ background:#0d3d30; border-radius:14px; }}

.dropdown {{
  position:absolute; top:100%; left:0; background:#0d3d30;
  border-radius:14px; box-shadow:0 10px 22px rgba(0,0,0,0.25);
  z-index:10001; padding:10px; visibility:hidden; opacity:0; transition:opacity .12s;
  min-width: 240px;
}}
.navbar ul li:hover > .dropdown {{ visibility:visible; opacity:1; }}
.dropdown .root {{ list-style:none; margin:0; padding:0; }}
.dropdown .root > li {{ position:relative; }}
.dropdown .root > li > span {{
  display:flex; align-items:center; justify-content:space-between; 
  color:#fff; font-weight:800; font-size:14px;
  padding:10px 12px; border-radius:10px; cursor:default;
}}
.dropdown .root > li > span::after {{ content:"›"; opacity:.8; margin-left:12px; }}
.dropdown .root > li:hover > span {{ background:rgba(255,255,255,.12); }}
.dropdown .flyout {{
  position:absolute; top:0; left:100%; background:#0d3d30; border-radius:12px;
  min-width:280px; max-height: 340px; overflow:auto; padding:10px; 
  box-shadow:0 10px 22px rgba(0,0,0,.25);
  z-index:10002; visibility:hidden; opacity:0; transition:opacity .12s;
}}
.dropdown .root > li:hover > .flyout {{ visibility:visible; opacity:1; }}
.dropdown .flyout ul {{ list-style:none; margin:0; padding:0; }}
.dropdown .flyout li a {{
  display:block; padding:8px 10px; border-radius:8px; color:#fff; 
  font-size:14px; text-decoration:none;
}}
.dropdown .flyout li a:hover {{ background:rgba(255,255,255,.12); }}

.section-title {{ 
  font-size:22px; font-weight:900; color:#0F4237; 
  margin: 1.0rem 0 12px 0; 
}}

.col-heading {{
  font-weight:900; font-size:20px; margin: .5rem 0 .4rem 0; 
}}
.stSelectbox label {{ display:none !important; }}
.stSelectbox > div > div {{ border-radius:12px !important; }}

/* MODIFIED: This section enables the floating panel effect */
.fcard {{
  background:#0F4237; color:#fff; border-radius:14px; 
  box-shadow:0 14px 22px rgba(16,40,32,0.18);
  padding:0; overflow:hidden; position:relative;
  /* Set a fixed height for all panels */
  height: 400px; 
}}
.fcard-body {{
  /* This container will hold all the update rows */
  height: 100%; /* Fill the parent .fcard */
  overflow-y:auto; /* Allow manual scrolling if content is too long */
  scroll-behavior: smooth;
}}
/* END MODIFICATION */

.urow {{
  display:flex; gap:14px; align-items:flex-start; padding:14px 16px; 
  font-size:14px; line-height:1.4; border-bottom:1px solid rgba(255,255,255,.10);
}}
.badge {{
  min-width:52px; display:flex; flex-direction:column; align-items:center; 
  justify-content:center; border-radius:10px; background:#fff; color:#0F4237; 
  font-weight:900; line-height:1; padding:8px 8px;
}}
.badge .day {{ font-size:18px; }}
.badge .mon {{ font-size:11px; text-transform:uppercase; opacity:.8; margin-top:2px; }}
.urow a {{ color:#fff; font-weight:700; text-decoration:none; }}
.urow a:hover {{ text-decoration:underline; }}

</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet">
"""


# ADDED: This function contains the necessary JavaScript for real-time features.
def javascript_injector() -> str:
    """Returns all necessary JavaScript with a robust initializer."""
    return """
<script>
    // --- SCRIPT DEFINITIONS ---

    // 1. Real-Time Clock Script
    function updateClock() {
        const clockElement = document.getElementById("realtime-clock");
        if (clockElement) {
            const now = new Date();
            const options = { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
            const formatter = new Intl.DateTimeFormat('en-GB', options);
            const parts = formatter.formatToParts(now);
            const day = parts.find(p => p.type === 'day').value;
            const month = parts.find(p => p.type === 'month').value.toLowerCase();
            const year = parts.find(p => p.type === 'year').value;
            const time = parts.filter(p => ['hour', 'minute', 'second'].includes(p.type)).map(p => p.value).join(':');
            clockElement.innerHTML = `${day} - ${month} - ${year} &nbsp;|&nbsp; ${time} IST`;
        }
    }

    // 2. Floating Panel Script
    function initFloatingPanels(){
        const speedPxPerSec = 26;
        const resumeDelayMs = 6000;
        const raf = window.requestAnimationFrame || (fn => setTimeout(fn, 16));

        document.querySelectorAll(".fcard-body").forEach(el => {
            let pausedHover = false, pausedUser = false, lastUserTs = 0;
            const pauseUser = () => { pausedUser = true; lastUserTs = Date.now(); };
            const maybeResume = () => { if (pausedUser && (Date.now() - lastUserTs) > resumeDelayMs) pausedUser = false; };
            el.addEventListener("mouseenter", () => pausedHover = true);
            el.addEventListener("mouseleave", () => pausedHover = false);
            ["wheel", "touchstart", "touchmove", "scroll", "keydown"].forEach(evt => el.addEventListener(evt, pauseUser, { passive: true }));

            (function tick() {
                maybeResume();
                if (!pausedHover && !pausedUser) {
                    el.scrollTop += speedPxPerSec / 60.0;
                    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 1) {
                        el.scrollTop = 0;
                    }
                }
                raf(tick);
            })();
        });
    }

    // --- ROBUST INITIALIZER (THE FIX) ---
    const initializer = setInterval(function() {
        const clockElement = document.getElementById("realtime-clock");
        const panelElements = document.querySelectorAll(".fcard-body");

        if (clockElement && panelElements.length > 0) {
            updateClock();
            setInterval(updateClock, 1000);
            initFloatingPanels();
            clearInterval(initializer);
        }
    }, 100);
</script>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Navbar with flyouts
# ─────────────────────────────────────────────────────────────────────────────
def _links_list(page: str, level: str, names: list[str]) -> str:
    from urllib.parse import quote
    return "".join(
        f'<li><a target="_self" href="?page={page}&level={level}&entity={quote(name)}">{name}</a></li>'
        for name in names
    )


def dropdown_html(page: str) -> str:
    central_links = _links_list(page, "central", CENTRAL_ALL)
    states_links = _links_list(page, "state", STATES)
    uts_links = _links_list(page, "state", UTS)
    return f"""
<div class="dropdown">
  <ul class="root">
    <li class="has-fly">
      <span>Central</span>
      <div class="flyout"><ul>{central_links}</ul></div>
    </li>
    <li class="has-fly">
      <span>States</span>
      <div class="flyout"><ul>{states_links}</ul></div>
    </li>
    <li class="has-fly">
      <span>Union Territories</span>
      <div class="flyout"><ul>{uts_links}</ul></div>
    </li>
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


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────────────
def render_header():
    # MODIFIED: Changed the static timestamp to a placeholder div with an ID.
    st.markdown(
        f"""
        <div class="topbar">
          <div class="ts" id="realtime-clock">Loading...</div>
          <div class="brand"><img alt="NSEFI logo" src="{NSEFI_URI}"/></div>
        </div>
        <h1 class="pagetitle">{TITLE}</h1>
        {navbar_html()}
        """,
        unsafe_allow_html=True,
    )


def _badge(iso_date: str) -> str:
    try:
        y, m, d = [int(x) for x in iso_date.split("-")]
        dt = datetime(y, m, d)
        return f"<div class='badge'><div class='day'>{dt.strftime('%d')}</div><div class='mon'>{dt.strftime('%b').upper()}</div></div>"
    except Exception:
        return "<div class='badge'><div class='day'>—</div><div class='mon'></div></div>"


def _row_html(date_iso: str, title: str, url: str) -> str:
    # This function is simplified to match your desired output
    return f"""
    <div class="urow">
      {_badge(date_iso)}
      <div class="row-main">
        <div class="row-title"><a href="{url}" target="_blank" rel="noopener">{title}</a></div>
      </div>
    </div>
    """


def _panel_html(items: list[dict], body_id: str) -> str:
    if not items:
        body = "<div class='urow'><div>No updates found.</div></div>"
    else:
        body = "".join(
            _row_html(it.get("date", ""), it.get("title", ""), it.get("url", "#")) for it in
            items)
    return f"""
    <div class='fcard'>
      <div id="{body_id}" class='fcard-body'>
        {body}
      </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────────────────────
def page_home():
    now = ist_now()
    yyyy, mm = now.year, now.month

    snap = read_month_snapshot(yyyy, mm) or {}

    # In a full implementation, you would combine data from all central sources.
    all_central_items = []
    for source in CENTRAL_ALL:
        all_central_items.extend(snap.get("central", {}).get(source, []))

    st.markdown(f"<div class='section-title'>Latest updates — {now.strftime('%B')} {now.year}</div>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.markdown("<div class='col-heading'>Central</div>", unsafe_allow_html=True)
        selected_central = st.selectbox("Central filter", ["All"] + CENTRAL_ALL, index=0, key="central_filter",
                                        label_visibility="collapsed")

        if selected_central == "All":
            display_central_items = all_central_items
        else:
            display_central_items = snap.get("central", {}).get(selected_central, [])

        st.markdown(_panel_html(display_central_items, "body-central"), unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='col-heading'>States</div>", unsafe_allow_html=True)
        st.selectbox("State filter", ["All"] + STATES, index=0, key="state_filter", label_visibility="collapsed")
        st.markdown(_panel_html([], "body-states"), unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='col-heading'>UTs</div>", unsafe_allow_html=True)
        st.selectbox("UT filter", ["All"] + UTS, index=0, key="ut_filter", label_visibility="collapsed")
        st.markdown(_panel_html([], "body-uts"), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown(css(), unsafe_allow_html=True)
    render_header()
    page = st.query_params.get("page", "home")
    if isinstance(page, list):
        page = page[0]

    if page == "home":
        page_home()
    elif page == "representations":
        st.subheader("Representations")
        st.info("Your representations page placeholder.")
    elif page == "policies":
        st.subheader("Policies")
        st.info("Use the hover menu to pick Central / States / UTs / Entity.")
    elif page == "regulations":
        st.subheader("Regulations")
        st.info("Use the hover menu to pick Central / States / UTs / Entity.")
    else:
        page_home()

    # ADDED: This single line injects the JavaScript that makes the clock and panels work.
    st.markdown(javascript_injector(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()