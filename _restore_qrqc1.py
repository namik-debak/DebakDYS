# -*- coding: utf-8 -*-
"""
Sağlık taraması sırasında GET ile tetiklenen qrqc_close işlemini geri alır.

QRQC-2026-001 kaydı 2026-08-07 08:48:56'da yanlışlıkla "Kapatıldı" durumuna
geçirildi. Bağlı DÖF (DÖF-2026-100) hâlâ "Devam Ediyor" olduğundan kayıt
"DÖF Tetiklendi" durumuna döndürülür.

Denetim izi hash zincirli olduğu için hatalı kayıt SİLİNMEZ; zincire yeni
bir düzeltme kaydı eklenir.
"""
import os
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

os.environ["DYS_NOTIFICATIONS_ENABLED"] = "false"
os.environ["DYS_SCHEDULER_ENABLED"] = "false"

from app import _audit_record_hash  # noqa: E402
from models import AuditLog, QRQCItem, SessionLocal  # noqa: E402

QRQC_ID = 1
YENI_DURUM = "DÖF Tetiklendi"
# trigger-dof'un QRQC'yi güncellediği an (DÖF-2026-100 oluşturma zamanı)
ONCEKI_GUNCELLEME = datetime(2026, 7, 22, 9, 15, 18, 984026)

db = SessionLocal()
try:
    q = db.get(QRQCItem, QRQC_ID)
    if not q:
        print("QRQC bulunamadı.")
        sys.exit(1)

    print("ÖNCE:")
    print(f"  durum             = {q.durum}")
    print(f"  kapanis_tarihi    = {q.kapanis_tarihi}")
    print(f"  guncelleme_tarihi = {q.guncelleme_tarihi}")
    print(f"  dof_id            = {q.dof_id}")

    eski_durum = q.durum
    q.durum = YENI_DURUM
    q.kapanis_tarihi = None
    q.guncelleme_tarihi = ONCEKI_GUNCELLEME

    detay = (
        f"Düzeltme: {q.qrqc_no} kaydı sistem sağlık taraması sırasında sehven "
        f"'{eski_durum}' durumuna alınmıştı; '{YENI_DURUM}' durumuna geri alındı."
    )
    tarih = datetime.now()
    son = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    onceki_hash = son.kayit_hash if son else None
    db.add(
        AuditLog(
            kullanici_id=1,
            islem_tipi="Düzenleme",
            document_id=None,
            detay=detay,
            ip_adresi="127.0.0.1",
            tarih=tarih,
            onceki_hash=onceki_hash,
            kayit_hash=_audit_record_hash(onceki_hash, 1, "Düzenleme", None, detay, tarih),
        )
    )
    db.commit()

    q = db.get(QRQCItem, QRQC_ID)
    print("\nSONRA:")
    print(f"  durum             = {q.durum}")
    print(f"  kapanis_tarihi    = {q.kapanis_tarihi}")
    print(f"  guncelleme_tarihi = {q.guncelleme_tarihi}")
    print(f"  dof_id            = {q.dof_id}")
    print("\nDenetim izine düzeltme kaydı eklendi.")
finally:
    db.close()
