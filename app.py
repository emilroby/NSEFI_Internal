# version: 1.1.1
# app.py — NSEFI policy & regulatory monitoring dashboard (no map, floating updates)

from __future__ import annotations
import base64
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

import streamlit as st
import pandas as pd
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSEFI policy and regulatory monitoring dashboard",
    layout="wide",
    page_icon="🟩",
)

TITLE = "NSEFI policy and regulatory monitoring dashboard"
DATA_DIR = Path("data")

CENTRAL_ALL = ["MoP","MNRE","MoF","CEA","CTUIL","CERC","Grid India"]
CENTRAL_FOR_POLICIES = ["MoP","MNRE","MoF"]

STATES: List[str] = sorted([
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana",
    "Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur",
    "Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
    "Tripura","Uttar Pradesh","Uttarakhand","West Bengal"
])
UTS: List[str] = sorted([
    "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu",
    "Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"
])

# ─────────────────────────────────────────────────────────────────────────────
# Assets & helpers
# ─────────────────────────────────────────────────────────────────────────────
def find_asset(prefix_or_exact: str) -> Optional[Path]:
    if not DATA_DIR.exists():
        return None
    p = DATA_DIR / prefix_or_exact
    if p.exists():
        return p
    for ext in ("png","jpg","jpeg","svg","webp"):
        p = DATA_DIR / f"{prefix_or_exact}.{ext}"
        if p.exists():
            return p
    for p in DATA_DIR.iterdir():
        if p.is_file() and p.stem.lower() == prefix_or_exact.lower():
            return p
    return None

def image_to_data_uri(path: Path | None) -> str | None:
    if not path or not path.exists(): return None
    ext = path.suffix.lower()
    if ext == ".svg":
        return f"data:image/svg+xml;utf8,{path.read_text(encoding='utf-8')}"
    mime = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg",".jpeg") else "image/webp")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def pick_brand_green() -> str:
    src = find_asset("12th_year_anniversary_logo_transparent")
    if not src: return "#1b5e20"
    try:
        img = Image.open(src).convert("RGBA").resize((96,96))
        pixels = [(r,g,b) for (r,g,b,a) in img.getdata() if a>0]
        greens = [(r,g,b) for (r,g,b) in pixels if g>r and g>b and not (r>235 and g>235 and b>235)]
        pool = greens or [(r,g,b) for (r,g,b) in pixels if not (r>235 and g>235 and b>235)]
        r = int(sum(p[0] for p in pool)/len(pool)); g = int(sum(p[1] for p in pool)/len(pool)); b = int(sum(p[2] for p in pool)/len(pool))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#1b5e20"

BRAND        = pick_brand_green()  # Navbar matches NSEFI logo color
BRAND_DEEP   = "#0F4237"
BRAND_HOVER  = "#0d3d30"
TEXT_DARK    = "#0F4237"
NSEFI_URI    = image_to_data_uri(find_asset("12th_year_anniversary_logo_transparent"))

def qp(key: str, default: str = "") -> str:
    try: params = dict(st.query_params)
    except Exception: params = st.experimental_get_query_params()
    val = params.get(key, default)
    if isinstance(val, list): return val[0] if val else default
    return val if isinstance(val, str) else default

# ─────────────────────────────────────────────────────────────────────────────
# Dummy updates (current month + previous months generator)
# ─────────────────────────────────────────────────────────────────────────────
def aug_dates() -> List[str]:
    return ["2025-08-02","2025-08-05","2025-08-08","2025-08-11","2025-08-14",
            "2025-08-17","2025-08-20","2025-08-23","2025-08-26","2025-08-29"]

def make_aug_updates(name: str, tag: str) -> List[Dict]:
    ds = aug_dates()
    return [{"type": tag, "title": f"{name}: example update {i+1}", "date": ds[i]} for i in range(len(ds))]

