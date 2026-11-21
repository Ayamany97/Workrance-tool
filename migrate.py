"""
migrate.py — استيراد إكسل الشركة إلى Supabase (مرة واحدة فقط)
شغّله بعد إعداد schema.sql في Supabase
"""

import os, sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from supabase import create_client

# ═══ ضع بيانات Supabase هنا ═══
SUPABASE_URL = "https://uwapmgxpasurmhdoyidb.supabase.co"
SUPABASE_KEY = "sb_secret_oApNiVqATQti8Ec5ot4GHQ_sY-16DdW"
EXCEL_FILE   = "ايكسل الشركة 21-11-2026.xlsx"
# ══════════════════════════════

def clean_phone(p):
    if not p or (isinstance(p, float) and pd.isna(p)): return ''
    return str(p).strip().split('.')[0].replace(' ','').replace('-','')

def fmt_dt(d):
    try:    return pd.to_datetime(d).strftime('%Y-%m-%d')
    except: return str(d).strip() if d and str(d) != 'nan' else ''

def safe_str(v):
    if v is None: return ''
    if isinstance(v, float) and pd.isna(v): return ''
    return str(v).strip()

def detect_assigned(status_val):
    s = safe_str(status_val).lower()
    if 'احمد' in s or 'أحمد' in s: return 'أحمد'
    if 'رهف'  in s:                 return 'رهف'
    return ''

def migrate():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ضع SUPABASE_URL و SUPABASE_KEY في الملف أولاً")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✓ متصل بـ Supabase")

    # اقرأ الإكسل
    print(f"→ جاري قراءة {EXCEL_FILE} ...")
    df = pd.read_excel(EXCEL_FILE, sheet_name='الكل')
    print(f"✓ {len(df)} صف")

    # اجلب المعرفات الموجودة
    existing = sb.table('violations').select('violation_id').execute()
    existing_ids = {r['violation_id'] for r in existing.data}
    print(f"→ موجود في Supabase: {len(existing_ids)}")

    batch, added, skipped, errors = [], 0, 0, 0

    for i, row in df.iterrows():
        vid = safe_str(row.get('رقم المخالفة'))
        if not vid or vid == 'nan':
            skipped += 1
            continue
        if vid in existing_ids:
            skipped += 1
            continue

        try:
            batch.append({
                'violation_id':     vid,
                'driver_name':      safe_str(row.get('السائق')),
                'phone':            clean_phone(row.get('الجوال')),
                'plate':            safe_str(row.get('اللوحة (نظام)')),
                'authority':        safe_str(row.get('الجهة')),
                'violation_date':   fmt_dt(row.get('التاريخ')),
                'amount':           float(row.get('المبلغ', 0)) if not pd.isna(row.get('المبلغ', 0)) else 0,
                'system_status':    safe_str(row.get('حالة السستم')) or 'معلقة',
                'system_notified':  safe_str(row.get('التبليغ (السستم)')),
                'match_status':     safe_str(row.get('حالة المطابقة')) or 'مؤكدة',
                'status':           safe_str(row.get('الحالة')) or 'جديد',
                'my_notes':         safe_str(row.get('ملاحظاتي')),
                'contact_date':     fmt_dt(row.get('تاريخ التواصل')),
                'assigned_to':      detect_assigned(row.get('الحالة')),
                'manually_added':   False,
            })
        except Exception as e:
            errors += 1
            print(f"  ⚠ خطأ في الصف {i}: {e}")
            continue

        if len(batch) >= 50:
            sb.table('violations').insert(batch).execute()
            added += len(batch)
            batch = []
            print(f"  → {added} مُضاف حتى الآن...")

    if batch:
        sb.table('violations').insert(batch).execute()
        added += len(batch)

    print(f"\n✅ انتهى الاستيراد")
    print(f"   مُضاف:    {added}")
    print(f"   متخطّى:   {skipped}")
    print(f"   أخطاء:    {errors}")

if __name__ == "__main__":
    migrate()
