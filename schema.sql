-- ═══════════════════════════════════════════════════
-- WORKRANCE — Supabase Schema
-- شغّل هذا الملف في Supabase SQL Editor
-- ═══════════════════════════════════════════════════

-- جدول المخالفات الرئيسي
CREATE TABLE IF NOT EXISTS violations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    violation_id TEXT UNIQUE NOT NULL,
    driver_name TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    plate TEXT NOT NULL DEFAULT '',
    authority TEXT DEFAULT '',
    violation_date TEXT DEFAULT '',
    amount NUMERIC DEFAULT 0,
    system_status TEXT DEFAULT 'معلقة',
    system_notified TEXT DEFAULT '',
    match_status TEXT DEFAULT 'مؤكدة',
    status TEXT DEFAULT 'جديد',
    my_notes TEXT DEFAULT '',
    contact_date TEXT DEFAULT '',
    assigned_to TEXT DEFAULT '',
    manually_added BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول المدفوعات
CREATE TABLE IF NOT EXISTS payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    violation_id TEXT DEFAULT '',
    driver_name TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    plate TEXT NOT NULL DEFAULT '',
    amount_paid NUMERIC NOT NULL DEFAULT 0,
    payment_type TEXT NOT NULL DEFAULT 'كامل',
    payment_method TEXT DEFAULT 'تحويل بنكي',
    receipt_url TEXT DEFAULT '',
    receipt_ref TEXT DEFAULT '',
    collected_by TEXT NOT NULL DEFAULT '',
    other_collector TEXT DEFAULT '',
    verification_status TEXT DEFAULT 'بانتظار التأكيد',
    payment_date TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول سجل التواصل
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    driver_name TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    plate TEXT NOT NULL DEFAULT '',
    notification_type TEXT NOT NULL DEFAULT 'تبليغ',
    sent_by TEXT NOT NULL DEFAULT '',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT DEFAULT ''
);

-- جدول التذكيرات
CREATE TABLE IF NOT EXISTS reminders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    phone TEXT NOT NULL DEFAULT '',
    plate TEXT NOT NULL DEFAULT '',
    driver_name TEXT DEFAULT '',
    reminder_date DATE NOT NULL,
    note TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    is_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(phone, plate)
);

-- فهارس للأداء
CREATE INDEX IF NOT EXISTS idx_violations_plate ON violations(plate);
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status);
CREATE INDEX IF NOT EXISTS idx_violations_phone ON violations(phone);
CREATE INDEX IF NOT EXISTS idx_payments_plate ON payments(plate);
CREATE INDEX IF NOT EXISTS idx_payments_verif ON payments(verification_status);
CREATE INDEX IF NOT EXISTS idx_notifs_plate ON notifications(plate);
CREATE INDEX IF NOT EXISTS idx_notifs_sent_at ON notifications(sent_at);

-- تعطيل RLS (الأداة تستخدم service key)
ALTER TABLE violations   DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments     DISABLE ROW LEVEL SECURITY;
ALTER TABLE notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminders    DISABLE ROW LEVEL SECURITY;