STATE_UPDATES: Dict[str,List[Dict]]   = {s: make_aug_updates(s,"Regulatory") for s in STATES}
UT_UPDATES: Dict[str,List[Dict]]      = {u: make_aug_updates(u,"Regulatory") for u in UTS}
CENTRAL_UPDATES: Dict[str,List[Dict]] = {c: make_aug_updates(c,"Update") for c in CENTRAL_ALL}

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_TO_NUM = {m:i+1 for i,m in enumerate(MONTHS)}

def make_month_updates(name: str, tag: str, year: int, month_name: str) -> List[Dict]:
    m = MONTH_TO_NUM.get(month_name, 1)
    dates = [f"{year:04d}-{m:02d}-05", f"{year:04d}-{m:02d}-14", f"{year:04d}-{m:02d}-24"]
    return [{"type": tag, "title": f"{name}: {month_name} update {i+1}", "date": d} for i,d in enumerate(dates)]

def build_prev_maps(year: int, month_name: str):
    return (
        {c: make_month_updates(c,"Update", year, month_name) for c in CENTRAL_ALL},
        {s: make_month_updates(s,"Regulatory", year, month_name) for s in STATES},
        {u: make_month_updates(u,"Regulatory", year, month_name) for u in UTS},
    )

# ─────────────────────────────────────────────────────────────────────────────
# CSS — tight spacing + floating updates + navbar in NSEFI green
# ─────────────────────────────────────────────────────────────────────────────
def css() -> str:
    return f"""
<style>
:root {{
  --brand: {BRAND};
  --brandDeep: {BRAND_DEEP};
  --brandHover: {BRAND_HOVER};
  --textDark: {TEXT_DARK};
}}
html, body, .stApp {{
  background:
    radial-gradient(1200px 700px at 12% -10%, #F3FAF6 0%, transparent 60%),
    radial-gradient(1200px 700px at 90% 0%, #E8F3EE 0%, transparent 65%),
    linear-gradient(180deg, #FFFFFF 0%, #F7FBF9 100%);
  font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}}
#MainMenu, footer, header {{ visibility:hidden; height:0; }}
.block-container {{ padding-top:.40rem !important; overflow:visible; }}

/* Top bar — timestamp (left) + NSEFI logo (right) */
.topbar {{
  display:flex; align-items:center; justify-content:space-between; gap:18px;
  padding:4px 0 0 0; font-weight:700; color:#0F4237; font-size:16px;
}}
.topbar .dt {{ display:flex; align-items:center; gap:10px; }}
.topbar .nsefi img {{
  height: 60px; width:auto; background:transparent !important; border-radius:0 !important;
  padding:0 !important; box-shadow:none !important;
}}

/* Centered title, pulled close to navbar */
.titlewrap {{ margin:0; padding:0; line-height:1; }}
.pagetitle {{
  text-align:center; font-weight:900; color:var(--textDark);
  margin: 18px 0 8px 0 !important; padding:0 !important;
  font-size:38px; line-height:1.1;
}}

/* Navbar = NSEFI green, compact height, minimal outer gap */
.navbar {{
  margin: 0 !important;
  background: var(--brand);
  border-radius: 10px;
  padding: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,.10);
}}
.navbar > ul {{ list-style:none; margin:0; padding:0; display:flex; }}
.navbar > ul > li {{ position:relative; }}
.navbar a, .navbar span {{
  display:block; padding:8px 16px;
  color:#fff; text-decoration:none; font-weight:700; font-size:15px;
}}
.navbar > ul > li:hover {{ background: var(--brandHover); border-radius:10px; }}

/* Dropdown menu */
.navbar ul li .dropdown {{
  visibility:hidden; opacity:0; transition:opacity .12s ease-in-out;
  position:absolute; background:var(--brandHover); width:340px; top:100%; left:0;
  border-radius:0 0 10px 10px; box-shadow:0 6px 16px rgba(0,0,0,0.25);
  z-index:100001; padding:8px 10px;
}}
.navbar ul li:hover > .dropdown {{ visibility:visible; opacity:1; }}
.navbar .dropdown ul {{ list-style:none; margin:0; padding:0; max-height:230px; overflow:auto; }}
.menu-title {{ color:#e6fff5; font-size:12px; font-weight:800; margin:6px; }}
.menu-list li a {{ display:block; padding:7px 10px; border-radius:8px; color:#fff; font-size:14px; }}
.menu-list li a:hover {{ background:rgba(255,255,255,.12); }}

/* Section headings */
.section-title {{ font-size:18px; font-weight:900; color:var(--textDark); margin:10px 0 8px; }}
.box-title {{ font-size:20px; font-weight:900; color:var(--textDark); margin:2px 0 4px; }}

/* Prev updates block — snug under navbar */
.prev-card {{
  margin: 8px 0 10px 0;
  padding: 10px 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fcfa 100%);
  border: 1px solid #e5ece8; border-radius: 12px;
  box-shadow: 0 4px 12px rgba(16,40,32,0.05);
}}
.prev-title {{ font-size: 18px; font-weight: 900; color: var(--textDark); margin: 0 0 6px 0; }}

/* Hide default labels on selects (we use placeholders/titles) */
[data-baseweb="select"] label, .stSelectbox label {{ display:none !important; }}
.stSelectbox > div > div {{ border-radius:12px!important; }}

/* Sticky Latest Updates row (floats while scrolling) — closer to top */
.float-row {{ position: sticky; top: 74px; z-index: 5; }}

/* Updates ticker */
.updates {{
  position:relative; background:var(--brandDeep); color:#ffffff;
  border-radius:10px; padding:0; overflow:hidden;
  box-shadow:0 8px 18px rgba(16,40,32,0.06);
}}
.ticker  {{ position:relative; height:220px; overflow:hidden; }}
.track   {{ position:absolute; left:0; right:0; top:0; animation: moveUp 22s linear infinite; }}
.updates:hover .track {{ animation-play-state: paused; }}
.item {{ padding:10px 12px; font-size:14px; line-height:1.4; border-bottom:1px solid rgba(255,255,255,.08); }}
.tag  {{ font-size:11px; padding:2px 8px; border:1px solid rgba(255,255,255,.6); border-radius:999px; margin-right:8px; }}

@keyframes moveUp {{ 0% {{ transform:translateY(0); }} 100% {{ transform:translateY(-50%); }} }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
"""

