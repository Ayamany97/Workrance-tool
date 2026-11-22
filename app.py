"""Workrance — متابعة مخالفات السائقين"""

import streamlit as st
import pandas as pd
import urllib.parse
import uuid
import io
import httpx as _hx
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

RIYADH = ZoneInfo("Asia/Riyadh")

# ══════════════════════════════════════════════════════════
# SVG ICONS
# ══════════════════════════════════════════════════════════
def ico(name, sz=16, col="currentColor"):
    _i = {
        "truck":    '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
        "car":      '<path d="M5 17H3a2 2 0 0 1-2-2V9l3-6h10l3 6v6a2 2 0 0 1-2 2h-2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
        "phone":    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 11.19 19 19.5 19.5 0 0 1 3 10.81 19.79 19.79 0 0 1 .14 1.26 2 2 0 0 1 2.14 0h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L6.09 7.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
        "bell":     '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
        "check":    '<polyline points="20 6 9 17 4 12"/>',
        "x":        '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
        "check-c":  '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "x-c":      '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
        "alert":    '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        "clock":    '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        "dollar":   '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        "send":     '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
        "search":   '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
        "refresh":  '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
        "users":    '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
        "chart":    '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/>',
        "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
        "upload":   '<polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>',
        "download": '<polyline points="8 17 12 21 16 17"/><line x1="12" y1="21" x2="12" y2="9"/><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"/>',
        "plus":     '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
        "board":    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/>',
        "save":     '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
        "msg":      '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        "user":     '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
        "globe":    '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
        "no-phone": '<line x1="1" y1="1" x2="23" y2="23"/><path d="M16.5 16.5L19 19a2 2 0 0 1-2 2A19.79 19.79 0 0 1 8.37 17.93 19.5 19.5 0 0 1 3.07 9.8a19.79 19.79 0 0 1-2.93-8.72A2 2 0 0 1 2.14 0h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L6.09 7.91"/>',
        "file":     '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        "hash":     '<line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>',
        "chevron":  '<polyline points="9 18 15 12 9 6"/>',
        "hourglass":'<path d="M5 2h14M5 22h14"/><path d="M17 2v5l-5 5 5 5v5M7 2v5l5 5-5 5v5"/>',
        "back":     '<polyline points="15 18 9 12 15 6"/>',
        "eye":      '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
        "confirm":  '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    }
    inner = _i.get(name, '<circle cx="12" cy="12" r="3"/>')
    return (f'<span style="display:inline-flex;align-items:center;vertical-align:middle">'
            f'<svg width="{sz}" height="{sz}" viewBox="0 0 24 24" fill="none" stroke="{col}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner}</svg></span>')

WA_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-left:6px;flex-shrink:0"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347zm-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741 1.456 1.282-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26C2.98 6.335 7.416 1.9 12.869 1.9c2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884zm8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'

st.set_page_config(page_title="Workrance", page_icon="🚛", layout="wide",
                   initial_sidebar_state="auto")

# ══════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════
st.markdown("""<style>

/* ── BASE ── */
.stApp { direction:rtl; background:#0a0f1e; }
.stTextArea textarea, .stTextInput input { direction:rtl; font-family:'Segoe UI',Tahoma,Arial,sans-serif; }
.stTextArea textarea { line-height:1.85; font-size:14px; }
.block-container { padding-top:4rem!important; padding-bottom:2rem!important; }
header[data-testid="stHeader"] { background:rgba(10,15,30,0.95)!important; backdrop-filter:blur(8px); border-bottom:1px solid #1e293b; }

/* ── PAGE HEADER ── */
.pg-hdr {
    display:flex; align-items:center; gap:10px;
    font-size:22px; font-weight:800; color:#f1f5f9;
    margin-bottom:14px; padding-bottom:12px;
    border-bottom:1px solid #1e293b;
}
.pg-hdr svg { flex-shrink:0; }

/* ── STAT STRIP ── */
.stat-strip {
    display:flex; gap:8px; margin-bottom:14px;
    overflow-x:auto; padding-bottom:4px;
}
.stat-strip::-webkit-scrollbar { height:3px; }
.stat-strip::-webkit-scrollbar-thumb { background:#1e293b; border-radius:2px; }
.stat-card {
    flex:1; min-width:72px; background:#111827;
    border:1px solid #1e293b; border-radius:12px;
    padding:12px 8px 10px; text-align:center;
}
.stat-num { font-size:26px; font-weight:800; line-height:1.1; }
.stat-lbl {
    font-size:11px; color:#64748b; margin-top:5px;
    display:flex; align-items:center; justify-content:center; gap:4px; white-space:nowrap;
}

/* ── DRIVER CARDS ── */
.drv-card {
    background:#111827; border-radius:14px; padding:13px 14px; margin:4px 0;
    border-right:5px solid #1e293b; display:flex; justify-content:space-between;
    align-items:center; gap:10px; box-shadow:0 2px 6px rgba(0,0,0,.25);
    transition:background .15s;
}
.drv-card:hover { background:#161f35; }
.drv-sel { background:#1a2744!important; border-right-width:6px!important; }
.dc-info { flex:1; min-width:0; }
.dc-name { font-size:14px; font-weight:700; color:#f1f5f9; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; display:block; }
.dc-sub  { font-size:11px; color:#475569; margin-top:4px; display:flex; align-items:center; gap:5px; }
.dc-note { font-size:10px; color:#64748b; margin-top:3px; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; font-style:italic; }
.dc-side { text-align:left; flex-shrink:0; display:flex; flex-direction:column; align-items:flex-end; gap:5px; }
.dc-badge { display:inline-block; padding:3px 9px; border-radius:20px; font-size:11px; font-weight:700; white-space:nowrap; }
.dc-amt  { font-size:11px; color:#64748b; font-weight:600; }

/* status borders */
.drv-new{border-right-color:#ef4444}.drv-reminder{border-right-color:#f97316}
.drv-check{border-right-color:#eab308}.drv-pending{border-right-color:#f97316}
.drv-partial{border-right-color:#a855f7}.drv-notified{border-right-color:#3b82f6}
.drv-done{border-right-color:#22c55e}.drv-no_contact,.drv-no_phone,.drv-no_wa{border-right-color:#334155}

/* badges */
.b-new{background:rgba(239,68,68,.15);color:#f87171}
.b-reminder{background:rgba(249,115,22,.15);color:#fb923c}
.b-check{background:rgba(234,179,8,.15);color:#fbbf24}
.b-pending{background:rgba(249,115,22,.15);color:#fb923c}
.b-partial{background:rgba(168,85,247,.15);color:#c084fc}
.b-notified{background:rgba(59,130,246,.15);color:#60a5fa}
.b-done{background:rgba(34,197,94,.15);color:#4ade80}
.b-no_contact,.b-no_phone,.b-no_wa{background:rgba(51,65,85,.4);color:#64748b}

/* ── DRIVER OPEN BUTTON ── */
.drv-open > div > button {
    background:rgba(96,165,250,.06)!important;
    border:1px solid rgba(96,165,250,.12)!important;
    border-radius:0 0 12px 12px!important;
    color:#475569!important; font-size:11px!important;
    min-height:24px!important; height:24px!important;
    margin-top:-2px!important; padding:0!important;
    letter-spacing:.4px!important;
}
.drv-open > div > button:hover {
    background:rgba(96,165,250,.14)!important;
    color:#93c5fd!important;
}

/* ── DRIVER DETAIL HEADER ── */
.drv-hdr {
    background:#111827; border:1px solid #1e293b; border-radius:14px;
    padding:14px 16px; margin-bottom:14px;
    display:flex; justify-content:space-between; align-items:flex-start; gap:12px;
}
.dh-name { font-size:18px; font-weight:800; color:#f1f5f9; display:block; }
.dh-meta { margin-top:6px; display:flex; flex-wrap:wrap; gap:12px; }
.dh-pill { display:flex; align-items:center; gap:5px; font-size:12px; color:#94a3b8; }

/* ── VIOLATION ROWS ── */
.viol-row {
    padding:10px 13px; margin:4px 0; border-radius:10px;
    background:#111827; border-right:3px solid #334155;
    font-size:13px; line-height:1.6;
    display:flex; align-items:flex-start; gap:10px;
}
.viol-icon { flex-shrink:0; margin-top:1px; }
.viol-body { flex:1; }
.viol-paid  { border-right-color:#22c55e; }
.viol-unpaid{ border-right-color:#ef4444; }

/* ── BUTTONS ── */
.stButton > button {
    min-height:44px; font-family:'Segoe UI',Tahoma,Arial,sans-serif;
    border-radius:10px!important; font-weight:600!important; font-size:14px!important;
    touch-action:manipulation; -webkit-tap-highlight-color:transparent;
    transition:all .15s!important;
}
.stButton > button:hover  { opacity:.88!important; transform:translateY(-1px)!important; }
.stButton > button:active { opacity:.72!important; transform:scale(.97)!important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#0d1626,#0a0f1e)!important;
    border-left:1px solid #1e293b;
}
@media (min-width:768px) {
    section[data-testid="stSidebar"] { min-width:220px!important; max-width:220px!important; }
}
section[data-testid="stSidebar"] > div:first-child { padding:0.9rem 0.75rem!important; }
[data-testid="stSidebar"] .stRadio > div { gap:2px!important; }
[data-testid="stSidebar"] .stRadio label { border-radius:8px!important; padding:10px 14px!important; font-size:14px!important; transition:background .15s!important; }
[data-testid="stSidebar"] .stRadio label:hover { background:rgba(96,165,250,.1)!important; }
[data-testid="stSidebar"] .stCheckbox label { font-size:13px!important; }

/* ── SIDEBAR COLLAPSE / CLOSE BUTTON ── */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapseButton"] button:hover {
    color:#94a3b8!important; opacity:1!important;
    background:rgba(148,163,184,.1)!important;
    border-radius:8px!important; border:1px solid #1e293b!important;
}
[data-testid="collapsedControl"] {
    background:rgba(13,22,38,.95)!important;
    border:1px solid #1e293b!important;
    border-radius:0 10px 10px 0!important;
    padding:4px!important;
}
[data-testid="collapsedControl"] button {
    color:#94a3b8!important; opacity:1!important;
}

/* ── METRICS (payments/reports page) ── */
div[data-testid="metric-container"] {
    background:linear-gradient(145deg,#1a2744,#111827);
    border:1px solid #1e3a5f; border-radius:14px; padding:14px 16px;
    box-shadow:0 4px 12px rgba(0,0,0,.3);
}
div[data-testid="stMetricLabel"] { font-size:11px!important;color:#64748b!important;text-transform:uppercase;letter-spacing:.8px;font-weight:600; }
div[data-testid="stMetricValue"] { font-size:26px!important;font-weight:800!important;color:#f1f5f9!important; }

/* ── RESPONSIVE TABLET ≤1100px ── */
@media screen and (max-width:1100px) {
    .block-container { padding-left:.6rem!important; padding-right:.6rem!important; }
}
/* ── RESPONSIVE MOBILE ≤768px ── */
@media screen and (max-width:768px) {
    /* columns that are NOT viol-action keep stacking; viol-action stays row */
    [data-testid="stHorizontalBlock"] { flex-direction:column!important; gap:.4rem!important; }
    [data-testid="stColumn"] { width:100%!important; min-width:100%!important; flex:unset!important; }
    .viol-act-row [data-testid="stHorizontalBlock"] { flex-direction:row!important; gap:4px!important; }
    .viol-act-row [data-testid="stColumn"]:first-child { flex:1!important; width:auto!important; min-width:0!important; }
    .viol-act-row [data-testid="stColumn"]:not(:first-child) { width:44px!important; min-width:44px!important; flex:unset!important; }
    input,textarea,select { font-size:16px!important; -webkit-text-size-adjust:100%; }
    .stButton > button { min-height:52px!important; font-size:16px!important; border-radius:12px!important; }
    .drv-card { padding:14px!important; }
    .dc-name { font-size:15px!important; }
    .stat-num { font-size:22px!important; }
    .block-container { padding:.5rem!important; padding-top:3.5rem!important; }
    button[data-baseweb="tab"] { font-size:12px!important; padding:.45rem .5rem!important; }
    section[data-testid="stSidebar"] { min-width:min(88vw,300px)!important; }
    hr { margin:.5rem 0!important; }
    .pg-hdr { font-size:18px!important; }
}
@media screen and (max-width:480px) {
    .block-container { padding:.35rem!important; padding-top:3rem!important; }
    .stat-card { min-width:60px; padding:10px 6px 8px; }
}

</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# HTTP — direct PostgREST
# ══════════════════════════════════════════════════════════
def _base(): return st.secrets["SUPABASE_URL"]

def _h(extra=None):
    k = st.secrets["SUPABASE_KEY"]
    h = {"apikey":k,"Authorization":f"Bearer {k}","Content-Type":"application/json"}
    if extra: h.update(extra)
    return h

def _rh():
    return _h({"Range-Unit":"items","Range":"0-9999"})

# ══════════════════════════════════════════════════════════
# CACHE & DATA LOAD
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def _viols():
    try:
        r = _hx.get(f"{_base()}/rest/v1/violations?select=*", headers=_rh(), timeout=30)
        d = r.json() if r.status_code==200 else []
        return pd.DataFrame(d) if d else pd.DataFrame()
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=60)
def _pays():
    try:
        r = _hx.get(f"{_base()}/rest/v1/payments?select=*", headers=_rh(), timeout=30)
        d = r.json() if r.status_code==200 else []
        return pd.DataFrame(d) if d else pd.DataFrame()
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=60)
def _notifs():
    try:
        r = _hx.get(f"{_base()}/rest/v1/notifications?select=*", headers=_rh(), timeout=30)
        d = r.json() if r.status_code==200 else []
        return pd.DataFrame(d) if d else pd.DataFrame()
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=60)
def _rems():
    try:
        r = _hx.get(f"{_base()}/rest/v1/reminders?select=*", headers=_rh(), timeout=30)
        d = r.json() if r.status_code==200 else []
        return {f"{x['phone']}_{x['plate']}":x for x in (d or [])}
    except Exception: return {}

def bust():
    _viols.clear(); _pays.clear(); _notifs.clear(); _rems.clear()
    build_drivers.clear()

# ══════════════════════════════════════════════════════════
# DATA — WRITE
# ══════════════════════════════════════════════════════════
def upd_status(name, phone, plate, status, notes="", cdate=""):
    d = {"status":status,"updated_at":datetime.now(RIYADH).isoformat()}
    if cdate: d["contact_date"] = cdate
    if notes: d["my_notes"] = notes
    _hx.patch(f"{_base()}/rest/v1/violations",
              params={"driver_name":f"eq.{name}","phone":f"eq.{phone}","plate":f"eq.{plate}"},
              json=d, headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def log_notif(name, phone, plate, ntype, sent_by, notes=""):
    _hx.post(f"{_base()}/rest/v1/notifications",
             json={"driver_name":name,"phone":phone,"plate":plate,
                   "notification_type":ntype,"sent_by":sent_by,
                   "sent_at":datetime.now(RIYADH).isoformat(),"notes":notes},
             headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def upsert_rem(phone, plate, name, rdate, note, by):
    _hx.post(f"{_base()}/rest/v1/reminders",
             json={"phone":phone,"plate":plate,"driver_name":name,
                   "reminder_date":rdate.isoformat(),"note":note,
                   "created_by":by,"is_done":False},
             headers=_h({"Prefer":"resolution=merge-duplicates,return=minimal"}), timeout=30)
    bust()

def mark_rem_done(phone, plate):
    _hx.patch(f"{_base()}/rest/v1/reminders",
              params={"phone":f"eq.{phone}","plate":f"eq.{plate}"},
              json={"is_done":True},
              headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def upd_violation(vid, status, notes=""):
    d = {"status":status,"updated_at":datetime.now(RIYADH).isoformat()}
    if notes: d["my_notes"] = notes
    _hx.patch(f"{_base()}/rest/v1/violations",
              params={"violation_id":f"eq.{vid}"},
              json=d, headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def del_violation(vid):
    _hx.delete(f"{_base()}/rest/v1/violations",
               params={"violation_id":f"eq.{vid}"},
               headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def add_payment(vid, name, phone, plate, amt, ptype, method,
                receipt_url, receipt_ref, collector, other_col, verif, pdate, notes):
    _hx.post(f"{_base()}/rest/v1/payments",
             json={"violation_id":vid,"driver_name":name,"phone":phone,"plate":plate,
                   "amount_paid":amt,"payment_type":ptype,"payment_method":method,
                   "receipt_url":receipt_url,"receipt_ref":receipt_ref,
                   "collected_by":collector,"other_collector":other_col,
                   "verification_status":verif,"payment_date":pdate,"notes":notes},
             headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def confirm_pay(pid):
    _hx.patch(f"{_base()}/rest/v1/payments",
              params={"id":f"eq.{pid}"},
              json={"verification_status":"مؤكد"},
              headers=_h({"Prefer":"return=minimal"}), timeout=30)
    bust()

def upload_receipt(f, pid):
    try:
        ext = f.name.split(".")[-1]
        path = f"receipts/{pid}.{ext}"
        r = _hx.post(f"{_base()}/storage/v1/object/{path}",
                     content=f.read(),
                     headers={"apikey":st.secrets["SUPABASE_KEY"],
                              "Authorization":f"Bearer {st.secrets['SUPABASE_KEY']}",
                              "Content-Type":f.type,"x-upsert":"true"},
                     timeout=60)
        if r.status_code in (200,201):
            return f"{_base()}/storage/v1/object/public/{path}"
        return ""
    except Exception as e:
        st.warning(f"تعذّر رفع الإيصال: {e}")
        return ""

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════
def cp(p):
    if not p or (isinstance(p,float) and pd.isna(p)): return ""
    return str(p).strip().split(".")[0].replace(" ","").replace("-","")

def wa_num(p):
    s = cp(p)
    if not s: return None
    if s.startswith("00966"): return s[2:]
    if s.startswith("966"):   return s
    if s.startswith("05"):    return "966"+s[1:]
    if s.startswith("5") and len(s)==9: return "966"+s
    return "966"+s

def famt(x):
    try:
        v=float(x); return f"{int(v):,}" if v==int(v) else f"{v:,.2f}"
    except: return "0"

def fdt(d):
    try:    return pd.to_datetime(d).strftime("%d-%m-%Y")
    except: return str(d).strip() if d and str(d) not in ("nan","None","") else ""

def jlbl(j):
    if not j or str(j) in ("nan","None",""): return "مخالفة"
    j=str(j)
    if "مرور"  in j: return "مرورية"
    if "نقل"   in j: return "نقل"
    if "بلد"   in j: return "بلدية"
    if "جمارك" in j: return "جمركية"
    if "قضائ"  in j: return "قضائية"
    if "أوزان" in j or "اوزان" in j: return "أوزان"
    return j

def wa_link(phone, msg):
    n = wa_num(phone)
    if not n: return None
    return f"https://wa.me/{n}?text={urllib.parse.quote(msg)}"

def wa_btn(url, label, color):
    if not url: return
    st.components.v1.html(f"""
    <style>
    .wb{{width:100%;padding:13px 0;background:{color};color:white;border:none;
    border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;
    font-family:'Segoe UI',Arial;display:flex;align-items:center;justify-content:center;gap:7px;
    touch-action:manipulation;-webkit-tap-highlight-color:transparent;transition:opacity .15s,transform .1s}}
    .wb:hover{{opacity:.87}}
    .wb:active{{opacity:.74;transform:scale(0.97)}}
    @media(max-width:768px){{.wb{{padding:17px 0;font-size:17px;border-radius:12px}}}}
    </style>
    <button class="wb" onclick="window.open('{url}','whatsapp_workrance')">{label}{WA_SVG}</button>
    """, height=56)

def now_sa_str():
    n = datetime.now(RIYADH)
    return n.strftime("%d-%m-%Y"), n.strftime("%H:%M"), n.strftime("%d-%m-%Y %H:%M")

def fmt_sent_at(s):
    try:    return datetime.fromisoformat(str(s)).astimezone(RIYADH).strftime("%d-%m-%Y %H:%M")
    except: return str(s)[:16]

# ══════════════════════════════════════════════════════════
# STATUS
# ══════════════════════════════════════════════════════════
def get_sk(statuses):
    vals=[str(s).strip() for s in statuses if s and str(s).strip() not in ("","nan","None")]
    if not vals: return "new"
    if any("مدفوع جزئي" in v or "جزئي" in v for v in vals): return "partial"
    if any("تم الدفع" in v or "مدفوع" in v for v in vals) and all(
        "مدفوع" in v or v.strip()=="تم" for v in vals): return "done"
    if any(v.strip()=="تم" for v in vals): return "done"
    if any("بانتظار تأكيد" in v for v in vals): return "partial"
    if any("تم التبليغ" in v or "تم التبيلغ" in v for v in vals): return "notified"
    if any("تشيك" in v for v in vals): return "check"
    if any("معلق" in v for v in vals): return "pending"
    if any("لم يتم" in v for v in vals): return "new"
    if any("لا داعي" in v or "لاداعي" in v for v in vals): return "no_contact"
    if any("بلا رقم" in v or "لا يوجد رقم" in v or "لايوجد رقم" in v for v in vals): return "no_phone"
    if any("واتساب" in v and ("لا" in v or "بلا" in v or "لايوجد" in v) for v in vals): return "no_wa"
    return "new"

SL = {
    "new":"جديد","reminder":"تذكير اليوم","check":"تشيك",
    "pending":"معلق","partial":"دفع جزئي","notified":"تم التبليغ",
    "done":"تم","no_contact":"لا داعي","no_phone":"بلا رقم","no_wa":"بلا واتساب",
}
SL_SHORT = {
    "new":"جديد","reminder":"تذكير","check":"تشيك","pending":"معلق",
    "partial":"جزئي","notified":"تبليغ","done":"تم",
    "no_contact":"لا داعي","no_phone":"بلا رقم","no_wa":"بلا واتساب",
}
PR = {"reminder":0,"new":1,"check":2,"pending":3,"partial":4,
      "notified":5,"done":6,"no_contact":7,"no_phone":8,"no_wa":9}

STAT_CFG = [
    ("new",      "#ef4444", "alert",     "جديد"),
    ("reminder", "#f97316", "bell",      "تذكير"),
    ("check",    "#eab308", "clock",     "تشيك"),
    ("pending",  "#f97316", "hourglass", "معلق"),
    ("notified", "#3b82f6", "send",      "تبليغ"),
    ("done",     "#22c55e", "check-c",   "تم"),
]

# ══════════════════════════════════════════════════════════
# MESSAGE GENERATION
# ══════════════════════════════════════════════════════════
def gen_notif(name, plate, viols, user, pays=None):
    total = sum(float(v.get("amount",0)) for v in viols if v.get("amount"))
    lines = [
        f"السلام عليكم سيد {name}",
        "",
        f"معك {user} من شركة اتحاد الشاحنات للنقليات.",
        "",
        f"تم تسجيل المخالفة التالية على المركبة {plate} :",
        "",
    ]
    for i,v in enumerate(viols,1):
        lines.append(f"{i}) {jlbl(v.get('authority'))} - {fdt(v.get('violation_date'))} - {famt(v.get('amount'))} ريال")
    if pays:
        total_paid = sum(float(p.get("amount_paid",0)) for p in pays)
        remaining  = max(0, total-total_paid)
        lines += ["","سجل الدفعات:"]
        for p in pays:
            lines.append(f"  • تم سداد {famt(p.get('amount_paid',0))} ريال بتاريخ {p.get('payment_date','')}")
        lines += ["",f"الإجمالي المتبقي: {famt(remaining)}  ريال سعودي"]
    else:
        lines += ["",f"الإجمالي: {famt(total)}  ريال سعودي"]
    lines += [
        "","نرجو سداد المبلغ عن طريق الذهاب لمقر الشركة او عن طريق حوالة بنكية لحساب الشركة وإرسال صورة الإيصال هنا بعد السداد.",
        "","شاكرين تعاونك.","",user,"شركة اتحاد الشاحنات للنقليات",
    ]
    return "\n".join(lines)

def gen_reminder(name, plate, viols, user, pays=None):
    total = sum(float(v.get("amount",0)) for v in viols if v.get("amount"))
    if pays:
        total_paid = sum(float(p.get("amount_paid",0)) for p in pays)
        remaining  = max(0, total-total_paid)
        amt_str = f"{famt(remaining)} ريال (المتبقي من {famt(total)})"
        pay_lines = "\n".join(f"  • تم سداد {famt(p.get('amount_paid',0))} ريال بتاريخ {p.get('payment_date','')}" for p in pays)
        pay_section = f"\nسجل الدفعات:\n{pay_lines}\n"
    else:
        amt_str = f"{famt(total)} ريال"
        pay_section = ""
    return "\n".join([
        f"السلام عليكم سيد {name}،","",
        f"معك {user} من شركة اتحاد الشاحنات للنقليات.","",
        f"نود التذكير بوجود مخالفات معلقة على المركبة {plate} بقيمة {amt_str}.",
        pay_section,
        "اي تحديثات بخصوص المخالفات؟ يرجى تحديد موعد سداد متوقع.","",
        "شاكرين تعاونك.","",user,"شركة اتحاد الشاحنات للنقليات",
    ])

# ══════════════════════════════════════════════════════════
# BUILD DRIVER LIST
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def build_drivers(vdf, pdf, rems, today_iso):
    if vdf.empty: return []
    # to_dict('records') + pure-Python loop is ~10x faster than iterrows()
    records = vdf.to_dict("records")
    pays_records = pdf.to_dict("records") if not pdf.empty else []

    # pre-index payments by (name, plate) for O(1) lookup
    pays_idx = {}
    for p in pays_records:
        k = (p.get("driver_name",""), p.get("plate",""))
        pays_idx.setdefault(k, []).append(p)

    groups = {}
    for row in records:
        ph  = cp(row.get("phone")) or "بلا رقم"
        pl  = str(row.get("plate","")).strip() or "غير محدد"
        key = (str(row.get("driver_name","")).strip(), ph, pl)
        groups.setdefault(key, []).append(row)

    result = []
    for key, rows in groups.items():
        name, phone, plate = key
        sk  = get_sk([r.get("status","") for r in rows])
        if phone == "بلا رقم" and sk == "new":
            sk = "pending"
        rk  = f"{phone}_{plate}"
        if rk in rems and not rems[rk].get("is_done") and str(rems[rk].get("reminder_date","9999")) <= today_iso:
            sk = "reminder"
        dpays     = pays_idx.get((name, plate), [])
        # violations paid (any payment recorded, confirmed or pending)
        paid_vids = {p.get("violation_id") for p in dpays if p.get("violation_id")}
        sys_pend  = [r for r in rows if str(r.get("system_status","")).strip() == "معلقة"]
        # prows = unpaid pending violations (not covered by any payment)
        prows     = [r for r in sys_pend if r.get("violation_id") not in paid_vids]
        tp        = sum(float(r.get("amount",0)) for r in prows if r.get("amount"))
        conf_paid = sum(float(p.get("amount_paid",0)) for p in dpays
                        if p.get("verification_status") == "مؤكد"
                        and p.get("violation_id") in {r.get("violation_id") for r in prows})
        remaining = max(0, tp - conf_paid)
        latest_note = next((str(r.get("my_notes","")).strip() for r in sorted(rows, key=lambda x: str(x.get("contact_date","") or ""), reverse=True) if str(r.get("my_notes","")).strip() not in ("","nan","None")), "")
        result.append({
            "key":key, "name":name, "phone":phone, "plate":plate,
            "sk":sk, "label":SL.get(sk, sk),
            "rows":rows, "prows":prows, "count":len(rows),
            "tp":tp, "conf_paid":conf_paid, "remaining":remaining,
            "pays":dpays, "rem":rems.get(rk, {}),
            "note":latest_note,
        })
    result.sort(key=lambda d: (PR.get(d["sk"], 99), d["name"]))
    return result

# ══════════════════════════════════════════════════════════
# PAGE: السائقون
# ══════════════════════════════════════════════════════════
def pg_drivers(user):
    vdf=_viols(); pdf=_pays(); ndf=_notifs(); rems=_rems()
    today=date.today(); today_iso=today.isoformat()

    if vdf.empty:
        st.warning("لا توجد بيانات. ارفع إكسل من صفحة الإدارة.")
        return

    drivers=build_drivers(vdf,pdf,rems,today_iso)

    # sidebar filters
    with st.sidebar:
        show_all = st.toggle("عرض الكل", value=False)
        if show_all:
            fn=fr=fc=fp=fpa=fnt=fd=fnph=fnwa=fnc=True
        else:
            fn  = st.checkbox("🔴 جديد",        value=True)
            fr  = st.checkbox("🔔 تذكير اليوم", value=True)
            fc  = st.checkbox("🟡 تشيك",        value=True)
            fp  = st.checkbox("🟠 معلق",        value=True)
            fpa = st.checkbox("🟣 دفع جزئي",   value=True)
            fnt = st.checkbox("🔵 تم التبليغ", value=False)
            fd  = st.checkbox("🟢 تم",          value=False)
            fnph= st.checkbox("⚫ بلا رقم",     value=True)
            fnwa= st.checkbox("⚫ بلا واتساب",  value=True)
            fnc = st.checkbox("⚫ لا داعي",     value=False)
        st.divider()
        srch=st.text_input("",placeholder="بحث: اسم أو لوحة...",label_visibility="collapsed")
        sc1, sc2 = st.columns([1,1])
        with sc1:
            if st.button("تحديث",use_container_width=True):
                bust(); st.rerun()
        with sc2:
            no_ph_drvs = [d for d in drivers if d["phone"] == "بلا رقم"]
            if no_ph_drvs:
                _rows_nph = []
                for _d in no_ph_drvs:
                    for _v in _d["rows"]:
                        _rows_nph.append({"السائق":_d["name"],"اللوحة":_d["plate"],
                            "رقم المخالفة":_v.get("violation_id",""),
                            "الجهة":_v.get("authority",""),
                            "التاريخ":fdt(_v.get("violation_date","")),
                            "المبلغ":_v.get("amount",""),"الحالة":_v.get("status","")})
                _buf = io.BytesIO()
                pd.DataFrame(_rows_nph).to_excel(_buf, index=False, engine="openpyxl")
                st.download_button(f"بلا رقم",data=_buf.getvalue(),
                    file_name="drivers_no_phone.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="exp_noph")

    fm={"new":fn,"reminder":fr,"check":fc,"pending":fp,"partial":fpa,"notified":fnt,"done":fd,
        "no_phone":fnph,"no_wa":fnwa,"no_contact":fnc}
    shown=[d for d in drivers
           if fm.get(d["sk"],True)
           and (not srch or srch in d["name"] or srch.upper() in d["plate"].upper())]

    # pagination — reset page when search/filter changes
    _filter_sig = f"{srch}|{fn}{fr}{fc}{fp}{fpa}{fnt}{fd}{fnph}{fnwa}{fnc}"
    if st.session_state.get("_fsig") != _filter_sig:
        st.session_state["_fsig"] = _filter_sig
        st.session_state["drv_page"] = 0
    PER_PAGE   = 20
    total_pgs  = max(1, (len(shown) + PER_PAGE - 1) // PER_PAGE)
    cur_page   = min(st.session_state.get("drv_page", 0), total_pgs - 1)
    page_start = cur_page * PER_PAGE
    page_shown = shown[page_start : page_start + PER_PAGE]

    # ── stat strip (custom HTML) ──
    cnt={k:sum(1 for d in drivers if d["sk"]==k) for k in PR}
    cards_html = ""
    for sk, color, icon_name, label in STAT_CFG:
        n = cnt.get(sk, 0)
        cards_html += (
            f'<div class="stat-card">'
            f'<div class="stat-num" style="color:{color}">{n}</div>'
            f'<div class="stat-lbl">{ico(icon_name, 12, color)}<span>{label}</span></div>'
            f'</div>'
        )
    st.markdown(f'<div class="stat-strip">{cards_html}</div>', unsafe_allow_html=True)

    sel_key = st.session_state.get("sel")
    sel = next((d for d in drivers if d["key"]==sel_key), None) if sel_key else None

    if not sel:
        # ── driver list ──
        pg_lbl = f"صفحة {cur_page+1}/{total_pgs}" if total_pgs>1 else ""
        st.markdown(
            f"<div style='font-size:12px;color:#64748b;margin-bottom:6px;display:flex;justify-content:space-between'>"
            f"<span>{ico('users',13,'#64748b')} {len(shown)} سائق</span>"
            f"<span>{pg_lbl}</span></div>",
            unsafe_allow_html=True)

        for i in range(0, len(page_shown), 2):
            gc1, gc2 = st.columns(2)
            for j, col in enumerate([gc1, gc2]):
                idx = i + j
                if idx >= len(page_shown):
                    break
                d = page_shown[idx]
                with col:
                    rem_disp = famt(d["remaining"]) if d["remaining"]>0 else famt(d["tp"])
                    sel_cls  = "drv-sel" if st.session_state.get("sel")==d["key"] else ""
                    note_prev = str(d.get("note","")).strip()
                    note_prev = "" if note_prev in ("","nan","None") else note_prev[:40] + ("…" if len(note_prev)>40 else "")
                    note_line = f'<span class="dc-note">{note_prev}</span>' if note_prev else ""
                    st.markdown(
                        f'<div class="drv-card drv-{d["sk"]} {sel_cls}">'
                        f'  <div class="dc-info">'
                        f'    <span class="dc-name">{d["name"]}</span>'
                        f'    <span class="dc-sub">{ico("car",12,"#475569")} {d["plate"]}'
                        f'      <span style="color:#334155">·</span> {d["count"]} مخالفة</span>'
                        f'    {note_line}'
                        f'  </div>'
                        f'  <div class="dc-side">'
                        f'    <span class="dc-badge b-{d["sk"]}">{SL_SHORT.get(d["sk"],d["sk"])}</span>'
                        f'    <span class="dc-amt">{rem_disp} ر</span>'
                        f'  </div>'
                        f'</div>',
                        unsafe_allow_html=True)
                    st.markdown('<div class="drv-open">', unsafe_allow_html=True)
                    if st.button("فتح", key=f"d{page_start+idx}", use_container_width=True):
                        st.session_state.sel=d["key"]
                        st.session_state.sf=st.session_state.pf=st.session_state.sysv=False
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        # pagination controls
        if total_pgs > 1:
            pc1,pc2,pc3 = st.columns([1,2,1])
            with pc1:
                if cur_page>0 and st.button("→ السابق",use_container_width=True,key="pg_prev"):
                    st.session_state.drv_page=cur_page-1; st.rerun()
            with pc2:
                st.markdown(f"<div style='text-align:center;color:#475569;font-size:12px;padding-top:10px'>{cur_page+1} / {total_pgs}</div>",unsafe_allow_html=True)
            with pc3:
                if cur_page<total_pgs-1 and st.button("التالي ←",use_container_width=True,key="pg_next"):
                    st.session_state.drv_page=cur_page+1; st.rerun()

    else:
        sk = sel_key

        # ── detail header card ──
        status_badge = f'<span class="dc-badge b-{sel["sk"]}" style="font-size:12px;padding:4px 12px">{sel["label"]}</span>'
        st.markdown(
            f'<div class="drv-hdr">'
            f'  <div>'
            f'    <span class="dh-name">{sel["name"]}</span>'
            f'    <div class="dh-meta">'
            f'      <span class="dh-pill">{ico("car",14,"#60a5fa")} {sel["plate"]}</span>'
            f'      <span class="dh-pill">{ico("phone",14,"#60a5fa")} {sel["phone"]}</span>'
            f'      <span class="dh-pill">{ico("board",14,"#60a5fa")} {sel["count"]} مخالفة</span>'
            f'    </div>'
            f'  </div>'
            f'  {status_badge}'
            f'</div>',
            unsafe_allow_html=True)

        bc1, bc2 = st.columns([1, 5])
        with bc1:
            if st.button("رجوع", key="back_drv", use_container_width=True):
                st.session_state.sel=None; st.rerun()

        # reminder alert
        rem = sel.get("rem",{})
        if rem.get("reminder_date"):
            overdue = str(rem["reminder_date"]) <= today_iso
            lbl = "متأخر" if overdue else "تذكير"
            ra1, ra2 = st.columns([6, 1])
            with ra1:
                st.warning(f"{'⚠️' if overdue else '⏰'} {lbl}: {rem['reminder_date']}"
                           + (f"  —  {rem['note']}" if rem.get("note") else ""))
            with ra2:
                if st.button("تم ✓", key=f"rdone_{sk}", use_container_width=True):
                    mark_rem_done(sel["phone"], sel["plate"])
                    st.toast(f"تم إنجاز تذكير {sel['name']}")
                    st.rerun()

        # payment summary
        if sel["pays"]:
            conf=[p for p in sel["pays"] if p.get("verification_status")=="مؤكد"]
            pend=[p for p in sel["pays"] if p.get("verification_status")=="بانتظار التأكيد"]
            if conf: st.success(f"مدفوع مؤكد: {famt(sum(float(p.get('amount_paid',0)) for p in conf))} ريال")
            if pend: st.warning(f"بانتظار المحاسبة: {famt(sum(float(p.get('amount_paid',0)) for p in pend))} ريال")

        st.divider()

        # ── violations ──
        st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:6px'>{ico('file',13,'#64748b')} المخالفات</div>",
                    unsafe_allow_html=True)
        dpays_vids = {p.get("violation_id") for p in sel["pays"]}
        for v in sel["rows"]:
            ss   = str(v.get("system_status","")).strip()
            st_v = str(v.get("status","")).strip()
            vid  = v.get("violation_id","")
            paid = ("مدفوع" in ss or "تم الدفع" in st_v or "مدفوع" in st_v
                    or vid in dpays_vids)
            icon_html = (f'{ico("check-c",15,"#22c55e")}' if paid
                         else f'{ico("x-c",15,"#ef4444")}')
            paid_lbl = " — مدفوعة" if paid and vid in dpays_vids else ""
            st.markdown('<div class="viol-act-row">', unsafe_allow_html=True)
            vc1, vc2, vc3 = st.columns([10, 1, 1])
            with vc1:
                st.markdown(
                    f'<div class="viol-row {"viol-paid" if paid else "viol-unpaid"}">'
                    f'  <span class="viol-icon">{icon_html}</span>'
                    f'  <span class="viol-body">'
                    f'    <b>{jlbl(v.get("authority"))}</b>'
                    f'    <span style="color:#475569"> · {fdt(v.get("violation_date"))} · </span>'
                    f'    <b>{famt(v.get("amount"))} ريال</b>'
                    f'    <span style="color:#22c55e;font-size:11px">{paid_lbl}</span>'
                    f'    <br><small style="color:#334155">{ss} &nbsp; {vid}</small>'
                    f'  </span>'
                    f'</div>',
                    unsafe_allow_html=True)
            with vc2:
                if st.button("✏️", key=f"ev_{vid}", use_container_width=True, help="تعديل"):
                    if st.session_state.get("edit_v") == vid:
                        st.session_state.pop("edit_v", None)
                    else:
                        st.session_state["edit_v"] = vid
                        st.session_state.pop("del_confirm", None)
                    st.rerun()
            with vc3:
                if st.button("🗑️", key=f"dv_{vid}", use_container_width=True, help="حذف"):
                    if st.session_state.get("del_confirm") == vid:
                        st.session_state.pop("del_confirm", None)
                    else:
                        st.session_state["del_confirm"] = vid
                        st.session_state.pop("edit_v", None)
                        st.toast("⚠ اضغط تأكيد لإتمام الحذف")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # ── edit form ──
            if st.session_state.get("edit_v") == vid:
                ef1, ef2 = st.columns([2, 1])
                with ef1:
                    e_st = st.selectbox("الحالة:", ["تم التبليغ","معلق","تم الدفع","مدفوع جزئي",
                                                    "بلا واتساب","بلا رقم","لا داعي للتواصل","لم يتم التواصل"],
                                        key=f"est_{vid}")
                cur_notes = str(v.get("my_notes","")).strip()
                cur_notes = "" if cur_notes in ("nan","None") else cur_notes
                e_notes = st.text_area("ملاحظة:", value=cur_notes, key=f"en_{vid}",
                                       placeholder="اختياري...", height=68)
                es1, es2 = st.columns(2)
                with es1:
                    if st.button("حفظ", type="primary", key=f"esv_{vid}", use_container_width=True):
                        upd_violation(vid, e_st, e_notes)
                        st.toast("✓ تم تحديث المخالفة")
                        st.session_state.pop("edit_v", None)
                        st.rerun()
                with es2:
                    if st.button("إلغاء", key=f"esc_{vid}", use_container_width=True):
                        st.session_state.pop("edit_v", None)
                        st.rerun()

            # ── delete confirmation ──
            if st.session_state.get("del_confirm") == vid:
                st.warning(f"حذف: **{jlbl(v.get('authority'))}** · {fdt(v.get('violation_date'))} · {famt(v.get('amount'))} ريال")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("تأكيد الحذف", type="primary", key=f"dok_{vid}", use_container_width=True):
                        del_violation(vid)
                        st.toast("✓ تم حذف المخالفة")
                        st.session_state.pop("del_confirm", None)
                        st.rerun()
                with dc2:
                    if st.button("إلغاء", key=f"dcan_{vid}", use_container_width=True):
                        st.session_state.pop("del_confirm", None)
                        st.rerun()

        if sel["remaining"]>0:
            st.markdown(
                f'<div style="margin-top:8px;padding:10px 14px;background:rgba(239,68,68,.1);'
                f'border-radius:10px;border-right:3px solid #ef4444;font-size:13px;color:#fca5a5">'
                f'{ico("dollar",14,"#ef4444")} المتبقي: <b>{famt(sel["remaining"])} ريال</b></div>',
                unsafe_allow_html=True)
        elif sel["tp"]>0:
            st.markdown(
                f'<div style="margin-top:8px;padding:10px 14px;background:rgba(59,130,246,.1);'
                f'border-radius:10px;border-right:3px solid #3b82f6;font-size:13px;color:#93c5fd">'
                f'{ico("dollar",14,"#3b82f6")} الإجمالي: <b>{famt(sel["tp"])} ريال</b></div>',
                unsafe_allow_html=True)

        # notification log
        if not ndf.empty:
            dn=ndf[(ndf["driver_name"]==sel["name"])&(ndf["plate"]==sel["plate"])].sort_values("sent_at",ascending=False)
            if not dn.empty:
                with st.expander(f"سجل التواصل ({len(dn)} مرة)"):
                    for _,n in dn.iterrows():
                        st.markdown(f"• **{n.get('notification_type','')}** — {fmt_sent_at(n.get('sent_at',''))} — {n.get('sent_by','')}  {('— '+str(n.get('notes',''))) if n.get('notes') else ''}")

        st.divider()

        # ── messages ──
        pviols     = sel["prows"] if sel["prows"] else sel["rows"]
        conf_pays  = [p for p in sel["pays"] if p.get("verification_status")=="مؤكد"]
        notif_msg  = gen_notif(sel["name"],sel["plate"],pviols,user,conf_pays or None)
        remind_msg = gen_reminder(sel["name"],sel["plate"],pviols,user,conf_pays or None)

        st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:4px'>{ico('msg',13,'#64748b')} رسالة التبليغ</div>", unsafe_allow_html=True)
        edited_notif = st.text_area("",value=notif_msg,height=200,
                                    key=f"mn_{sk}_{user}",label_visibility="collapsed")

        # ── action buttons ──
        url = wa_link(sel["phone"],edited_notif) if sel["phone"]!="بلا رقم" else None
        if url: wa_btn(url,"تبليغ واتساب","#25D366")
        else:   st.button("لا يوجد رقم",disabled=True,use_container_width=True)

        b3, b4, b5 = st.columns(3)
        with b3:
            if st.button("تم الإرسال",use_container_width=True,key=f"sf_{sk}"):
                st.session_state.sf=True; st.session_state.pf=False
        with b4:
            if st.button("سجل دفع",use_container_width=True,key=f"pf_{sk}"):
                st.session_state.pf=True; st.session_state.sf=False
        with b5:
            if st.button("أرقام السستم",use_container_width=True,key=f"sv_{sk}"):
                st.session_state.sysv=not st.session_state.get("sysv",False)

        if st.session_state.get("sysv"):
            st.markdown(f"<div style='font-size:12px;color:#64748b;margin:8px 0 4px'>{ico('hash',13,'#64748b')} أرقام للسستم</div>",
                        unsafe_allow_html=True)
            for v in pviols:
                st.code(f"{v.get('violation_id','')} | {jlbl(v.get('authority'))} | {fdt(v.get('violation_date'))} | {famt(v.get('amount'))} ريال")

        # ── SENT FORM ──
        if st.session_state.get("sf"):
            st.divider()
            st.markdown(f"<div style='font-size:14px;font-weight:700;color:#f1f5f9;margin-bottom:8px'>{ico('board',16,'#60a5fa')} تسجيل الإرسال</div>",
                        unsafe_allow_html=True)
            new_st=st.selectbox("الحالة:",["تم التبليغ","معلق","بلا واتساب","بلا رقم","لا داعي للتواصل","تم الدفع"],key=f"nst_{sk}")
            nv=st.text_area("ملاحظة:",key=f"nv_{sk}",placeholder="وعد بالدفع / لا يرد / ...")
            rd = today + timedelta(days=3)
            st.caption(f"سيُضاف تذكير تلقائياً في {rd.strftime('%d-%m-%Y')}")
            sc1,sc2=st.columns(2)
            with sc1:
                if st.button("حفظ",type="primary",key=f"ssv_{sk}",use_container_width=True):
                    today_d,time_d,full_d=now_sa_str()
                    upd_status(sel["name"],sel["phone"],sel["plate"],f"{new_st} {full_d}",nv,today_d)
                    log_notif(sel["name"],sel["phone"],sel["plate"],"تبليغ",user,nv)
                    upsert_rem(sel["phone"],sel["plate"],sel["name"],rd,nv,user)
                    st.toast(f"✓ حُفظ: {new_st} — {sel['name']}")
                    st.session_state.sf=False; st.session_state.sel=None; st.rerun()
            with sc2:
                if st.button("إلغاء",key=f"scc_{sk}",use_container_width=True):
                    st.session_state.sf=False; st.rerun()

        # ── PAYMENT FORM ──
        if st.session_state.get("pf"):
            st.divider()
            st.markdown(f"<div style='font-size:14px;font-weight:700;color:#f1f5f9;margin-bottom:8px'>{ico('dollar',16,'#60a5fa')} تسجيل دفعة</div>",
                        unsafe_allow_html=True)
            pviols_pay = sel["prows"]
            if not pviols_pay:
                st.info("جميع مخالفات هذا السائق مسجّلة كمدفوعة.")
                if st.button("إغلاق",key=f"pcc_empty_{sk}",use_container_width=True):
                    st.session_state.pf=False; st.rerun()
            else:
                # violation selector
                viol_opts = {
                    f"{jlbl(v.get('authority'))}  ·  {fdt(v.get('violation_date'))}  ·  {famt(v.get('amount'))} ريال": v
                    for v in pviols_pay
                }
                sv_lbl = st.selectbox("المخالفة:", list(viol_opts.keys()), key=f"vs_{sk}")
                sv     = viol_opts[sv_lbl]
                default_amt = float(sv.get("amount",0))

                pt=st.radio("نوع الدفع:",["كامل","جزئي"],horizontal=True,key=f"pt_{sk}")
                if pt=="جزئي":
                    amt=st.number_input("المبلغ المدفوع (ريال):",min_value=0.01,
                                        value=round(default_amt/2,2),key=f"amt_{sk}")
                else:
                    amt=default_amt
                    st.info(f"المبلغ الكامل: {famt(amt)} ريال")
                pc1,pc2=st.columns(2)
                with pc1: pm=st.selectbox("طريقة الدفع:",["تحويل بنكي","نقد","آخر"],key=f"pm_{sk}")
                with pc2: pd_=st.date_input("تاريخ الدفع:",value=today,key=f"pdd_{sk}")
                col=st.radio("من جمّع؟",["أحمد","رهف","آخر"],horizontal=True,key=f"col_{sk}")
                other=""
                if col=="آخر": other=st.text_input("اسم الموظف:",key=f"oc_{sk}")
                verif=st.radio("الحالة:",["بانتظار التأكيد من المحاسبة","مؤكد"],horizontal=True,key=f"vr_{sk}")
                rref=""; rurl=""
                if pm=="تحويل بنكي":
                    rref=st.text_input("رقم الإيصال / المرجع:",key=f"rr_{sk}")
                    rf=st.file_uploader("صورة الإيصال:",type=["jpg","jpeg","png","pdf"],key=f"rf_{sk}")
                else: rf=None
                pnts=st.text_area("ملاحظة:",key=f"pnts_{sk}",placeholder="اختياري...")
                ps1,ps2=st.columns(2)
                with ps1:
                    if st.button("حفظ الدفعة",type="primary",key=f"psv_{sk}",use_container_width=True):
                        if amt<=0: st.error("أدخل مبلغاً صحيحاً")
                        else:
                            if rf: rurl=upload_receipt(rf,str(uuid.uuid4())[:8])
                            vid = sv.get("violation_id","")
                            add_payment(vid,sel["name"],sel["phone"],sel["plate"],
                                        amt,pt,pm,rurl,rref if pm=="تحويل بنكي" else "",
                                        col,other,verif,pd_.strftime("%d-%m-%Y"),pnts)
                            today_d,_,full_d=now_sa_str()
                            new_vst=(f"تم الدفع {full_d}" if pt=="كامل"
                                     else f"مدفوع جزئي {full_d}")
                            upd_violation(vid, new_vst, pnts)
                            st.toast(f"✓ {famt(amt)} ريال — {jlbl(sv.get('authority'))}")
                            st.session_state.pf=False; bust(); st.rerun()
                with ps2:
                    if st.button("إلغاء",key=f"pcc_{sk}",use_container_width=True):
                        st.session_state.pf=False; st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE: المدفوعات
# ══════════════════════════════════════════════════════════
def pg_payments():
    st.markdown(f'<div class="pg-hdr">{ico("dollar",22,"#60a5fa")} المدفوعات</div>',
                unsafe_allow_html=True)
    df=_pays()
    if df.empty: st.info("لا توجد مدفوعات مسجّلة بعد."); return

    t1, t2 = st.tabs(["بانتظار التأكيد","المؤكدة"])
    with t1:
        pend=df[df["verification_status"]=="بانتظار التأكيد"]
        if pend.empty: st.success("لا يوجد دفعات بانتظار التأكيد")
        else:
            st.markdown(f"**{len(pend)} دفعة بانتظار التأكيد**")
            for _,p in pend.iterrows():
                with st.container():
                    c1,c2,c3,c4=st.columns([3,1,1,1])
                    with c1:
                        st.markdown(f"**{p.get('driver_name','')}** — {p.get('plate','')} — {p.get('payment_date','')}")
                        st.caption(f"طريقة: {p.get('payment_method','')} | جمّع: {p.get('collected_by','')} {p.get('other_collector','')}")
                        if p.get("receipt_ref"): st.caption(f"مرجع: {p.get('receipt_ref','')}")
                        if p.get("receipt_url"): st.markdown(f"[الإيصال]({p.get('receipt_url','')})")
                        if p.get("notes"): st.caption(f"ملاحظة: {p.get('notes','')}")
                    with c2: st.metric("المبلغ",f"{famt(p.get('amount_paid',0))} ر")
                    with c3: st.metric("النوع",p.get("payment_type",""))
                    with c4:
                        if st.button("تأكيد",key=f"cf_{p.get('id','')}",use_container_width=True,type="primary"):
                            confirm_pay(p.get("id"))
                            if p.get("payment_type")=="كامل":
                                upd_status(p.get("driver_name",""),p.get("phone",""),p.get("plate",""),"تم الدفع")
                            st.success("تم التأكيد"); st.rerun()
                    st.divider()
    with t2:
        conf=df[df["verification_status"]=="مؤكد"]
        if conf.empty: st.info("لا توجد مدفوعات مؤكدة بعد.")
        else:
            tc1,tc2,tc3=st.columns(3)
            tc1.metric("إجمالي المحصّل",f"{famt(conf['amount_paid'].astype(float).sum())} ر")
            tc2.metric("محصّل أحمد",f"{famt(conf[conf['collected_by']=='أحمد']['amount_paid'].astype(float).sum())} ر")
            tc3.metric("محصّل رهف",f"{famt(conf[conf['collected_by']=='رهف']['amount_paid'].astype(float).sum())} ر")
            st.dataframe(conf[["driver_name","plate","amount_paid","payment_type",
                                "payment_method","collected_by","payment_date"]]\
                .rename(columns={"driver_name":"السائق","plate":"اللوحة","amount_paid":"المبلغ",
                                  "payment_type":"النوع","payment_method":"الطريقة",
                                  "collected_by":"جمّع","payment_date":"التاريخ"}),
                use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════
# PAGE: التقارير
# ══════════════════════════════════════════════════════════
def pg_reports():
    st.markdown(f'<div class="pg-hdr">{ico("chart",22,"#60a5fa")} التقارير</div>',
                unsafe_allow_html=True)
    ndf=_notifs(); vdf=_viols(); pdf=_pays()
    today=date.today()

    tab_a,tab_r,tab_all=st.tabs(["أحمد","رهف","الكل"])

    def _person_stats(person_name, tab):
        with tab:
            if not ndf.empty:
                ndf2=ndf.copy()
                ndf2["_d"]=pd.to_datetime(ndf2["sent_at"],errors="coerce").dt.date
                pn=ndf2[ndf2["sent_by"]==person_name]
                td=pn[pn["_d"]==today]
                c1,c2,c3,c4=st.columns(4)
                c1.metric("تبليغ اليوم",len(td))
                c2.metric("سائقون اليوم",td["driver_name"].nunique() if not td.empty else 0)
                c3.metric("إجمالي التبليغات",len(pn))
                c4.metric("سائقون مختلفون",pn["driver_name"].nunique() if not pn.empty else 0)
                if not pn.empty:
                    st.markdown("**آخر 10 تبليغات:**")
                    last=pn.sort_values("sent_at",ascending=False).head(10)
                    for _,n in last.iterrows():
                        st.markdown(f"• {fmt_sent_at(n.get('sent_at',''))} — **{n.get('driver_name','')}** — {n.get('plate','')} — {n.get('notification_type','')} {('— '+str(n.get('notes',''))) if n.get('notes') else ''}")
            else:
                st.info("لا توجد إشعارات مسجّلة بعد.")
            if not pdf.empty:
                st.divider()
                cp_=pdf[(pdf["verification_status"]=="مؤكد")&(pdf["collected_by"]==person_name)]
                st.metric(f"محصّل {person_name}",f"{famt(cp_['amount_paid'].astype(float).sum())} ريال" if not cp_.empty else "0 ريال")
                if not cp_.empty:
                    st.dataframe(cp_[["driver_name","plate","amount_paid","payment_method","payment_date"]]\
                        .rename(columns={"driver_name":"السائق","plate":"اللوحة","amount_paid":"المبلغ",
                                          "payment_method":"الطريقة","payment_date":"التاريخ"}),
                        use_container_width=True,hide_index=True)

    _person_stats("أحمد", tab_a)
    _person_stats("رهف",  tab_r)

    with tab_all:
        if not ndf.empty:
            ndf3=ndf.copy()
            ndf3["_d"]=pd.to_datetime(ndf3["sent_at"],errors="coerce").dt.date
            td=ndf3[ndf3["_d"]==today]
            c1,c2,c3,c4=st.columns(4)
            c1.metric("تبليغ اليوم",len(td))
            c2.metric("أحمد اليوم",len(td[td["sent_by"]=="أحمد"]))
            c3.metric("رهف اليوم",len(td[td["sent_by"]=="رهف"]))
            c4.metric("سائقون مختلفون",td["driver_name"].nunique() if not td.empty else 0)
        if not pdf.empty:
            st.divider()
            cp_=pdf[pdf["verification_status"]=="مؤكد"]
            pc1,pc2,pc3=st.columns(3)
            pc1.metric("إجمالي المحصّل",f"{famt(cp_['amount_paid'].astype(float).sum())} ر")
            pc2.metric("محصّل أحمد",f"{famt(cp_[cp_['collected_by']=='أحمد']['amount_paid'].astype(float).sum())} ر")
            pc3.metric("محصّل رهف",f"{famt(cp_[cp_['collected_by']=='رهف']['amount_paid'].astype(float).sum())} ر")

    st.divider()
    st.markdown("### تقرير مخصص")
    if vdf.empty: st.info("لا توجد بيانات."); return

    rc1,rc2=st.columns(2)
    with rc1: rep_user=st.selectbox("الموظف:",["أحمد","رهف","الكل"])
    with rc2:
        all_plates=sorted(vdf["plate"].dropna().unique().tolist())
        sel_plates=st.multiselect("أرقام اللوحات:",all_plates,placeholder="اختر أو ابحث...")

    if not st.button("توليد التقرير",type="primary"): return
    if not sel_plates: st.warning("اختر لوحة واحدة على الأقل"); return

    rows=[]
    for plate in sel_plates:
        pv=vdf[vdf["plate"]==plate]
        if pv.empty: continue
        fr=pv.iloc[0]
        dname=fr.get("driver_name",""); phone_=cp(fr.get("phone",""))
        dn=pd.DataFrame()
        if not ndf.empty:
            dn=ndf[(ndf["driver_name"]==dname)&(ndf["plate"]==plate)].sort_values("sent_at")
        n1_dt=n2_dt=n1_note=n2_note=n1_by=n2_by=""
        if not dn.empty:
            try: n1_dt=fmt_sent_at(dn.iloc[0]["sent_at"]); n1_note=str(dn.iloc[0].get("notes","")); n1_by=str(dn.iloc[0].get("sent_by",""))
            except: pass
            if len(dn)>1:
                try: n2_dt=fmt_sent_at(dn.iloc[1]["sent_at"]); n2_note=str(dn.iloc[1].get("notes","")); n2_by=str(dn.iloc[1].get("sent_by",""))
                except: pass
        dp=pd.DataFrame()
        if not pdf.empty:
            dp=pdf[(pdf["driver_name"]==dname)&(pdf["plate"]==plate)&(pdf["verification_status"]=="مؤكد")]
        total_paid=dp["amount_paid"].astype(float).sum() if not dp.empty else 0
        for _,v in pv.iterrows():
            rows.append({
                "السائق":dname,"الجوال":phone_,"اللوحة":plate,
                "تاريخ المخالفة":fdt(v.get("violation_date","")),
                "المبلغ":float(v.get("amount",0)),
                "حالة السستم":v.get("system_status",""),
                "الحالة":v.get("status",""),
                "تاريخ أول تبليغ":n1_dt,"بواسطة":n1_by,"ملاحظات أول تبليغ":n1_note,
                "تاريخ ثاني تبليغ":n2_dt,"بواسطة2":n2_by,"ملاحظات ثاني تبليغ":n2_note,
                "تم سداد":famt(total_paid) if total_paid>0 else "",
            })

    if not rows: st.warning("لا توجد بيانات للوحات المختارة"); return
    rdf=pd.DataFrame(rows)
    st.dataframe(rdf,use_container_width=True,hide_index=True)
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine="openpyxl") as w:
        rdf.to_excel(w,index=False,sheet_name="التقرير")
    out.seek(0)
    st.download_button("تحميل التقرير",out,
        file_name=f"تقرير_{rep_user}_{today}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary")

# ══════════════════════════════════════════════════════════
# PAGE: الإدارة
# ══════════════════════════════════════════════════════════
def pg_admin():
    st.markdown(f'<div class="pg-hdr">{ico("settings",22,"#60a5fa")} الإدارة</div>',
                unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["رفع إكسل","إضافة مخالفة","تصدير"])

    with t1:
        st.markdown("### رفع إكسل جديد ودمجه")
        st.info("ستُضاف فقط المخالفات الجديدة — شغلك القديم لن يُمس")
        up=st.file_uploader("ارفع ملف الإكسل (شيت الكل):",type=["xlsx"])
        if up and st.button("دمج الملف",type="primary"):
            with st.spinner("جاري الدمج..."):
                try:
                    ndf_=pd.read_excel(up,sheet_name="الكل")
                    ex=_viols()
                    ex_ids=set(ex["violation_id"].dropna().astype(str)) if not ex.empty else set()
                    ndf_["_v"]=ndf_["رقم المخالفة"].astype(str)
                    to_add=ndf_[~ndf_["_v"].isin(ex_ids)]
                    added=0; batch=[]
                    def _ss(v): return str(v).strip() if v and str(v) not in ("nan","None") else ""
                    for _,row in to_add.iterrows():
                        vid=_ss(row.get("رقم المخالفة"))
                        if not vid: continue
                        st_v=_ss(row.get("الحالة"))
                        asgn=""
                        if "احمد" in st_v.lower() or "أحمد" in st_v: asgn="أحمد"
                        elif "رهف" in st_v: asgn="رهف"
                        batch.append({
                            "violation_id":vid,
                            "driver_name":_ss(row.get("السائق")),
                            "phone":cp(row.get("الجوال","")),
                            "plate":_ss(row.get("اللوحة (نظام)")),
                            "authority":_ss(row.get("الجهة")),
                            "violation_date":fdt(row.get("التاريخ")),
                            "amount":float(row.get("المبلغ",0)) if not pd.isna(row.get("المبلغ",0)) else 0,
                            "system_status":_ss(row.get("حالة السستم")) or "معلقة",
                            "system_notified":_ss(row.get("التبليغ (السستم)")),
                            "match_status":_ss(row.get("حالة المطابقة")) or "مؤكدة",
                            "status":"جديد","my_notes":_ss(row.get("ملاحظاتي")),
                            "assigned_to":asgn,"manually_added":False,
                        })
                        if len(batch)>=50:
                            _hx.post(f"{_base()}/rest/v1/violations",json=batch,
                                     headers=_h({"Prefer":"return=minimal"}),timeout=60)
                            added+=len(batch); batch=[]
                    if batch:
                        _hx.post(f"{_base()}/rest/v1/violations",json=batch,
                                 headers=_h({"Prefer":"return=minimal"}),timeout=60)
                        added+=len(batch)
                    bust()
                    st.success(f"{added} مخالفة جديدة أُضيفت | {len(ex_ids)} موجودة مسبقاً لم تُمس")
                except Exception as e:
                    st.error(f"خطأ: {e}")

    with t2:
        st.markdown("### إضافة مخالفة يدوياً")
        ma1,ma2=st.columns(2)
        with ma1:
            new_plate=st.text_input("رقم اللوحة:*",placeholder="ASA 1234")
            new_name=st.text_input("اسم السائق:*",placeholder="اسم السائق")
            new_phone=st.text_input("رقم الجوال:",placeholder="05XXXXXXXX")
        with ma2:
            new_auth=st.selectbox("الجهة:",["مخالفات مرورية","مخالفات هيئة النقل","مخالفات بلدية","مخالفات جمركية","مخالفات أوزان","إجراء قضائي"])
            new_date=st.date_input("تاريخ المخالفة:",value=date.today())
            new_amt=st.number_input("مبلغ المخالفة (ريال):",min_value=0.0,step=100.0)
        new_notes=st.text_area("ملاحظة:",placeholder="اختياري...")
        if st.button("إضافة المخالفة",type="primary"):
            if not new_plate or not new_name:
                st.error("رقم اللوحة واسم السائق مطلوبان")
            else:
                vid=f"MAN-{date.today().strftime('%Y')}-{str(uuid.uuid4())[:6].upper()}"
                try:
                    _hx.post(f"{_base()}/rest/v1/violations",
                             json={"violation_id":vid,"driver_name":new_name.strip(),
                                   "phone":cp(new_phone),"plate":new_plate.strip().upper(),
                                   "authority":new_auth,"violation_date":new_date.strftime("%Y-%m-%d"),
                                   "amount":new_amt,"system_status":"معلقة",
                                   "match_status":"مؤكدة","status":"جديد",
                                   "my_notes":new_notes,"manually_added":True},
                             headers=_h({"Prefer":"return=minimal"}),timeout=30)
                    bust()
                    st.success(f"تمت الإضافة — رقم المخالفة: {vid}")
                except Exception as e: st.error(f"خطأ: {e}")

    with t3:
        st.markdown("### تصدير كامل")
        if st.button("تصدير إكسل كامل",type="primary"):
            vdf=_viols(); pdf=_pays(); ndf=_notifs()
            if vdf.empty: st.error("لا توجد بيانات"); return
            with st.spinner("جاري التصدير..."):
                out=io.BytesIO()
                with pd.ExcelWriter(out,engine="openpyxl") as w:
                    exp=vdf.rename(columns={
                        "driver_name":"السائق","phone":"الجوال","plate":"اللوحة (نظام)",
                        "authority":"الجهة","violation_id":"رقم المخالفة",
                        "violation_date":"التاريخ","amount":"المبلغ",
                        "system_status":"حالة السستم","system_notified":"التبليغ (السستم)",
                        "match_status":"حالة المطابقة","status":"الحالة",
                        "my_notes":"ملاحظاتي","contact_date":"تاريخ التواصل",
                    })
                    exp.to_excel(w,index=False,sheet_name="الكل")
                    for lbl,kw in [("مطلوب أحمد","أحمد"),("مطلوب رهف","رهف")]:
                        sub=vdf[vdf["status"].str.contains(kw,na=False)]
                        if not sub.empty: sub.to_excel(w,index=False,sheet_name=lbl)
                    if not pdf.empty: pdf.to_excel(w,index=False,sheet_name="المدفوعات")
                    if not ndf.empty: ndf.to_excel(w,index=False,sheet_name="سجل التواصل")
                out.seek(0)
            st.download_button("تحميل الملف",out,
                file_name=f"Workrance_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary")

# ══════════════════════════════════════════════════════════
# PAGE: التذكيرات
# ══════════════════════════════════════════════════════════
def pg_reminders(user):
    vdf=_viols(); pdf=_pays(); ndf=_notifs(); rems=_rems()
    today=date.today(); today_iso=today.isoformat()

    st.markdown(f'<div class="pg-hdr">{ico("bell",22,"#f97316")} التذكيرات</div>', unsafe_allow_html=True)

    if vdf.empty:
        st.warning("لا توجد بيانات."); return

    all_drvs = build_drivers(vdf, pdf, rems, today_iso)

    # drivers with pending reminders (due today or overdue)
    due = [d for d in all_drvs
           if d.get("rem",{}).get("reminder_date")
           and not d["rem"].get("is_done")
           and str(d["rem"]["reminder_date"]) <= today_iso]

    if not due:
        st.success("لا يوجد تذكيرات مستحقة اليوم.")
        upcoming = sorted(
            [d for d in all_drvs if d.get("rem",{}).get("reminder_date") and not d["rem"].get("is_done")
             and str(d["rem"]["reminder_date"]) > today_iso],
            key=lambda d: d["rem"]["reminder_date"])
        if upcoming:
            st.divider()
            st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:8px'>{ico('clock',13,'#64748b')} التذكيرات القادمة ({len(upcoming)})</div>", unsafe_allow_html=True)
            for d in upcoming[:15]:
                rdate = d["rem"]["reminder_date"]
                note  = d["rem"].get("note","")
                st.markdown(
                    f"<div style='padding:6px 0;border-bottom:1px solid #1e293b;font-size:13px'>"
                    f"<b style='color:#e2e8f0'>{d['name']}</b> "
                    f"<span style='color:#475569'>{d['plate']} · {rdate}</span>"
                    + (f"<br><span style='color:#475569;font-size:11px;padding-right:12px'>{note}</span>" if note else "")
                    + "</div>", unsafe_allow_html=True)
        return

    overdue = [d for d in due if str(d["rem"]["reminder_date"]) < today_iso]
    today_r = [d for d in due if str(d["rem"]["reminder_date"]) == today_iso]
    st.markdown(
        f'<div class="stat-strip">'
        f'<div class="stat-card"><div class="stat-num" style="color:#ef4444">{len(overdue)}</div>'
        f'<div class="stat-lbl">{ico("alert",12,"#ef4444")}<span>متأخر</span></div></div>'
        f'<div class="stat-card"><div class="stat-num" style="color:#f97316">{len(today_r)}</div>'
        f'<div class="stat-lbl">{ico("bell",12,"#f97316")}<span>اليوم</span></div></div>'
        f'<div class="stat-card"><div class="stat-num" style="color:#94a3b8">{len(due)}</div>'
        f'<div class="stat-lbl">{ico("users",12,"#94a3b8")}<span>الإجمالي</span></div></div>'
        f'</div>', unsafe_allow_html=True)

    sel_key = st.session_state.get("rem_sel")
    rsel = next((d for d in due if d["key"]==sel_key), None) if sel_key else None

    if not rsel:
        st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:6px'>{ico('bell',13,'#64748b')} {len(due)} تذكير مستحق</div>", unsafe_allow_html=True)
        for i, d in enumerate(due):
            rdate = d["rem"].get("reminder_date","")
            is_ov = str(rdate) < today_iso
            bc    = "#ef4444" if is_ov else "#f97316"
            lbl   = "متأخر" if is_ov else "اليوم"
            bcls  = "b-new" if is_ov else "b-reminder"
            note  = d["rem"].get("note","")
            st.markdown(
                f'<div class="drv-card" style="border-right-color:{bc}">'
                f'  <div class="dc-info">'
                f'    <span class="dc-name">{d["name"]}</span>'
                f'    <span class="dc-sub">{ico("car",12,"#475569")} {d["plate"]}'
                f'      <span style="color:#334155">·</span> {ico("clock",12,"#475569")} {rdate}</span>'
                + (f'    <span style="font-size:11px;color:#475569;margin-top:2px;display:block">{note}</span>' if note else "")
                + f'  </div>'
                f'  <div class="dc-side">'
                f'    <span class="dc-badge {bcls}">{lbl}</span>'
                f'    <span class="dc-amt">{famt(d["remaining"] or d["tp"])} ر</span>'
                f'  </div>'
                f'</div>', unsafe_allow_html=True)
            st.markdown('<div class="drv-open">', unsafe_allow_html=True)
            if st.button("تذكير", key=f"ropen_{i}", use_container_width=True):
                st.session_state["rem_sel"] = d["key"]; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        rdate   = rsel["rem"].get("reminder_date","")
        is_ov   = str(rdate) < today_iso
        pviols  = rsel["prows"] if rsel["prows"] else rsel["rows"]
        dpv     = {p.get("violation_id") for p in rsel["pays"]}
        conf_p  = [p for p in rsel["pays"] if p.get("verification_status")=="مؤكد"]

        bc1, bc2 = st.columns([1, 5])
        with bc1:
            if st.button("رجوع", key="rem_back", use_container_width=True):
                st.session_state["rem_sel"] = None; st.rerun()

        status_badge = f'<span class="dc-badge {"b-new" if is_ov else "b-reminder"}" style="font-size:12px;padding:4px 12px">{"متأخر" if is_ov else "اليوم"}</span>'
        st.markdown(
            f'<div class="drv-hdr">'
            f'  <div>'
            f'    <span class="dh-name">{rsel["name"]}</span>'
            f'    <div class="dh-meta">'
            f'      <span class="dh-pill">{ico("car",14,"#60a5fa")} {rsel["plate"]}</span>'
            f'      <span class="dh-pill">{ico("phone",14,"#60a5fa")} {rsel["phone"]}</span>'
            f'      <span class="dh-pill">{ico("clock",14,"#f97316")} تذكير {rdate}</span>'
            f'    </div>'
            + (f'    <div style="margin-top:5px;font-size:12px;color:#64748b">{rsel["rem"].get("note","")}</div>' if rsel["rem"].get("note") else "")
            + f'  </div>  {status_badge}'
            f'</div>', unsafe_allow_html=True)

        for v in pviols:
            paid = v.get("violation_id","") in dpv
            ih   = f'{ico("check-c",14,"#22c55e")}' if paid else f'{ico("x-c",14,"#ef4444")}'
            st.markdown(
                f'<div class="viol-row {"viol-paid" if paid else "viol-unpaid"}">'
                f'  <span class="viol-icon">{ih}</span>'
                f'  <span class="viol-body"><b>{jlbl(v.get("authority"))}</b>'
                f'  <span style="color:#475569"> · {fdt(v.get("violation_date"))} · </span>'
                f'  <b>{famt(v.get("amount"))} ريال</b></span></div>', unsafe_allow_html=True)

        if rsel["remaining"]>0:
            st.markdown(f'<div style="margin-top:6px;padding:8px 12px;background:rgba(239,68,68,.1);border-radius:8px;border-right:3px solid #ef4444;font-size:13px;color:#fca5a5">{ico("dollar",13,"#ef4444")} المتبقي: <b>{famt(rsel["remaining"])} ريال</b></div>', unsafe_allow_html=True)

        st.divider()

        remind_msg = gen_reminder(rsel["name"], rsel["plate"], pviols, user, conf_p or None)
        st.markdown(f"<div style='font-size:12px;color:#64748b;margin-bottom:4px'>{ico('msg',13,'#64748b')} رسالة التذكير</div>", unsafe_allow_html=True)
        edited_rem = st.text_area("", value=remind_msg, height=210,
                                  key=f"rm_{sel_key}_{user}", label_visibility="collapsed")

        rurl = wa_link(rsel["phone"], edited_rem) if rsel["phone"] != "بلا رقم" else None
        if rurl: wa_btn(rurl, "إرسال التذكير واتساب", "#f97316")
        else:    st.button("لا يوجد رقم", disabled=True, use_container_width=True)

        st.divider()
        ra1, ra2 = st.columns(2)
        with ra1:
            if st.button("تم التذكير ✓", type="primary", key="rem_done", use_container_width=True):
                mark_rem_done(rsel["phone"], rsel["plate"])
                log_notif(rsel["name"], rsel["phone"], rsel["plate"], "تذكير", user)
                st.toast(f"✓ تم — {rsel['name']}")
                st.session_state["rem_sel"] = None; st.rerun()
        with ra2:
            if st.button("تأجيل 3 أيام", key="rem_post", use_container_width=True):
                new_rd = today + timedelta(days=3)
                upsert_rem(rsel["phone"], rsel["plate"], rsel["name"], new_rd, rsel["rem"].get("note",""), user)
                st.toast(f"تم التأجيل إلى {new_rd.strftime('%d-%m-%Y')}")
                st.session_state["rem_sel"] = None; st.rerun()


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
def main():
    for k,v in [("user","أحمد"),("sel",None),("rem_sel",None),("sf",False),("pf",False),("sysv",False)]:
        if k not in st.session_state: st.session_state[k]=v

    with st.sidebar:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0 10px">'
            f'{ico("truck",22,"#60a5fa")}'
            f'<span style="font-size:18px;font-weight:800;color:#f1f5f9">Workrance</span>'
            f'</div>',
            unsafe_allow_html=True)
        st.divider()
        # user picker — vertical
        u_chosen = st.radio("", ["أحمد", "رهف"],
                            index=0 if st.session_state["user"]=="أحمد" else 1,
                            label_visibility="collapsed")
        if u_chosen != st.session_state["user"]:
            st.session_state["user"]=u_chosen
            st.session_state.sel=st.session_state["rem_sel"]=None
            st.session_state.sf=st.session_state.pf=st.session_state.sysv=False
            st.rerun()
        user=st.session_state["user"]
        st.divider()
        page=st.radio("", [
            "السائقون", "التذكيرات", "المدفوعات", "التقارير", "الإدارة"
        ], label_visibility="collapsed")

        # reminder alert badge
        _rems_now = _rems()
        _today_m  = date.today().isoformat()
        _due_now  = [v for v in _rems_now.values()
                     if not v.get("is_done") and str(v.get("reminder_date","9999")) <= _today_m]
        if _due_now:
            st.markdown(
                f'<div style="background:rgba(249,115,22,.12);border:1px solid rgba(249,115,22,.3);'
                f'border-radius:10px;padding:9px 12px;margin-top:6px;font-size:13px;color:#fb923c">'
                f'{ico("bell",14,"#f97316")} <b>{len(_due_now)}</b> تذكير مستحق اليوم</div>',
                unsafe_allow_html=True)

    st.markdown("<div style='position:fixed;bottom:8px;left:8px;font-size:10px;color:#334155;z-index:9999'>v2.1</div>", unsafe_allow_html=True)

    if   page=="السائقون":  pg_drivers(user)
    elif page=="التذكيرات": pg_reminders(user)
    elif page=="المدفوعات": pg_payments()
    elif page=="التقارير":  pg_reports()
    elif page=="الإدارة":   pg_admin()

if __name__=="__main__":
    main()
