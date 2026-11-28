"""
import_new_file.py — استيراد تحديث أحمد المصنّف إلى Supabase
شغّله مرة واحدة بعد إنشاء الملف المصنّف
"""

import sys, io, re, uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx
import openpyxl
from datetime import datetime, date

SUPABASE_URL = "https://uwapmgxpasurmhdoyidb.supabase.co"
SUPABASE_KEY = "sb_secret_oApNiVqATQti8Ec5ot4GHQ_sY-16DdW"
EXCEL_FILE   = "ايكسل\\تحديث اخير احمد - مصنف.xlsx"

def hdr(extra=None):
    h = {"apikey": SUPABASE_KEY,
         "Authorization": f"Bearer {SUPABASE_KEY}",
         "Content-Type": "application/json"}
    if extra: h.update(extra)
    return h

def rh():
    return hdr({"Range-Unit": "items", "Range": "0-9999"})

def norm_plate(p):
    if p is None: return None
    cleaned = re.sub(r'\s+', '', str(p).strip().upper())
    return cleaned if len(cleaned) > 2 else None

def clean_phone(p):
    if not p: return ''
    s = str(p).strip().split('.')[0].replace(' ', '').replace('-', '')
    return s if s.isdigit() else ''

# تحويل التصنيف إلى قيمة status يقرأها get_sk() بالأداة
STATUS_MAP = {
    'مسدد':                  'تم',
    'يجب التذكير':           'تم التبليغ',
    'يجب التذكير - جزئي':   'تم التبليغ',
    'مختلط':                 'تشيك',
    'دفع جزئي':              'مدفوع جزئي',
    'جديد':                  'جديد',
    'بيانات ناقصة':          'جديد',
}

def main():
    client = httpx.Client(timeout=30)
    today_iso = date.today().isoformat()

    # ── 1. جلب جميع المخالفات الموجودة ──
    print("→ جلب المخالفات الموجودة من Supabase...")
    r = client.get(
        f"{SUPABASE_URL}/rest/v1/violations"
        "?select=violation_id,plate,driver_name,phone",
        headers=rh())
    existing = r.json() if r.status_code == 200 else []

    # لوحة (normalized) → قائمة violation_ids
    plate_to_vids = {}
    for v in existing:
        p = norm_plate(v.get('plate'))
        if p:
            plate_to_vids.setdefault(p, []).append(v['violation_id'])
    print(f"  {len(existing)} مخالفة، {len(plate_to_vids)} لوحة فريدة في الـ DB\n")

    # ── 2. قراءة الإكسل المصنّف ──
    print(f"→ قراءة {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    updated = inserted = reminders_set = skipped = errors = 0

    for row in ws.iter_rows(min_row=12, values_only=True):
        if not any(v is not None for v in row[:10]):
            continue

        plate     = norm_plate(row[1])
        plate_raw = str(row[1]).strip() if row[1] else ''
        if not plate:
            skipped += 1
            continue

        name           = str(row[2]).strip() if row[2] else ''
        phone          = clean_phone(row[3])
        classification = str(row[13]).strip() if row[13] else 'جديد'
        warning        = str(row[14]).strip() if row[14] and str(row[14]) not in ('None', '') else ''
        db_status      = STATUS_MAP.get(classification, 'جديد')

        # مبالغ المخالفات بالتصنيف
        baladia       = row[4] if isinstance(row[4], (int, float)) and row[4] else 0
        transport_w   = row[5] if isinstance(row[5], (int, float)) and row[5] else 0
        transport_a   = row[6] if isinstance(row[6], (int, float)) and row[6] else 0
        traffic_pre26 = row[7] if isinstance(row[7], (int, float)) and row[7] else 0
        traffic_26    = row[8] if isinstance(row[8], (int, float)) and row[8] else 0

        vids = plate_to_vids.get(plate, [])

        if vids:
            # ── تحديث المخالفات الموجودة ──
            upd = {"status": db_status,
                   "updated_at": datetime.utcnow().isoformat()}
            if warning:
                upd["my_notes"] = warning

            ids_str = "(" + ",".join(vids) + ")"
            r2 = client.patch(
                f"{SUPABASE_URL}/rest/v1/violations",
                params={"violation_id": f"in.{ids_str}"},
                json=upd,
                headers=hdr({"Prefer": "return=minimal"}))
            if r2.status_code in (200, 204):
                updated += 1
            else:
                errors += 1
                print(f"  ⚠ خطأ تحديث {plate}: {r2.status_code}")

            # ── تذكير لـ "يجب التذكير" ──
            if 'تذكير' in classification and phone:
                r3 = client.post(
                    f"{SUPABASE_URL}/rest/v1/reminders",
                    json={"phone": phone, "plate": plate_raw,
                          "driver_name": name, "reminder_date": today_iso,
                          "note": "متابعة — تم التبليغ سابقاً ولم يُسدَّد",
                          "created_by": "النظام", "is_done": False},
                    headers=hdr({"Prefer": "resolution=merge-duplicates,return=minimal"}))
                if r3.status_code in (200, 201, 204):
                    reminders_set += 1

        else:
            # ── إضافة سجلات جديدة لسائقين غير موجودين ──
            categories = [
                ('مخالفات بلدية',              baladia),
                ('مخالفات وزارة النقل أوزان',  transport_w),
                ('مخالفات هيئة النقل',         transport_a),
                ('مخالفات مرورية قبل 2026',    traffic_pre26),
                ('مخالفات مرورية 2026',        traffic_26),
            ]
            for auth, amt in categories:
                if not amt:
                    continue
                suffix = uuid.uuid4().hex[:6].upper()
                vid = f"MAN-{plate}-{suffix}"
                record = {
                    "violation_id":   vid,
                    "driver_name":    name,
                    "phone":          phone,
                    "plate":          plate_raw,
                    "authority":      auth,
                    "violation_date": "",
                    "amount":         float(amt),
                    "system_status":  "معلقة",
                    "system_notified": "",
                    "match_status":   "مؤكدة",
                    "status":         db_status,
                    "my_notes":       warning,
                    "contact_date":   "",
                    "assigned_to":    "أحمد",
                    "manually_added": True,
                }
                r4 = client.post(
                    f"{SUPABASE_URL}/rest/v1/violations",
                    json=record,
                    headers=hdr({"Prefer": "return=minimal"}))
                if r4.status_code in (200, 201):
                    inserted += 1
                else:
                    errors += 1
                    print(f"  ⚠ خطأ إضافة {plate}/{auth}: {r4.status_code}")

    print(f"\n✅ انتهى الاستيراد")
    print(f"  محدَّث (سائق موجود):   {updated}")
    print(f"  مُضاف (مخالفة جديدة):  {inserted}")
    print(f"  تذكيرات مضبوطة:        {reminders_set}")
    print(f"  متخطّى (بلا لوحة):     {skipped}")
    print(f"  أخطاء:                 {errors}")

if __name__ == "__main__":
    main()