# ─────────────────────────────────────────────────────────────────────────────
# Navbar HTML
# ─────────────────────────────────────────────────────────────────────────────
def dropdown_html(page: str) -> str:
    centrals = CENTRAL_FOR_POLICIES if page == "policies" else CENTRAL_ALL
    central_links = "".join(
        f'<li><a target="_self" href="?page={page}&level=central&entity={c.replace(" ", "%20")}">{c}</a></li>'
        for c in centrals
    )
    states_links = "".join(
        f'<li><a target="_self" href="?page={page}&level=state&entity={s.replace(" ", "%20")}">{s}</a></li>'
        for s in STATES
    )
    uts_links = "".join(
        f'<li><a target="_self" href="?page={page}&level=state&entity={u.replace(" ", "%20")}">{u}</a></li>'
        for u in UTS
    )
    return f"""
<ul class="dropdown">
  <div class="menu-section"><div class="menu-title">Central</div><ul class="menu-list">{central_links}</ul></div>
  <div class="menu-section"><div class="menu-title">States</div><ul class="menu-list">{states_links}</ul></div>
  <div class="menu-section"><div class="menu-title">Union Territories</div><ul class="menu-list">{uts_links}</ul></div>
</ul>
"""

def navbar_html() -> str:
    return f"""
<nav class="navbar">
  <ul>
    <li><a target="_self" href="?page=home">Home</a></li>
    <li><span>Representations</span>{dropdown_html("representations")}</li>
    <li><span>Policies</span>{dropdown_html("policies")}</li>
    <li><span>Regulations</span>{dropdown_html("regulations")}</li>
  </ul>
</nav>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Header (timestamp+logo, title, navbar)
# ─────────────────────────────────────────────────────────────────────────────
def header_bar():
    now = datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.now()
    date_str = f"{now.strftime('%d')} - {now.strftime('%B').lower()} - {now.strftime('%Y')}"
    time_str = f"{now.strftime('%H:%M:%S')} IST"
    right_logo = f"<img src='{NSEFI_URI}' alt='NSEFI'/>" if NSEFI_URI else ""

    st.markdown(
        f"""
        <div class="topbar">
          <div class="dt"><span id="live-date">{date_str}</span><span style="opacity:.55">|</span><span id="live-time">{time_str}</span></div>
          <div class="nsefi">{right_logo}</div>
        </div>
        <div class="titlewrap"><h1 class="pagetitle">{TITLE}</h1></div>
        {navbar_html()}
        """,
        unsafe_allow_html=True,
    )

    # Live clock
    st.components.v1.html(
        """
        <script>
          (function(){
            function render(){
              const now = new Date();
              const opts = { timeZone:'Asia/Kolkata', year:'numeric', month:'long', day:'2-digit',
                             hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false };
              const parts = new Intl.DateTimeFormat('en-GB', opts).formatToParts(now)
                            .reduce((a,p)=>{a[p.type]=p.value; return a;}, {});
              const d = `${parts.day} - ${(parts.month||'').toLowerCase()} - ${parts.year}`;
              const t = `${parts.hour}:${parts.minute}:${parts.second} IST`;
              const dEl = window.parent.document.getElementById('live-date');
              const tEl = window.parent.document.getElementById('live-time');
              if(dEl) dEl.textContent = d;
              if(tEl) tEl.textContent = t;
            }
            render(); setInterval(render, 1000);
          })();
        </script>
        """,
        height=0,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Updates (floating/animated tickers)
# ─────────────────────────────────────────────────────────────────────────────
def ticker_html(items: List[Dict]) -> str:
    rows = "".join(
        f"<div class='item'><span class='tag'>{it['type']}</span>{it['title']} — <i>{it['date']}</i></div>"
        for it in items
    )
    return f"<div class='ticker'><div class='track'>{rows}{rows}</div></div>"

def updates_box(title_text: str, placeholder: str, options: List[str], data_map: Dict[str, List[Dict]], key: str):
    st.markdown(f"<div class='box-title'>{title_text}</div>", unsafe_allow_html=True)
    choice = st.selectbox(placeholder, ["All"] + options, index=0, key=key, label_visibility="collapsed")
    if choice == "All":
        items = []
        for opt in options:
            items.extend(data_map.get(opt, [])[:3])
        if not items:
            items = [{"type":"Update","title":"No updates available","date":"2025-08-01"}]
    else:
        items = data_map.get(choice, [{"type":"Update","title":f"No updates for {choice}","date":"2025-08-01"}])
    st.markdown("<div class='updates'>" + ticker_html(items) + "</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────────────────────────────────
def page_home():
    # Previous updates box (just below navbar)
    with st.container():
        st.markdown("<div class='prev-card'>", unsafe_allow_html=True)
        st.markdown("<div class='prev-title'>Previous updates</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            year = st.selectbox("Year", ["Choose an option"] + ["2024","2025"], index=0, key="prev_year", label_visibility="collapsed")
        with c2:
            month = st.selectbox("Month", ["Choose an option"] + MONTHS, index=0, key="prev_month", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    if year != "Choose an option" and month != "Choose an option":
        central_prev, state_prev, ut_prev = build_prev_maps(int(year), month)
        st.markdown("<div class='section-title'>Previous updates — " + f"{month} {year}" + "</div>", unsafe_allow_html=True)
        cpa, cpb, cpc = st.columns(3)
        with cpa:
            updates_box("Central", "Choose a central body", CENTRAL_ALL, central_prev, key="prev_central_sel")
        with cpb:
            updates_box("States", "Choose a state", STATES, state_prev, key="prev_state_sel")
        with cpc:
            updates_box("UTs", "Choose a UT", UTS, ut_prev, key="prev_ut_sel")

    # Latest updates (floating row)
    st.markdown("<div class='section-title'>Latest updates — August 2025</div>", unsafe_allow_html=True)
    st.markdown("<div class='float-row'>", unsafe_allow_html=True)
    cu1, cu2, cu3 = st.columns(3)
    with cu1:
        updates_box("Central", "Choose a central body", CENTRAL_ALL, CENTRAL_UPDATES, key="central_sel")
    with cu2:
        updates_box("States", "Choose a state", STATES, STATE_UPDATES, key="state_sel")
    with cu3:
        updates_box("UTs", "Choose a UT", UTS, UT_UPDATES, key="ut_sel")
    st.markdown("</div>", unsafe_allow_html=True)

def table(df: pd.DataFrame):
    st.dataframe(df, use_container_width=True, hide_index=True)

def page_representations(level: str, entity: str):
    st.subheader("Representations")
    if level == "central":
        if entity not in CENTRAL_ALL:
            st.info("Use the ribbon → Representations → Central to choose a body."); return
        rows = [
            {"date": "2025-08-07", "to": entity, "subject": "Open Access banking window for RE", "status": "Submitted"},
            {"date": "2025-08-21", "to": entity, "subject": "Scheduling & dispatch for VRE — improvements", "status": "Drafting"},
        ]
        table(pd.DataFrame(rows))
    elif level == "state":
        if entity not in STATES + UTS:
            st.info("Use the ribbon → Representations → State/UT to choose a region."); return
        rows = [
            {"date": "2025-08-08", "to": entity, "subject": f"{entity}: Rooftop net metering clarifications", "status": "Submitted"},
            {"date": "2025-08-19", "to": entity, "subject": f"{entity}: OA charges for RE — consult", "status": "Under review"},
        ]
        table(pd.DataFrame(rows))
    else:
        st.info("Open the menu and choose Central or State/UT.")

def page_policies(level: str, entity: str):
    st.subheader("Policies")
    if level == "central":
        if entity not in CENTRAL_FOR_POLICIES:
            st.info("Use the ribbon → Policies → Central to choose MNRE / MoP / MoF."); return
        st.info("At the national (Central) level: there is no policy to display.")
    elif level == "state":
        if entity not in STATES + UTS:
            st.info("Use the ribbon → Policies → State/UT to choose a region."); return
        rows = [{"policy": f"{entity} Renewable Energy Policy (placeholder)", "effective_from": "2025-08-01"}]
        table(pd.DataFrame(rows))
    else:
        st.info("Open the menu and choose Central or State/UT.")

def page_regulations(level: str, entity: str):
    st.subheader("Regulations")
    if level == "central":
        if entity not in CENTRAL_ALL:
            st.info("Use the ribbon → Regulations → Central to choose a body."); return
        rows = [{"regulation": f"{entity} — DSM / scheduling note (placeholder)", "effective_from": "2025-08-15"}]
        table(pd.DataFrame(rows))
    elif level == "state":
        if entity not in STATES + UTS:
            st.info("Use the ribbon → Regulations → State/UT to choose a region."); return
        rows = [{"regulation": f"{entity} SERC — OA / NM update (placeholder)", "effective_from": "2025-08-22"}]
        table(pd.DataFrame(rows))
    else:
        st.info("Open the menu and choose Central or State/UT.")

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown(css(), unsafe_allow_html=True)
    header_bar()

    page  = qp("page", "home").lower()
    level = qp("level", "").lower()
    entity = qp("entity", "")

    if page == "home":
        page_home()
    elif page == "representations":
        page_representations(level, entity)
    elif page == "policies":
        page_policies(level, entity)
    elif page == "regulations":
        page_regulations(level, entity)
    else:
        st.warning("Unknown page. Use the ribbon above to navigate.")

if __name__ == "__main__":
    main()