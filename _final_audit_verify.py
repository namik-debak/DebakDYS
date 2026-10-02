# -*- coding: utf-8 -*-
"""Denetim izi hash zincirini ve dağıtım parametrelerini doğrular (salt okuma)."""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

os.environ["DYS_NOTIFICATIONS_ENABLED"] = "false"
os.environ["DYS_SCHEDULER_ENABLED"] = "false"

from app import _audit_record_hash  # noqa: E402
from config import Config  # noqa: E402
from models import AuditLog, SessionLocal  # noqa: E402

print("=" * 68)
print("DENETİM İZİ HASH ZİNCİRİ")
print("=" * 68)
db = SessionLocal()
try:
    loglar = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    onceki = None
    bozuk = []
    hashli = 0
    for lg in loglar:
        beklenen = _audit_record_hash(
            onceki, lg.kullanici_id, lg.islem_tipi, lg.document_id, lg.detay, lg.tarih
        )
        if lg.kayit_hash:
            hashli += 1
            if lg.onceki_hash != onceki or lg.kayit_hash != beklenen:
                bozuk.append(lg.id)
            onceki = lg.kayit_hash
    print(f"  Toplam kayıt      : {len(loglar)}")
    print(f"  Hash'li kayıt     : {hashli}")
    print(f"  BOZUK HALKA       : {len(bozuk)} {bozuk[:20] if bozuk else ''}")
    print(f"  Sonuç             : {'ZİNCİR SAĞLAM' if not bozuk else 'ZİNCİR BOZUK'}")
    son = loglar[-1] if loglar else None
    if son:
        print(f"  Son kayıt         : #{son.id} [{son.tarih}] {son.detay}")
finally:
    db.close()

print()
print("=" * 68)
print("DAĞITIM / ORTAK KULLANIM PARAMETRELERİ")
print("=" * 68)
host = os.environ.get("DYS_HOST", "127.0.0.1")
port = os.environ.get("DYS_PORT", "5000")
threads = os.environ.get("DYS_THREADS", "4")

satirlar = [
    ("Ortam (DYS_ENV)", Config.ENV, "production olmalı"),
    ("Üretim modu", Config.IS_PRODUCTION, "True olmalı"),
    ("Sunucu adresi (DYS_HOST)", host, "LAN erişimi için 0.0.0.0"),
    ("Port", port, "-"),
    ("Waitress thread", threads, "8-16 önerilir"),
    ("Veritabanı", Config.DATABASE_URL, "çok kullanıcıda PostgreSQL"),
    ("Otomatik demo veri", Config.AUTO_SEED, "üretimde False"),
    ("Başlangıçta şifre gösterimi", Config.SHOW_STARTUP_CREDENTIALS, "üretimde False"),
    ("HTTPS zorunlu", Config.FORCE_HTTPS, "TLS varsa True"),
    ("Redis", Config.REDIS_URL or "(yok)", "oran sınırı + oturum iptali"),
    ("Oturum iptali aktif", Config.SESSION_REVOKE_ENABLED, "Redis gerekir"),
    ("Oran sınırı deposu", Config.RATE_LIMIT_STORAGE, "çok süreçte Redis"),
    ("SMTP sunucu", Config.SMTP_HOST or "(yok)", "bildirim için gerekli"),
    ("Bildirimler açık", Config.NOTIFICATIONS_ENABLED, "SMTP olmadan sadece log"),
    ("Zamanlanmış görevler", Config.SCHEDULER_ENABLED, "günlük özet için True"),
    ("Uygulama dış adresi", Config.APP_BASE_URL, "e-posta bağlantıları"),
    ("Yükleme klasörü", Config.UPLOAD_FOLDER, "yedekleme kapsamına al"),
    ("Maks. yükleme (MB)", Config.MAX_CONTENT_LENGTH // (1024 * 1024), "-"),
    ("Ters proxy öneki", Config.PREFIX or "(yok)", "IIS/ARR altında /dys"),
    ("Görevler ayrılığı (SoD)", Config.ENFORCE_SEGREGATION_OF_DUTIES, "True önerilir"),
]
for ad, deger, oneri in satirlar:
    print(f"  {ad:30s} = {str(deger):34s} | {oneri}")

# uploads boyutu
print()
total = 0
count = 0
for root, _dirs, files in os.walk(Config.UPLOAD_FOLDER):
    for f in files:
        try:
            total += os.path.getsize(os.path.join(root, f))
            count += 1
        except OSError:
            pass
print(f"  uploads klasörü: {count} dosya, {total / (1024*1024):.1f} MB")
db_size = os.path.getsize("dys.db") / (1024 * 1024) if os.path.exists("dys.db") else 0
print(f"  dys.db boyutu  : {db_size:.1f} MB")
