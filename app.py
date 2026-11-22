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

st.set_page_config(page_title="Workrance", page_icon="🚛", layout="wide",
                   initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════
# CSS — FULLY RESPONSIVE
# ═══════════════════════════════════════════════════════════
st.markdown("""<style>

/* ── BASE ── */
.stApp { direction: rtl; }
.stTextArea textarea, .stTextInput input {
    direction: rtl; font-family: 'Segoe UI', Arial, sans-serif;
}
.stTextArea textarea { line-height: 1.9; font-size: 15px; }
.block-container { padding-top: 1rem !important; }

/* ── COMPONENTS ── */
div[data-testid="metric-container"] {
    background: #111827; border: 1px solid #1f2937;
    border-radius: 10px; padding: 10px 14px;
}
.drv-card {
    background: #111827; border-radius: 10px;
    padding: 12px 16px; margin: 5px 0;
    border-right: 4px solid #374151;
}
.drv-new{border-right-color:#ef4444} .drv-reminder{border-right-color:#f97316}
.drv-check{border-right-color:#eab308} .drv-pending{border-right-color:#f97316}
.drv-partial{border-right-color:#a855f7} .drv-notified{border-right-color:#3b82f6}
.drv-done{border-right-color:#22c55e}

/* ── BUTTONS — touch-friendly globally ── */
.stButton > button {
    min-height: 44px;
    font-family: 'Segoe UI', Arial, sans-serif;
    border-radius: 8px !important;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
}

/* ── TABLET ≤1100px ── */
@media screen and (max-width: 1100px) {
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
    .stButton > button { min-height: 48px !important; font-size: 15px !important; }
    .drv-card { padding: 14px 18px !important; font-size: 14px !important; }
}

/* ── MOBILE ≤768px ── */
@media screen and (max-width: 768px) {
    /* Stack all columns */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.5rem !important;
    }
    [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 100% !important;
        flex: unset !important;
    }
    /* Prevent iOS input zoom — must be ≥16px */
    input, textarea, select { font-size: 16px !important; -webkit-text-size-adjust: 100%; }
    .stTextInput input, .stTextArea textarea,
    .stNumberInput input, .stSelectbox div { font-size: 16px !important; }
    /* Big tap targets */
    .stButton > button {
        min-height: 56px !important;
        font-size: 17px !important;
        border-radius: 12px !important;
        padding: 0 1.4rem !important;
    }
    .stButton > button:active { opacity: 0.75; transform: scale(0.98); }
    /* Cards */
    .drv-card {
        padding: 16px 18px !important;
        margin: 7px 0 !important;
        font-size: 15px !important;
        border-radius: 12px !important;
        border-right-width: 5px !important;
    }
    /* Metrics */
    div[data-testid="metric-container"] {
        padding: 12px !important; border-radius: 12px !important;
    }
    div[data-testid="stMetricLabel"]  { font-size: 11px !important; }
    div[data-testid="stMetricValue"]  { font-size: 20px !important; }
    /* Less container padding */
    .block-container { padding: 0.6rem !important; padding-top: 0.6rem !important; }
    /* Tabs */
    button[data-baseweb="tab"] { font-size: 13px !important; padding: 0.5rem 0.6rem !important; }
    /* Radio bigger tap */
    [data-testid="stRadio"] label    { padding: 10px 6px !important; font-size: 15px !important; }
    [data-testid="stCheckbox"] label { padding: 8px 4px !important; font-size: 14px !important; }
    /* Sidebar */
    section[data-testid="stSidebar"] { min-width: min(85vw, 300px) !important; }
    /* Headers */
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; }
    /* Expander */
    [data-testid="stExpander"] summary { font-size: 15px !important; padding: 0.8rem !important; }
    /* Divider */
    hr { margin: 0.6rem 0 !important; }
}

/* ── SMALL PHONES ≤480px ── */
@media screen and (max-width: 480px) {
    .block-container { padding: 0.4rem !important; }
    .drv-card { padding: 14px !important; }
    .stButton > button { min-height: 54px !important; }
}

</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# HTTP — direct PostgREST (no supabase-py)
# ═══════════════════════════════════════════════════════════
def _base(): return st.secrets["SUPABASE_URL"]

def _h(extra=None):
    k = st.secrets["SUPABASE_KEY"]
    h = {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}
    if extra: h.update(extra)
    return h

def _rh():  # read headers — allow up to 10000 rows
    return _h({"Range-Unit": "items", "Range": "0-9999"})

# ═══════════════════════════════════════════════════════════
# USER SELECT (no login screen)
# ═══════════════════════════════════════════════════════════
def get_user():
    if "user" not in st.session_state or not st.session_state["user"]:
        st.session_state["user"] = "أحمد"
    return st.session_state["user"]

# ═══════════════════════════════════════════════════════════
# DATA — LOAD
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def _viols():
    r = _hx.get(f"{_base()}/rest/v1/violations?select=*", headers=_rh(), timeout=30)
    d = r.json() if r.status_code == 200 else []
    return pd.DataFrame(d) if d else pd.DataFrame()

@st.cache_data(ttl=30)
def _pays():
    r = _hx.get(f"{_base()}/rest/v1/payments?select=*", headers=_rh(), timeout=30)
    d = r.json() if r.status_code == 200 else []
    return pd.DataFrame(d) if d else pd.DataFrame()

@st.cache_data(ttl=30)
def _notifs():
    r = _hx.get(f"{_base()}/rest/v1/notifications?select=*", headers=_rh(), timeout=30)
    d = r.json() if r.status_code == 200 else []
    return pd.DataFrame(d) if d else pd.DataFrame()

@st.cache_data(ttl=30)
def _rems():
    r = _hx.get(f"{_base()}/rest/v1/reminders?select=*", headers=_rh(), timeout=30)
    d = r.json() if r.status_code == 200 else []
    return {f"{x['phone']}_{x['plate']}": x for x in (d or [])}

def bust():
    _viols.clear(); _pays.clear(); _notifs.clear(); _rems.clear()

# ═══════════════════════════════════════════════════════════
# DATA — WRITE
# ═══════════════════════════════════════════════════════════
def upd_status(name, phone, plate, status, notes="", cdate=""):
    d = {"status": status, "updated_at": datetime.now(RIYADH).isoformat()}
    if cdate: d["contact_date"] = cdate
    if notes: d["my_notes"] = notes
    _hx.patch(f"{_base()}/rest/v1/violations",
              params={"driver_name": f"eq.{name}", "phone": f"eq.{phone}", "plate": f"eq.{plate}"},
              json=d, headers=_h({"Prefer": "return=minimal"}), timeout=30)
    bust()

def log_notif(name, phone, plate, ntype, sent_by, notes=""):
    _hx.post(f"{_base()}/rest/v1/notifications",
             json={"driver_name":name,"phone":phone,"plate":plate,
                   "notification_type":ntype,"sent_by":sent_by,
                   "sent_at":datetime.now(RIYADH).isoformat(),"notes":notes},
             headers=_h({"Prefer": "return=minimal"}), timeout=30)
    bust()

def upsert_rem(phone, plate, name, rdate, note, by):
    _hx.post(f"{_base()}/rest/v1/reminders",
             json={"phone":phone,"plate":plate,"driver_name":name,
                   "reminder_date":rdate.isoformat(),"note":note,
                   "created_by":by,"is_done":False},
             headers=_h({"Prefer": "resolution=merge-duplicates,return=minimal"}), timeout=30)
    bust()

def add_payment(vid, name, phone, plate, amt, ptype, method,
                receipt_url, receipt_ref, collector, other_col, verif, pdate, notes):
    _hx.post(f"{_base()}/rest/v1/payments",
             json={"violation_id":vid,"driver_name":name,"phone":phone,"plate":plate,
                   "amount_paid":amt,"payment_type":ptype,"payment_method":method,
                   "receipt_url":receipt_url,"receipt_ref":receipt_ref,
                   "collected_by":collector,"other_collector":other_col,
                   "verification_status":verif,"payment_date":pdate,"notes":notes},
             headers=_h({"Prefer": "return=minimal"}), timeout=30)
    bust()

def confirm_pay(pid):
    _hx.patch(f"{_base()}/rest/v1/payments",
              params={"id": f"eq.{pid}"},
              json={"verification_status":"مؤكد"},
              headers=_h({"Prefer": "return=minimal"}), timeout=30)
    bust()

def upload_receipt(f, pid):
    try:
        ext = f.name.split(".")[-1]
        path = f"receipts/{pid}.{ext}"
        r = _hx.post(f"{_base()}/storage/v1/object/{path}",
                     content=f.read(),
                     headers={"apikey": st.secrets["SUPABASE_KEY"],
                              "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}",
                              "Content-Type": f.type, "x-upsert": "true"},
                     timeout=60)
        if r.status_code in (200, 201):
            return f"{_base()}/storage/v1/object/public/{path}"
        return ""
    except Exception as e:
        st.warning(f"تعذّر رفع الإيصال: {e}")
        return ""

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
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
    if "مرور"  in j: return "مخالفة مرورية"
    if "نقل"   in j: return "مخالفة نقل"
    if "بلد"   in j: return "مخالفة بلدية"
    if "جمارك" in j: return "مخالفة جمركية"
    if "قضائ"  in j: return "إجراء قضائي"
    if "أوزان" in j or "اوزان" in j: return "مخالفة أوزان"
    return j

def wa_link(phone, msg):
    n = wa_num(phone)
    if not n: return None
    return f"https://web.whatsapp.com/send?phone={n}&text={urllib.parse.quote(msg)}"

def wa_btn(url, label, color):
    if not url: return
    st.components.v1.html(f"""
    <style>
    .wb{{width:100%;padding:14px 0;background:{color};color:white;border:none;
    border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer;
    font-family:'Segoe UI',Arial;letter-spacing:0.3px;
    touch-action:manipulation;-webkit-tap-highlight-color:transparent;
    transition:opacity .15s,transform .1s}}
    .wb:hover{{opacity:.88}}
    .wb:active{{opacity:.75;transform:scale(0.97)}}
    @media(max-width:768px){{.wb{{padding:18px 0;font-size:18px;border-radius:12px}}}}
    </style>
    <button class="wb" onclick="window.open('{url}','whatsapp_workrance')">{label}</button>
    """, height=58)

def now_sa_str():
    n = datetime.now(RIYADH)
    return n.strftime("%d-%m-%Y"), n.strftime("%H:%M"), n.strftime("%d-%m-%Y %H:%M")

def fmt_sent_at(s):
    try:
        return datetime.fromisoformat(str(s)).astimezone(RIYADH).strftime("%d-%m-%Y %H:%M")
    except: return str(s)[:16]

# ═══════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════
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
    "new":"🔴 جديد","reminder":"🔔 تذكير اليوم","check":"🟡 تشيك",
    "pending":"🟠 معلق","partial":"🟣 دفع جزئي","notified":"🔵 تم التبليغ",
    "done":"🟢 تم","no_contact":"⚫ لا داعي","no_phone":"⚫ بلا رقم","no_wa":"⚫ بلا واتساب",
}
PR = {"reminder":0,"new":1,"check":2,"pending":3,"partial":4,
      "notified":5,"done":6,"no_contact":7,"no_phone":8,"no_wa":9}

# ═══════════════════════════════════════════════════════════
# MESSAGE GENERATION
# ═══════════════════════════════════════════════════════════
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
        remaining  = max(0, total - total_paid)
        lines += ["", "سجل الدفعات:"]
        for p in pays:
            lines.append(f"  • تم سداد {famt(p.get('amount_paid',0))} ريال بتاريخ {p.get('payment_date','')}")
        lines += ["", f"الإجمالي المتبقي: {famt(remaining)}  ريال سعودي"]
    else:
        lines += ["", f"الإجمالي: {famt(total)}  ريال سعودي"]
    lines += [
        "",
        "نرجو سداد المبلغ عن طريق الذهاب لمقر الشركة او عن طريق حوالة بنكية لحساب الشركة وإرسال صورة الإيصال هنا بعد السداد.",
        "",
        "شاكرين تعاونك.",
        "",
        user,
        "شركة اتحاد الشاحنات للنقليات"
    ]
    return "\n".join(lines)

def gen_reminder(name, plate, viols, user, pays=None):
    total = sum(float(v.get("amount",0)) for v in viols if v.get("amount"))
    if pays:
        total_paid = sum(float(p.get("amount_paid",0)) for p in pays)
        remaining  = max(0, total - total_paid)
        amt_str = f"{famt(remaining)} ريال (المتبقي من {famt(total)})"
        pay_lines = "\n".join(f"  • تم سداد {famt(p.get('amount_paid',0))} ريال بتاريخ {p.get('payment_date','')}" for p in pays)
        pay_section = f"\nسجل الدفعات:\n{pay_lines}\n"
    else:
        amt_str = f"{famt(total)} ريال"
        pay_section = ""
    return "\n".join([
        f"السلام عليكم سيد {name}،",
        "",
        f"معك {user} من شركة اتحاد الشاحنات للنقليات.",
        "",
        f"نود التذكير بوجود مخالفات معلقة على المركبة {plate} بقيمة {amt_str}.",
        pay_section,
        "اي تحديثات بخصوص المخالفات؟ يرجى تحديد موعد سداد متوقع.",
        "",
        "شاكرين تعاونك.",
        "",
        user,
        "شركة اتحاد الشاحنات للنقليات"
    ])

# ═══════════════════════════════════════════════════════════
# BUILD DRIVER LIST
# ═══════════════════════════════════════════════════════════
def build_drivers(vdf, pdf, rems, today_iso):
    if vdf.empty: return []
    vdf = vdf.copy()
    vdf["_ph"] = vdf["phone"].apply(lambda x: cp(x) or "بلا رقم")
    vdf["_pl"] = vdf["plate"].apply(lambda x: str(x).strip() if x else "غير محدد")
    groups = {}
    for _, row in vdf.iterrows():
        key=(str(row.get("driver_name","")).strip(), row["_ph"], row["_pl"])
        groups.setdefault(key,[]).append(row.to_dict())
    result=[]
    for key,rows in groups.items():
        name,phone,plate=key
        sk=get_sk([r.get("status","") for r in rows])
        rk=f"{phone}_{plate}"
        if rk in rems and not rems[rk].get("is_done") and str(rems[rk].get("reminder_date","9999"))<=today_iso:
            sk="reminder"
        prows=[r for r in rows if str(r.get("system_status","")).strip()=="معلقة"]
        tp=sum(float(r.get("amount",0)) for r in prows if r.get("amount"))
        dpays=[]
        if not pdf.empty:
            m=(pdf["driver_name"]==name)&(pdf["plate"]==plate)
            dpays=pdf[m].to_dict("records")
        conf_paid=sum(float(p.get("amount_paid",0)) for p in dpays if p.get("verification_status")=="مؤكد")
        remaining=max(0,tp-conf_paid)
        result.append({
            "key":key,"name":name,"phone":phone,"plate":plate,
            "sk":sk,"label":SL.get(sk,sk),
            "rows":rows,"prows":prows,"count":len(rows),
            "tp":tp,"conf_paid":conf_paid,"remaining":remaining,
            "pays":dpays,"rem":rems.get(rk,{}),
        })
    result.sort(key=lambda d:(PR.get(d["sk"],99),d["name"]))
    return result

# ═══════════════════════════════════════════════════════════
# PAGE: السائقون
# ═══════════════════════════════════════════════════════════
def pg_drivers(user):
    vdf=_viols(); pdf=_pays(); ndf=_notifs(); rems=_rems()
    today=date.today(); today_iso=today.isoformat()

    if vdf.empty:
        st.warning("لا توجد بيانات. ارفع إكسل من صفحة الإدارة.")
        return

    drivers=build_drivers(vdf,pdf,rems,today_iso)

    # sidebar filters
    with st.sidebar:
        st.markdown("**الفلتر:**")
        fn=st.checkbox("🔴 جديد",        value=True)
        fr=st.checkbox("🔔 تذكير اليوم", value=True)
        fc=st.checkbox("🟡 تشيك",        value=True)
        fp=st.checkbox("🟠 معلق",        value=True)
        fpa=st.checkbox("🟣 دفع جزئي",   value=True)
        fnt=st.checkbox("🔵 تم التبليغ", value=False)
        fd=st.checkbox("🟢 تم",          value=False)
        st.divider()
        srch=st.text_input("🔍 بحث",placeholder="اسم أو لوحة...")
        st.divider()
        if st.button("🔄 تحديث",use_container_width=True):
            bust(); st.rerun()

    fm={"new":fn,"reminder":fr,"check":fc,"pending":fp,"partial":fpa,"notified":fnt,"done":fd}
    shown=[d for d in drivers
           if fm.get(d["sk"],True)
           and (not srch or srch in d["name"] or srch.upper() in d["plate"].upper())]

    # stats — 2 rows of 3 (mobile-friendly)
    cnt={k:sum(1 for d in drivers if d["sk"]==k) for k in PR}
    items=[("new","🔴 جديد"),("reminder","🔔 تذكير"),("check","🟡 تشيك"),
           ("pending","🟠 معلق"),("notified","🔵 تبليغ"),("done","🟢 تم")]
    r1,r2=st.columns(3),st.columns(3)
    for col,(k,lbl) in zip(r1+r2, items):
        col.metric(lbl,cnt.get(k,0))
    st.divider()

    left,right=st.columns([1,1.6])

    # driver list
    CMAP={"new":"#ef4444","reminder":"#f97316","check":"#eab308","pending":"#f97316",
          "partial":"#a855f7","notified":"#3b82f6","done":"#22c55e"}
    with left:
        st.markdown(f"**السائقون ({len(shown)})**")
        for i,d in enumerate(shown):
            color=CMAP.get(d["sk"],"#6b7280")
            bg="#1a2744" if st.session_state.get("sel")==d["key"] else "#111827"
            rem_disp=famt(d["remaining"]) if d["remaining"]>0 else famt(d["tp"])
            st.markdown(f"""<div class="drv-card drv-{d['sk']}" style="background:{bg}">
                <span style="color:{color};font-weight:bold">{d['label']}</span>
                &nbsp;&nbsp;<strong>{d['name']}</strong><br>
                <small style="color:#9ca3af">📋 {d['plate']} &nbsp;|&nbsp; {d['count']} مخالفة &nbsp;|&nbsp; {rem_disp} ريال</small>
            </div>""",unsafe_allow_html=True)
            if st.button("اختر ←",key=f"d{i}",use_container_width=True):
                st.session_state.sel=d["key"]
                st.session_state.sf=st.session_state.pf=st.session_state.sysv=False
                st.rerun()

    # driver detail
    with right:
        sk=st.session_state.get("sel")
        sel=next((d for d in drivers if d["key"]==sk),None) if sk else None
        if not sel:
            st.info("👈 اختر سائقاً من القائمة")
            return

        st.markdown(f"## {sel['name']}")
        h1,h2,h3=st.columns(3)
        h1.metric("📱 الجوال",sel["phone"])
        h2.metric("🚗 اللوحة",sel["plate"])
        h3.metric("الحالة",sel["label"])

        # reminder alert
        rem=sel.get("rem",{})
        if rem.get("reminder_date"):
            overdue=str(rem["reminder_date"])<=today_iso
            st.warning(f"{'⚠️ متأخر' if overdue else '⏰'} تذكير: {rem['reminder_date']}"
                       +(f"  —  {rem['note']}" if rem.get("note") else ""))

        # payment summary
        if sel["pays"]:
            conf=[p for p in sel["pays"] if p.get("verification_status")=="مؤكد"]
            pend=[p for p in sel["pays"] if p.get("verification_status")=="بانتظار التأكيد"]
            if conf: st.success(f"✅ مدفوع مؤكد: {famt(sum(float(p.get('amount_paid',0)) for p in conf))} ريال")
            if pend: st.warning(f"⏳ بانتظار المحاسبة: {famt(sum(float(p.get('amount_paid',0)) for p in pend))} ريال")

        st.divider()

        # violations
        st.markdown("**المخالفات:**")
        for i,v in enumerate(sel["rows"],1):
            ss=str(v.get("system_status","")).strip()
            paid="مدفوع" in ss
            st.markdown(
                f"<div style='padding:6px 10px;margin:3px 0;border-radius:5px;background:#111827;"
                f"border-right:3px solid {'#22c55e' if paid else '#ef4444'}'>"
                f"{'🟢' if paid else '🔴'} <b>{i}.</b> {jlbl(v.get('authority'))} | "
                f"{fdt(v.get('violation_date'))} | <b>{famt(v.get('amount'))} ريال</b> | "
                f"{ss} | <code>{v.get('violation_id','')}</code></div>",
                unsafe_allow_html=True)

        if sel["remaining"]>0:
            st.markdown(f"**💰 المتبقي: {famt(sel['remaining'])} ريال**")
        elif sel["tp"]>0:
            st.markdown(f"**💰 الإجمالي المعلق: {famt(sel['tp'])} ريال**")

        # notification log
        if not ndf.empty:
            dn=ndf[(ndf["driver_name"]==sel["name"])&(ndf["plate"]==sel["plate"])].sort_values("sent_at",ascending=False)
            if not dn.empty:
                with st.expander(f"📋 سجل التواصل ({len(dn)} مرة)"):
                    for _,n in dn.iterrows():
                        st.markdown(f"• **{n.get('notification_type','')}** — {fmt_sent_at(n.get('sent_at',''))} — {n.get('sent_by','')}  {('— '+str(n.get('notes',''))) if n.get('notes') else ''}")

        st.divider()

        # messages
        pviols=sel["prows"] if sel["prows"] else sel["rows"]
        conf_pays=[p for p in sel["pays"] if p.get("verification_status")=="مؤكد"]

        notif_msg   = gen_notif(sel["name"],sel["plate"],pviols,user,conf_pays or None)
        reminder_msg= gen_reminder(sel["name"],sel["plate"],pviols,user,conf_pays or None)

        msg_tab,rem_tab=st.tabs(["✉️ مسج التبليغ","🔔 مسج التذكير"])
        with msg_tab:
            edited_notif=st.text_area("",value=notif_msg,height=240,
                                      key=f"mn_{sk}_{user}",label_visibility="collapsed")
        with rem_tab:
            edited_rem=st.text_area("",value=reminder_msg,height=240,
                                    key=f"mr_{sk}_{user}",label_visibility="collapsed")

        # action buttons
        b1,b2,b3,b4=st.columns(4)
        with b1:
            url=wa_link(sel["phone"],edited_notif) if sel["phone"]!="بلا رقم" else None
            if url: wa_btn(url,"📱 تبليغ","#25D366")
            else: st.button("📵 بلا رقم",disabled=True,use_container_width=True)
        with b2:
            rurl=wa_link(sel["phone"],edited_rem) if sel["phone"]!="بلا رقم" else None
            if rurl: wa_btn(rurl,"🔔 تذكير","#3b82f6")
            else: st.button("🔔 تذكير",disabled=True,use_container_width=True)
        with b3:
            if st.button("✅ تم الإرسال",use_container_width=True,key=f"sf_{sk}"):
                st.session_state.sf=True; st.session_state.pf=False
        with b4:
            if st.button("💰 سجل دفع",use_container_width=True,key=f"pf_{sk}"):
                st.session_state.pf=True; st.session_state.sf=False

        b5,b6=st.columns(2)
        with b5:
            if st.button("🔢 أرقام السستم",use_container_width=True,key=f"sv_{sk}"):
                st.session_state.sysv=not st.session_state.get("sysv",False)
        with b6:
            if st.button("✖ إلغاء الاختيار",use_container_width=True,key=f"clr_{sk}"):
                st.session_state.sel=None; st.rerun()

        if st.session_state.get("sysv"):
            st.markdown("**أرقام للسستم:**")
            for v in pviols:
                st.code(f"{v.get('violation_id','')} | {jlbl(v.get('authority'))} | {fdt(v.get('violation_date'))} | {famt(v.get('amount'))} ريال")

        # ── SENT FORM ──
        if st.session_state.get("sf"):
            st.divider()
            st.markdown("**📝 تسجيل الإرسال:**")
            new_st=st.selectbox("الحالة:",["تم التبليغ","معلق","بلا واتساب","بلا رقم","لا داعي للتواصل","تم الدفع"],key=f"nst_{sk}")
            rc1,rc2=st.columns(2)
            with rc1: rd=st.date_input("⏰ تذكير:",value=today+timedelta(days=3),key=f"rd_{sk}")
            nv=st.text_area("📌 ملاحظة:",key=f"nv_{sk}",placeholder="وعد بالدفع / لا يرد / ...")
            sc1,sc2=st.columns(2)
            with sc1:
                if st.button("💾 حفظ",type="primary",key=f"ssv_{sk}",use_container_width=True):
                    today_d,time_d,full_d=now_sa_str()
                    st_txt=f"{new_st} {full_d}"
                    upd_status(sel["name"],sel["phone"],sel["plate"],st_txt,nv,today_d)
                    log_notif(sel["name"],sel["phone"],sel["plate"],"تبليغ",user,nv)
                    upsert_rem(sel["phone"],sel["plate"],sel["name"],rd,nv,user)
                    st.success(f"✅ تم الحفظ")
                    st.session_state.sf=False; st.session_state.sel=None; st.rerun()
            with sc2:
                if st.button("إلغاء",key=f"scc_{sk}",use_container_width=True):
                    st.session_state.sf=False; st.rerun()

        # ── PAYMENT FORM ──
        if st.session_state.get("pf"):
            st.divider()
            st.markdown("**💰 تسجيل دفعة:**")
            pt=st.radio("نوع الدفع:",["كامل","جزئي"],horizontal=True,key=f"pt_{sk}")
            default_amt=float(sel["remaining"]) if sel["remaining"]>0 else float(sel["tp"])
            if pt=="جزئي":
                amt=st.number_input("المبلغ المدفوع (ريال):",min_value=0.01,
                                    value=default_amt/2,key=f"amt_{sk}")
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
                if st.button("💾 حفظ الدفعة",type="primary",key=f"psv_{sk}",use_container_width=True):
                    if amt<=0: st.error("أدخل مبلغاً صحيحاً")
                    else:
                        if rf: rurl=upload_receipt(rf,str(uuid.uuid4())[:8])
                        vid=sel["prows"][0].get("violation_id","") if sel["prows"] else ""
                        add_payment(vid,sel["name"],sel["phone"],sel["plate"],
                                    amt,pt,pm,rurl,rref if pm=="تحويل بنكي" else "",
                                    col,other,verif,pd_.strftime("%d-%m-%Y"),pnts)
                        new_sk="تم الدفع" if pt=="كامل" and verif=="مؤكد" else \
                               "بانتظار تأكيد الدفع" if verif!="مؤكد" else "مدفوع جزئياً"
                        upd_status(sel["name"],sel["phone"],sel["plate"],new_sk)
                        st.success(f"✅ تم تسجيل {famt(amt)} ريال")
                        st.session_state.pf=False; bust(); st.rerun()
            with ps2:
                if st.button("إلغاء",key=f"pcc_{sk}",use_container_width=True):
                    st.session_state.pf=False; st.rerun()

# ═══════════════════════════════════════════════════════════
# PAGE: المدفوعات
# ═══════════════════════════════════════════════════════════
def pg_payments():
    st.markdown("## 💰 المدفوعات")
    df=_pays()
    if df.empty: st.info("لا توجد مدفوعات مسجّلة بعد."); return

    t1,t2=st.tabs(["⏳ بانتظار التأكيد","✅ المؤكدة"])
    with t1:
        pend=df[df["verification_status"]=="بانتظار التأكيد"]
        if pend.empty: st.success("لا يوجد دفعات بانتظار التأكيد ✓")
        else:
            st.markdown(f"**{len(pend)} دفعة بانتظار التأكيد**")
            for _,p in pend.iterrows():
                with st.container():
                    c1,c2,c3,c4=st.columns([3,1,1,1])
                    with c1:
                        st.markdown(f"**{p.get('driver_name','')}** — {p.get('plate','')} — {p.get('payment_date','')}")
                        st.caption(f"طريقة: {p.get('payment_method','')} | جمّع: {p.get('collected_by','')} {p.get('other_collector','')}")
                        if p.get("receipt_ref"): st.caption(f"مرجع: {p.get('receipt_ref','')}")
                        if p.get("receipt_url"): st.markdown(f"[📎 الإيصال]({p.get('receipt_url','')})")
                        if p.get("notes"): st.caption(f"ملاحظة: {p.get('notes','')}")
                    with c2: st.metric("المبلغ",f"{famt(p.get('amount_paid',0))} ر")
                    with c3: st.metric("النوع",p.get("payment_type",""))
                    with c4:
                        if st.button("✅ تأكيد",key=f"cf_{p.get('id','')}",use_container_width=True,type="primary"):
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

# ═══════════════════════════════════════════════════════════
# PAGE: التقارير
# ═══════════════════════════════════════════════════════════
def pg_reports():
    st.markdown("## 📊 التقارير")
    ndf=_notifs(); vdf=_viols(); pdf=_pays()
    today=date.today()

    # ── per-person stats tabs ──
    tab_a, tab_r, tab_all = st.tabs(["👤 أحمد","👤 رهف","🌐 الكل"])

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
    st.markdown("### تقرير مخصص — اختر لوحات وصدّر")
    if vdf.empty: st.info("لا توجد بيانات."); return

    rc1,rc2=st.columns(2)
    with rc1: rep_user=st.selectbox("الموظف:",["أحمد","رهف","الكل"])
    with rc2:
        all_plates=sorted(vdf["plate"].dropna().unique().tolist())
        sel_plates=st.multiselect("أرقام اللوحات:",all_plates,placeholder="اختر أو ابحث...")

    if not st.button("📊 توليد التقرير",type="primary"): return
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
    st.download_button("📥 تحميل التقرير",out,
        file_name=f"تقرير_{rep_user}_{today}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary")

# ═══════════════════════════════════════════════════════════
# PAGE: الإدارة
# ═══════════════════════════════════════════════════════════
def pg_admin():
    st.markdown("## ⚙️ الإدارة")
    t1,t2,t3=st.tabs(["📁 رفع إكسل","➕ إضافة مخالفة","📥 تصدير"])

    # ── UPLOAD & MERGE ──
    with t1:
        st.markdown("### رفع إكسل جديد ودمجه")
        st.info("ستُضاف فقط المخالفات الجديدة — شغلك القديم لن يُمس ✓")
        up=st.file_uploader("ارفع ملف الإكسل (شيت الكل):",type=["xlsx"])
        if up and st.button("🔄 دمج الملف",type="primary"):
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
                            _hx.post(f"{_base()}/rest/v1/violations", json=batch,
                                     headers=_h({"Prefer":"return=minimal"}), timeout=60)
                            added+=len(batch); batch=[]
                    if batch:
                        _hx.post(f"{_base()}/rest/v1/violations", json=batch,
                                 headers=_h({"Prefer":"return=minimal"}), timeout=60)
                        added+=len(batch)
                    bust()
                    st.success(f"✅ {added} مخالفة جديدة أُضيفت | {len(ex_ids)} موجودة مسبقاً لم تُمس")
                except Exception as e:
                    st.error(f"خطأ: {e}")

    # ── MANUAL ADD ──
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
        if st.button("➕ إضافة المخالفة",type="primary"):
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
                             headers=_h({"Prefer":"return=minimal"}), timeout=30)
                    bust()
                    st.success(f"✅ تمت الإضافة — رقم المخالفة: {vid}")
                except Exception as e: st.error(f"خطأ: {e}")

    # ── EXPORT ──
    with t3:
        st.markdown("### تصدير كامل")
        if st.button("📥 تصدير إكسل كامل",type="primary"):
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
            st.download_button("📥 تحميل الملف",out,
                file_name=f"Workrance_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary")

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    for k,v in [("user","أحمد"),("sel",None),("sf",False),("pf",False),("sysv",False)]:
        if k not in st.session_state: st.session_state[k]=v

    with st.sidebar:
        st.markdown("## 🚛 Workrance")
        st.divider()
        chosen=st.radio("أنت؟",["أحمد","رهف"],
                        index=0 if st.session_state["user"]=="أحمد" else 1,
                        horizontal=True)
        if chosen != st.session_state["user"]:
            st.session_state["user"]=chosen
            st.session_state.sel=None
            st.session_state.sf=st.session_state.pf=st.session_state.sysv=False
            st.rerun()
        user=st.session_state["user"]
        st.divider()
        page=st.radio("",[
            "👥 السائقون","💰 المدفوعات","📊 التقارير","⚙️ الإدارة"
        ],label_visibility="collapsed")

    if   page=="👥 السائقون": pg_drivers(user)
    elif page=="💰 المدفوعات": pg_payments()
    elif page=="📊 التقارير":  pg_reports()
    elif page=="⚙️ الإدارة":   pg_admin()

if __name__=="__main__":
    main()
