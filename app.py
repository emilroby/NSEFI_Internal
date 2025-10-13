# app.py
# NSEFI dashboard — fixed UI with FLOATING (auto-scroll) update panels that pause on hover and on user scroll

from __future__ import annotations
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st

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

# Canonical lists
CENTRAL_ALL = [
    "MoP", "MNRE", "MoF", "CEA", "CTUIL", "CERC", "Grid India"
]

STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa",
    "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
    "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
    "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
    "Uttar Pradesh","Uttarakhand","West Bengal"
]

UTS = [
    "Andaman and Nicobar Islands","Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu","Delhi",
    "Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"
]

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────
def ist_now() -> datetime:
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(tz=ist)

def find_asset(prefix_or_exact: str) -> Path | None:
    if not DATA_DIR.exists():
        return None
    p = DATA_DIR / prefix_or_exact
    if p.exists():
        return p
    for ext in ("png", "jpg", "jpeg", "svg", "webp"):
        q = DATA_DIR / f"{prefix_or_exact}.{ext}"
        if q.exists():
            return q
    for q in DATA_DIR.iterdir():
        if q.is_file() and q.stem.lower() == prefix_or_exact.lower():
            return q
    return None

def image_to_data_uri(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    ext = path.suffix.lower()
    if ext == ".svg":
        return f"data:image/svg+xml;utf8,{path.read_text(encoding='utf-8')}"
    mime = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg",".jpeg") else "image/webp")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

# Try multiple names; fall back to hosted logo
NSEFI_URI = image_to_data_uri(find_asset("12th_year_anniversary_logo_transparent")) \
            or image_to_data_uri(find_asset("NSEFI")) \
            or image_to_data_uri(find_asset("MNRE")) \
            or "https://nsefi.in/wp-content/uploads/2023/02/NSEFI-Logo-1.png"

# ─────────────────────────────────────────────────────────────────────────────
# CSS (fixed appearance)
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
.topbar .brand img {{ height: 48px; width:auto; }}

.pagetitle {{
  font-weight:900; color:#1e2a2a; 
  font-size: clamp(28px, 4.2vw, 48px);
  margin: 0.4rem 0 1.0rem 0;
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

/* floating card (mouse scroll + auto float) */
.fcard {{
  background:#0F4237; color:#fff; border-radius:14px; 
  box-shadow:0 14px 22px rgba(16,40,32,0.18);
  padding:0; overflow:hidden; position:relative;
  max-height: 400px;  /* floating window height */
}}
.fcard-body {{
  padding:0; max-height:400px; overflow-y:auto; scroll-behavior: smooth;
}}
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

.fcard {{ margin-bottom: 18px; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap" rel="stylesheet">
"""

# JS: auto-scroll each .fcard-body (float). Pause on hover or user scroll; resume after idle.
def floating_js() -> str:
    return """
<script>
(function(){
  function init(){
    const speedPxPerSec = 26;           // float speed
    const resumeDelayMs = 6000;          // resume after idle
    const raf = window.requestAnimationFrame || (fn=>setTimeout(fn,16));

    document.querySelectorAll(".fcard-body").forEach((el) => {
      let pausedHover = false;
      let pausedUser  = false;
      let lastUserTs  = 0;

      function pauseUser(){ pausedUser = true; lastUserTs = Date.now(); }
      function maybeResume(){
        if (pausedUser && (Date.now() - lastUserTs) > resumeDelayMs){
          pausedUser = false;
        }
      }
      // Pause conditions
      el.addEventListener("mouseenter", ()=> pausedHover = true);
      el.addEventListener("mouseleave", ()=> pausedHover = false);
      ["wheel","touchstart","touchmove","scroll","keydown"].forEach(evt=>{
        el.addEventListener(evt, pauseUser, {passive:true});
      });

      // Auto float loop
      (function tick(){
        maybeResume();
        if (!pausedHover && !pausedUser){
          const step = speedPxPerSec / 60.0; // per frame (approx)
          el.scrollTop += step;
          if (el.scrollTop + el.clientHeight >= el.scrollHeight - 1){
            el.scrollTop = 0; // loop
          }
        }
        raf(tick);
      })();
    });
  }
  // Run when DOM is ready; Streamlit reruns, so slight delay is safer
  const start = () => setTimeout(init, 50);
  if (document.readyState === "complete") start();
  else window.addEventListener("load", start);
})();
</script>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Navbar with flyouts
# ─────────────────────────────────────────────────────────────────────────────
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
    now = ist_now()
    date_str = f"{now.strftime('%d')} - {now.strftime('%B').lower()} - {now.strftime('%Y')}"
    time_str = f"{now.strftime('%H:%M:%S')} IST"

    st.markdown(
        f"""
        <div class="topbar">
          <div class="ts">{date_str} &nbsp;|&nbsp; {time_str}</div>
          <div class="brand">{f'<img alt="NSEFI logo" src="{NSEFI_URI}"/>' if NSEFI_URI else 'NSEFI'}</div>
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

def _row_html(date_iso: str, title: str, url: str, tag: str = "Update") -> str:
    return f"""
    <div class="urow">
      {_badge(date_iso)}
      <div class="row-main">
        <div class="row-title"><a href="{url}" target="_blank" rel="noopener">{title}</a></div>
        <div class="row-meta"><span class="pill">{tag}</span></div>
      </div>
    </div>
    """

def _dummy_updates() -> tuple[list[dict], list[dict], list[dict]]:
    # Placeholder sample items (keeps UI shape stable)
    return (
        [
            {"date":"2025-10-12","title":"CERC: example regulation update 1","url":"#","type":"Regulatory"},
            {"date":"2025-10-09","title":"MNRE: example policy circular","url":"#","type":"Update"},
            {"date":"2025-10-08","title":"CTUIL: What’s New — sample note","url":"#","type":"Update"},
            {"date":"2025-10-05","title":"MoP: example memo","url":"#","type":"Update"},
            {"date":"2025-10-02","title":"CEA: example guideline","url":"#","type":"Update"},
        ],
        [
            {"date":"2025-10-11","title":"Chhattisgarh: example update","url":"#","type":"Regulatory"},
            {"date":"2025-10-09","title":"Goa: example policy bulletin","url":"#","type":"Update"},
            {"date":"2025-10-06","title":"Rajasthan: example notice","url":"#","type":"Update"},
        ],
        [
            {"date":"2025-10-11","title":"Chandigarh: example order","url":"#","type":"Regulatory"},
            {"date":"2025-10-07","title":"Delhi: example circular","url":"#","type":"Update"},
            {"date":"2025-10-03","title":"J&K: sample update","url":"#","type":"Update"},
        ],
    )

def _panel_html(items: list[dict], body_id: str) -> str:
    """Floating card with mouse scroll + auto-scroll script (no arrows)."""
    if not items:
        body = "<div class='urow'><div>No updates found.</div></div>"
    else:
        body = "".join(_row_html(it.get("date",""), it.get("title",""), it.get("url","#"), it.get("type","Update")) for it in items)
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
    central_items, state_items, ut_items = _dummy_updates()

    now = ist_now()
    st.markdown(f"<div class='section-title'>Latest updates — {now.strftime('%B')} {now.year}</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.markdown("<div class='col-heading'>Central</div>", unsafe_allow_html=True)
        st.selectbox("Central filter", ["All"] + CENTRAL_ALL, index=0, key="central_filter", label_visibility="collapsed")
        st.markdown(_panel_html(central_items, "body-central"), unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='col-heading'>States</div>", unsafe_allow_html=True)
        st.selectbox("State filter", ["All"] + STATES, index=0, key="state_filter", label_visibility="collapsed")
        st.markdown(_panel_html(state_items, "body-states"), unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='col-heading'>UTs</div>", unsafe_allow_html=True)
        st.selectbox("UT filter", ["All"] + UTS, index=0, key="ut_filter", label_visibility="collapsed")
        st.markdown(_panel_html(ut_items, "body-uts"), unsafe_allow_html=True)

    # Inject floating JS once panels exist
    st.markdown(floating_js(), unsafe_allow_html=True)

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

if __name__ == "__main__":
    main()
