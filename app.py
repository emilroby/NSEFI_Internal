# version: 1.3.4 — Tight vertical spacing: all content raised closer to the title
# app.py — NSEFI policy & regulatory monitoring dashboard (no map)

from __future__ import annotations
import base64
import calendar
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from zoneinfo import ZoneInfo  # Py 3.9+
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

# Central
CENTRAL_ALL = ["MoP", "MNRE", "MoF", "CEA", "CTUIL", "CERC", "Grid India"]
CENTRAL_FOR_POLICIES = ["MoP", "MNRE", "MoF"]

# States & UTs (alphabetical)
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
STATES_UTS = STATES + UTS

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
        q = DATA_DIR / f"{prefix_or_exact}.{ext}"
        if q.exists():
            return q
    for q in DATA_DIR.iterdir():
        if q.is_file() and q.stem.lower() == prefix_or_exact.lower():
            return q
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
        img = Image.open(src).convert("RGBA").resize((96, 96))
        pixels = [(r,g,b) for (r,g,b,a) in img.getdata() if a > 0]
        greens = [(r,g,b) for (r,g,b) in pixels if g > r and g > b and not (r>235 and g>235 and b>235)]
        pool = greens or [(r,g,b) for (r,g,b) in pixels if not (r>235 and g>235 and b>235)]
        r = int(sum(p[0] for p in pool)/len(pool)); g = int(sum(p[1] for p in pool)/len(pool)); b = int(sum(p[2] for p in pool)/len(pool))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#1b5e20"

BRAND        = pick_brand_green()
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
# Dummy updates generators
# ─────────────────────────────────────────────────────────────────────────────
def month_dates(year: int, month: int) -> List[str]:
    last = calendar.monthrange(year, month)[1]
    days = [d for d in (2,5,8,11,14,17,20,23,26,29) if d <= last]
    return [f"{year:04d}-{month:02d}-{d:02d}" for d in days]

def build_updates_for_group(names: List[str], label: str, year: int, month: int) -> Dict[str, List[Dict]]:
    ds = month_dates(year, month)
    out: Dict[str, List[Dict]] = {}
    for name in names:
        out[name] = [{"type": label, "title": f"{name}: example update {i+1}", "date": ds[i % len(ds)]} for i in range(len(ds))]
    return out

def aug_dates() -> List[str]:
    return ["2025-08-02","2025-08-05","2025-08-08","2025-08-11","2025-08-14",
            "2025-08-17","2025-08-20","2025-08-23","2025-08-26","2025-08-29"]

def make_aug_updates(name: str, tag: str) -> List[Dict]:
    ds = aug_dates()
    return [{"type": tag, "title": f"{name}: example update {i+1}", "date": ds[i]} for i in range(len(ds))]

STATE_UPDATES: Dict[str, List[Dict]]   = {s: make_aug_updates(s, "Regulatory") for s in STATES}
UT_UPDATES: Dict[str, List[Dict]]      = {u: make_aug_updates(u, "Regulatory") for u in UTS}
CENTRAL_UPDATES: Dict[str, List[Dict]] = {c: make_aug_updates(c, "Update")      for c in CENTRAL_ALL}

@st.cache_data
def get_previous_updates_maps(year: int, month: int) -> Tuple[Dict[str, List[Dict]], Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    centrals = build_updates_for_group(CENTRAL_ALL, "Update", year, month)
    states   = build_updates_for_group(STATES, "Regulatory", year, month)
    uts      = build_updates_for_group(UTS, "Regulatory", year, month)
    return centrals, states, uts

# ─────────────────────────────────────────────────────────────────────────────
# CSS — tightened spacing everywhere
# ─────────────────────────────────────────────────────────────────────────────
def css() -> str:
    return f"""
<style>
:root {{
  --brand: {BRAND};
  --brandDeep: {BRAND_DEEP};
  --brandHover: {BRAND_HOVER};
  --textDark: {TEXT_DARK};
  --navGap: 4px;            /* equal, minimal gap above & below navbar */
  --belowTitle: 4px;        /* tiny gap under title */
  --belowNavToLatest: 6px;  /* tiny gap under navbar before Latest heading */
}}
html, body, .stApp {{
  background:
    radial-gradient(1200px 700px at 12% -10%, #F3FAF6 0%, transparent 60%),
    radial-gradient(1200px 700px at 90% 0%, #E8F3EE 0%, transparent 65%),
    linear-gradient(180deg, #FFFFFF 0%, #F7FBF9 100%);
  font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}}
#MainMenu, footer, header {{ visibility: hidden; height: 0; }}
/* Pull entire page higher */
.block-container {{ padding-top: .02rem; overflow: visible; }}

/* Top bar — timestamp (left) and NSEFI logo (right) on the SAME LINE */
.topbar {{
  display:flex; align-items:center; justify-content:space-between;
  gap:10px; padding:0 2px; font-weight:700; color:#0F4237; font-size:14px;
  margin-bottom: 2px;   /* very small */
}}
.topbar .logo img {{
  height: 58px; width:auto; background: transparent !important;
  border-radius: 0 !important; padding: 0 !important; box-shadow: none !important;
}}

/* Title — single line, minimal gap below */
.titlewrap {{ margin: 0; padding: 0; }}
.pagetitle {{
  text-align:center; font-weight:900; color:var(--textDark);
  margin: 0 0 var(--belowTitle) 0; padding: 0;
  font-size: clamp(28px, 3.2vw, 40px);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}

/* Navbar — sits very close to the title and latest heading */
.navbar {{
  margin: var(--navGap) 0 var(--navGap) 0;
  background: var(--brand); border-radius: 12px; padding: 0;
  box-shadow: 0 1px 6px rgba(0,0,0,.12);
}}
.navbar > ul {{ list-style:none; margin:0; padding:0; display:flex; }}
.navbar > ul > li {{ position:relative; }}
.navbar a, .navbar span {{
  display:block; padding:9px 16px; color:#fff; text-decoration:none;
  font-weight:700; font-size:15px; white-space:nowrap;
}}
.navbar > ul > li:hover {{ background: var(--brandHover); border-radius:12px; }}

/* Dropdown (Policies & Regulations only) */
.navbar ul li .dropdown {{
  visibility:hidden; opacity:0; transition:opacity .12s ease-in-out;
  position:absolute; background:var(--brandHover); width:360px; top:100%; left:0;
  border-radius:0 0 10px 10px; box-shadow:0 6px 16px rgba(0,0,0,0.25);
  z-index:100001; padding:8px 10px;
}}
.navbar ul li:hover > .dropdown {{ visibility:visible; opacity:1; }}
.navbar .dropdown ul {{ list-style:none; margin:0; padding:0; max-height:230px; overflow:auto; }}
.menu-title {{ color:#e6fff5; font-size:12px; font-weight:800; margin:6px; }}
.menu-list li a {{ display:block; padding:7px 10px; border-radius:8px; color:#fff; font-size:14px; }}
.menu-list li a:hover {{ background:rgba(255,255,255,.12); }}

/* Headings & spacing */
.section-title {{ font-size:18px; font-weight:900; color:var(--textDark); margin: 0 0 6px 0; }}
.section-title.first {{ margin-top: var(--belowNavToLatest); }}  /* tiny gap below navbar */
.small-heading {{ font-size:16px; font-weight:900; color:var(--textDark); margin: 6px 0 6px; }}

/* Selects */
[data-baseweb="select"] label, .stSelectbox label {{ display:none !important; }}
.stSelectbox > div > div {{ border-radius:12px!important; }}

/* Updates ticker cards */
.updates {{
  position:relative; background:var(--brandDeep); color:#ffffff;
  border-radius:10px; padding:0; overflow:hidden;
  box-shadow:0 10px 22px rgba(16,40,32,0.06);
}}
.ticker  {{ position:relative; height:240px; overflow:hidden; }}
.track   {{ position:absolute; left:0; right:0; top:0; animation: moveUp 20s linear infinite; }}
.updates:hover .track {{ animation-play-state: paused; }}
.item {{ padding:12px 14px; font-size:14px; line-height:1.4; border-bottom:1px solid rgba(255,255,255,.08); }}
.tag  {{ font-size:11px; padding:2px 8px; border:1px solid rgba(255,255,255,.6); border-radius:999px; margin-right:8px; }}

@keyframes moveUp {{ 0% {{ transform:translateY(0); }} 100% {{ transform:translateY(-50%); }} }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
"""

# ─────────────────────────────────────────────────────────────────────────────
# Navbar (Representations direct; Policies/Regulations dropdowns)
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
    <li><a target="_self" href="?page=representations">Representations</a></li>
    <li><span>Policies</span>{dropdown_html("policies")}</li>
    <li><span>Regulations</span>{dropdown_html("regulations")}</li>
  </ul>
</nav>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Header (timestamp + logo on same line; title centered; navbar below)
# ─────────────────────────────────────────────────────────────────────────────
def header_bar():
    now = datetime.now(ZoneInfo("Asia/Kolkata")) if ZoneInfo else datetime.now()
    date_str = f"{now.strftime('%d')} - {now.strftime('%B').lower()} - {now.strftime('%Y')}"
    time_str = f"{now.strftime('%H:%M:%S')} IST"
    logo_html = f"<div class='logo'><img src='{NSEFI_URI}' alt='NSEFI'/></div>" if NSEFI_URI else ""

    # Top bar with date/time (left) + logo (right)
    st.markdown(
        f"""
        <div class="topbar">
          <div class="dt"><span id="live-date">{date_str}</span>
            <span style="opacity:.5">|</span>
            <span id="live-time">{time_str}</span></div>
          {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Title (single line)
    st.markdown(f"<div class='titlewrap'><h1 class='pagetitle'>{TITLE}</h1></div>", unsafe_allow_html=True)

    # Live clock script
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
              const day=parts.day, month=(parts.month||'').toLowerCase(), year=parts.year;
              const time = `${parts.hour}:${parts.minute}:${parts.second} IST`;
              const dEl = window.parent.document.getElementById('live-date');
              const tEl = window.parent.document.getElementById('live-time');
              if(dEl) dEl.textContent = `${day} - ${month} - ${year}`;
              if(tEl) tEl.textContent = time;
            }
            render(); setInterval(render, 1000);
          })();
        </script>""",
        height=0,
    )

    # Navbar (gaps handled in CSS)
    st.markdown(navbar_html(), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Updates (floating tickers)
# ─────────────────────────────────────────────────────────────────────────────
def ticker_html(items: List[Dict]) -> str:
    rows = "".join(
        f"<div class='item'><span class='tag'>{it['type']}</span>{it['title']} — <i>{it['date']}</i></div>"
        for it in items
    )
    return f"<div class='ticker'><div class='track'>{rows}{rows}</div></div>"

def compact_updates_box(placeholder: str, options: List[str], data_map: Dict[str, List[Dict]], key: str):
    choice = st.selectbox(placeholder, ["All"] + options, index=0, key=key, label_visibility="collapsed")
    if choice == "All":
        items = []
        for opt in options:
            items.extend(data_map.get(opt, [])[:4])
        if not items:
            items = [{"type":"Update","title":"No updates available","date":"—"}]
    else:
        items = data_map.get(choice, [{"type":"Update","title":f"No updates for {choice}","date":"—"}])
    st.markdown("<div class='updates'>" + ticker_html(items) + "</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# REPRESENTATIONS — Excel loader + page
# ─────────────────────────────────────────────────────────────────────────────
REP_XLS_CANDIDATES = [DATA_DIR / "representations.xlsx", DATA_DIR / "regulations.xlsx"]

def _first_existing(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None

def _pick(df_cols: List[str], *cands: str) -> Optional[str]:
    low = {c.lower().strip(): c for c in df_cols}
    for c in cands:
        k = c.lower().strip()
        if k in low:
            return low[k]
    for c in cands:
        k = c.lower().strip()
        for col in df_cols:
            if k in col.lower():
                return col
    return None

@st.cache_data
def load_representations_df() -> pd.DataFrame:
    path = _first_existing(REP_XLS_CANDIDATES)
    if not path:
        sample = pd.DataFrame([
            {"Issue Category":"Open Access","Issue Name":"Banking window","Subject Line":"Banking for RE OA",
             "Issue Number":"NSEFI/REP/2024/001","Jurisdiction":"Central","Target":"MoP","Date of Issue":"2024-08-07"},
            {"Issue Category":"Scheduling","Issue Name":"VRE dispatch","Subject Line":"VRE scheduling improvements",
             "Issue Number":"NSEFI/REP/2025/014","Jurisdiction":"Central","Target":"CERC","Date of Issue":"2025-03-11"},
            {"Issue Category":"Net Metering","Issue Name":"Caps clarification","Subject Line":"Rooftop caps",
             "Issue Number":"NSEFI/REP/2025/031","Jurisdiction":"State","Target":"Gujarat","Date of Issue":"2025-06-19"},
            {"Issue Category":"OA Charges","Issue Name":"Consult process","Subject Line":"OA charges consult",
             "Issue Number":"NSEFI/REP/2025/052","Jurisdiction":"State","Target":"Tamil Nadu","Date of Issue":"2025-08-19"},
        ])
        sample["Date of Issue"] = pd.to_datetime(sample["Date of Issue"], errors="coerce")
        sample["Year"] = sample["Date of Issue"].dt.year
        return sample

    df_raw = pd.read_excel(path)
    cols = [str(c) for c in df_raw.columns]

    c_cat   = _pick(cols, "Issue Category","Category")
    c_name  = _pick(cols, "Issue Name","Issue")
    c_sub   = _pick(cols, "Subject Line","Subject")
    c_no    = _pick(cols, "Issue Number","Ref No","Reference")
    c_jur   = _pick(cols, "Jurisdiction","Directed To","Issue is Directed To")
    c_tgt   = _pick(cols, "Target","Agency","Ministry","State/UT","Exact State or Central agency or ministry")
    c_date  = _pick(cols, "Date of Issue","Date","Issued On")

    df = pd.DataFrame()
    if c_cat:  df["Issue Category"] = df_raw[c_cat]
    if c_name: df["Issue Name"] = df_raw[c_name]
    if c_sub:  df["Subject Line"] = df_raw[c_sub]
    if c_no:   df["Issue Number"] = df_raw[c_no]
    if c_jur:  df["Jurisdiction"] = df_raw[c_jur]
    if c_tgt:  df["Target"] = df_raw[c_tgt]
    if c_date: df["Date of Issue"] = pd.to_datetime(df_raw[c_date], errors="coerce")
    else:      df["Date of Issue"] = pd.NaT

    df["Jurisdiction"] = (df.get("Jurisdiction") or pd.Series(dtype=str)).astype(str).str.strip().str.title()
    df.loc[~df["Jurisdiction"].isin(["Central","State"]), "Jurisdiction"] = pd.NA
    df["Target"] = df["Target"].astype(str).str.strip()
    df["Year"] = pd.to_datetime(df["Date of Issue"], errors="coerce").dt.year

    want = ["Issue Category","Issue Name","Subject Line","Issue Number",
            "Jurisdiction","Target","Date of Issue","Year"]
    for w in want:
        if w not in df.columns:
            df[w] = pd.NA
    df = df[want]
    return df

def page_representations():
    st.subheader("Representations")

    df = load_representations_df()
    if df.empty:
        st.info("No data available. Place an Excel at data/representations.xlsx.")
        return

    st.markdown("<div class='small-heading'>Filters — Representations</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        year = st.selectbox("Year", ["All", 2025, 2024], index=0, key="rep_year")
    with c2:
        scope = st.selectbox("Jurisdiction", ["All", "Central", "State"], index=0, key="rep_scope")
    with c3:
        state_pick = None
        if scope == "State":
            states_list = ["All"] + STATES_UTS
            state_pick = st.selectbox("State / UT", states_list, index=0, key="rep_state")

    fdf = df.copy()
    if year != "All":
        fdf = fdf[fdf["Year"] == int(year)]
    if scope != "All":
        fdf = fdf[fdf["Jurisdiction"] == scope]
        if scope == "State" and state_pick and state_pick != "All":
            fdf = fdf[fdf["Target"].str.strip().str.casefold() == state_pick.strip().casefold()]

    if "Date of Issue" in fdf.columns:
        fdf = fdf.sort_values("Date of Issue", ascending=False)

    show_cols = ["Issue Category","Issue Name","Subject Line","Issue Number",
                 "Jurisdiction","Target","Date of Issue"]
    fdf_disp = fdf[show_cols].copy()
    if "Date of Issue" in fdf_disp:
        fdf_disp["Date of Issue"] = pd.to_datetime(fdf_disp["Date of Issue"], errors="coerce").dt.date

    st.dataframe(fdf_disp, use_container_width=True, hide_index=True)
    st.download_button(
        "Download shown rows (CSV)",
        data=fdf_disp.to_csv(index=False).encode("utf-8"),
        file_name="representations_filtered.csv",
        mime="text/csv",
        use_container_width=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# Policies & Regulations — structured tables + optional Excel loaders
# ─────────────────────────────────────────────────────────────────────────────
POLICY_XLS = DATA_DIR / "policies.xlsx"
REG_XLS    = DATA_DIR / "regulations.xlsx"

def _load_policies_excel() -> Optional[pd.DataFrame]:
    if not POLICY_XLS.exists():
        return None
    df_raw = pd.read_excel(POLICY_XLS)
    cols = [str(c) for c in df_raw.columns]
    def P(*names): return _pick(cols, *names)
    c_jur = P("Jurisdiction","Level")
    c_ent = P("Entity","Target","Agency","Ministry","State/UT")
    c_name = P("Policy Name","Policy")
    c_year = P("Year")
    c_prev = P("Previous Policy Name","Previous Policy")
    c_land = P("Land Incentives","Land")
    c_other= P("Other State Incentives","Other Incentives","Other")
    c_tgt  = P("Targets","Target Capacity","RE Targets")
    c_inf  = P("Support Infrastructure","Infrastructure")
    c_fund = P("Support Funds","Funds","Finance")
    df = pd.DataFrame()
    def col(src, default=None): return df_raw[src] if src else default
    df["Jurisdiction"] = col(c_jur, "State")
    df["Entity"] = col(c_ent, "")
    df["Policy Name"] = col(c_name, "")
    df["Year"] = col(c_year, "")
    df["Previous Policy Name"] = col(c_prev, "")
    df["Land Incentives"] = col(c_land, "")
    df["Other State Incentives"] = col(c_other, "")
    df["Targets"] = col(c_tgt, "")
    df["Support Infrastructure"] = col(c_inf, "")
    df["Support Funds"] = col(c_fund, "")
    df["Jurisdiction"] = df["Jurisdiction"].astype(str).str.strip().str.title()
    df.loc[~df["Jurisdiction"].isin(["Central","State"]), "Jurisdiction"] = "State"
    df["Entity"] = df["Entity"].astype(str).str.strip()
    return df

def _load_regulations_excel() -> Optional[pd.DataFrame]:
    if not REG_XLS.exists():
        return None
    df_raw = pd.read_excel(REG_XLS)
    cols = [str(c) for c in df_raw.columns]
    def P(*names): return _pick(cols, *names)
    c_jur = P("Jurisdiction","Level")
    c_ent = P("Entity","Target","Agency","Ministry","State/UT")
    c_name= P("Regulation Name","Regulation")
    c_year= P("Year")
    c_cfa = P("Criteria for Allowing","Criteria")
    c_elig= P("Eligibility")
    c_chg = P("Charges to be Paid","Charges")
    c_bank= P("Banking")
    df = pd.DataFrame()
    def col(src, default=None): return df_raw[src] if src else default
    df["Jurisdiction"] = col(c_jur, "State")
    df["Entity"] = col(c_ent, "")
    df["Regulation Name"] = col(c_name, "")
    df["Year"] = col(c_year, "")
    df["Criteria for Allowing"] = col(c_cfa, "")
    df["Eligibility"] = col(c_elig, "")
    df["Charges to be Paid"] = col(c_chg, "")
    df["Banking"] = col(c_bank, "")
    df["Jurisdiction"] = df["Jurisdiction"].astype(str).str.strip().str.title()
    df.loc[~df["Jurisdiction"].isin(["Central","State"]), "Jurisdiction"] = "State"
    df["Entity"] = df["Entity"].astype(str).str.strip()
    return df

def page_policies(level: str, entity: str):
    st.subheader("Policies")
    pol_df = _load_policies_excel()

    if level == "central":
        if entity not in CENTRAL_FOR_POLICIES:
            st.info("Use the ribbon → Policies → Central to choose MNRE / MoP / MoF."); return
    elif level == "state":
        if entity not in STATES_UTS:
            st.info("Use the ribbon → Policies → State/UT to choose a region."); return
    else:
        st.info("Open the menu and choose Central or State/UT."); return

    row: Optional[pd.Series] = None
    if pol_df is not None:
        scope = "Central" if level == "central" else "State"
        cand = pol_df[(pol_df["Jurisdiction"] == scope) & (pol_df["Entity"].str.casefold() == entity.casefold())]
        if not cand.empty:
            row = cand.iloc[0]

    if row is None:
        if level == "central":
            row = pd.Series({
                "Policy Name": f"{entity} Renewable Energy Policy",
                "Year": 2025,
                "Previous Policy Name": f"{entity} RE Policy 2019",
                "Land Incentives": "Land pooling, concessional leases",
                "Other State Incentives": "Waiver of certain duties",
                "Targets": "10 GW by 2030",
                "Support Infrastructure": "Green corridors, transmission upgrades",
                "Support Funds": "Viability gap funding scheme",
            })
        else:
            row = pd.Series({
                "Policy Name": f"{entity} Renewable Energy Policy",
                "Year": 2025,
                "Previous Policy Name": f"{entity} RE Policy 2020",
                "Land Incentives": "Land at concessional rates",
                "Other State Incentives": "Stamp duty exemption, tax rebates",
                "Targets": "5 GW by 2030",
                "Support Infrastructure": "Solar parks, EV charging infra",
                "Support Funds": "State green energy corpus",
            })

    top = pd.DataFrame([{
        "Policy Name": row.get("Policy Name", ""),
        "Year": row.get("Year", "")
    }])
    st.dataframe(top, use_container_width=True, hide_index=True)

    details = pd.DataFrame([{
        "Previous Policy Name": row.get("Previous Policy Name", ""),
        "Land Incentives": row.get("Land Incentives", ""),
        "Other State Incentives": row.get("Other State Incentives", ""),
        "Targets": row.get("Targets", ""),
        "Support Infrastructure": row.get("Support Infrastructure", ""),
        "Support Funds": row.get("Support Funds", "")
    }])
    st.dataframe(details, use_container_width=True, hide_index=True)

def page_regulations(level: str, entity: str):
    st.subheader("Regulations")
    reg_df = _load_regulations_excel()

    if level == "central":
        if entity not in CENTRAL_ALL:
            st.info("Use the ribbon → Regulations → Central to choose a body."); return
    elif level == "state":
        if entity not in STATES_UTS:
            st.info("Use the ribbon → Regulations → State/UT to choose a region."); return
    else:
        st.info("Open the menu and choose Central or State/UT."); return

    row: Optional[pd.Series] = None
    if reg_df is not None:
        scope = "Central" if level == "central" else "State"
        cand = reg_df[(reg_df["Jurisdiction"] == scope) & (reg_df["Entity"].str.casefold() == entity.casefold())]
        if not cand.empty:
            row = cand.iloc[0]

    if row is None:
        row = pd.Series({
            "Regulation Name": f"{entity} Green Energy Open Access Regulation",
            "Year": 2025,
            "Criteria for Allowing": "Consumers >100 kW eligible",
            "Eligibility": "All HT and EHT consumers",
            "Charges to be Paid": "Wheeling, transmission, CSS",
            "Banking": "Allowed, annual settlement",
        })

    top = pd.DataFrame([{
        "Regulation Name": row.get("Regulation Name", ""),
        "Year": row.get("Year", "")
    }])
    st.dataframe(top, use_container_width=True, hide_index=True)

    details = pd.DataFrame([{
        "Criteria for Allowing": row.get("Criteria for Allowing", ""),
        "Eligibility": row.get("Eligibility", ""),
        "Charges to be Paid": row.get("Charges to be Paid", ""),
        "Banking": row.get("Banking", "")
    }])
    st.dataframe(details, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# Home (Latest first, then Previous updates)
# ─────────────────────────────────────────────────────────────────────────────
def previous_updates_area():
    st.markdown("<div class='section-title'>Previous updates</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        y = st.selectbox("Choose Year", ["Choose an option", "2025", "2024"], index=0, key="prev_year")
    with c2:
        m = st.selectbox("Choose Month", ["Choose an option"] + list(calendar.month_name[1:]), index=0, key="prev_month")

    if y != "Choose an option" and m != "Choose an option":
        year_val = int(y)
        month_num = list(calendar.month_name).index(m)
        central_map, state_map, ut_map = get_previous_updates_maps(year_val, month_num)

        st.markdown(f"<div class='section-title'>Previous updates — {m} {year_val}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div class='small-heading'>Central</div>", unsafe_allow_html=True)
            compact_updates_box("Choose central body", CENTRAL_ALL, central_map, key=f"prev_central_{year_val}_{month_num}")
        with c2:
            st.markdown("<div class='small-heading'>States</div>", unsafe_allow_html=True)
            compact_updates_box("Choose state", STATES, state_map, key=f"prev_states_{year_val}_{month_num}")
        with c3:
            st.markdown("<div class='small-heading'>UTs</div>", unsafe_allow_html=True)
            compact_updates_box("Choose UT", UTS, ut_map, key=f"prev_uts_{year_val}_{month_num}")

def page_home():
    # Latest updates (sits immediately under navbar with minimal gap)
    st.markdown("<div class='section-title first'>Latest updates — August 2025</div>", unsafe_allow_html=True)

    # Latest updates three columns
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='small-heading'>Central</div>", unsafe_allow_html=True)
        compact_updates_box("Choose central body", CENTRAL_ALL, CENTRAL_UPDATES, key="central_sel")
    with c2:
        st.markdown("<div class='small-heading'>States</div>", unsafe_allow_html=True)
        compact_updates_box("Choose state", STATES, STATE_UPDATES, key="state_sel")
    with c3:
        st.markdown("<div class='small-heading'>UTs</div>", unsafe_allow_html=True)
        compact_updates_box("Choose UT", UTS, UT_UPDATES, key="ut_sel")

    # Previous updates below
    previous_updates_area()

# ─────────────────────────────────────────────────────────────────────────────
# App entry
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
        page_representations()
    elif page == "policies":
        page_policies(level, entity)
    elif page == "regulations":
        page_regulations(level, entity)
    else:
        st.warning("Unknown page. Use the ribbon above to navigate.")

if __name__ == "__main__":
    main()
