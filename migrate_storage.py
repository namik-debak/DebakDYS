"""
DYS — Tek Seferlik Depolama Migrasyonu
======================================
Eski düz (flat) UPLOAD_FOLDER içinde tutulan dosyaları versiyonlu düzene taşır:
    uploads/documents/<doc_id>/rev<revizyon_no>/<dosya_adi>

Güvenlik gereği dosyalar KOPYALANIR (taşınmaz); orijinaller yerinde kalır ve
yedek olur. Veritabanındaki dosya_yolu alanları yeni konuma güncellenir.
Betik idempotenttir: zaten yeni düzende olan dosyalar atlanır.

Çalıştırma:
    python migrate_storage.py
"""

import os
import shutil

from config import Config
from models import SessionLocal, init_db, Document, DocumentRevision
from helpers import document_storage_dir, file_sha256


def _already_versioned(path):
    if not path:
        return False
    norm = os.path.normpath(path).replace("\\", "/")
    return "/documents/" in norm and "/rev" in norm


def _resolve(path, ad):
    if path and os.path.isabs(path) and os.path.exists(path):
        return path
    if path and os.path.exists(path):
        return path
    fallback = os.path.join(Config.UPLOAD_FOLDER, ad or "")
    return fallback if os.path.exists(fallback) else None


def migrate():
    init_db()

    # 1) Önce salt-okunur olarak plan çıkar (kayıt bilgilerini topla), bağlantıyı kapat.
    db = SessionLocal()
    try:
        rev_kayitlar = [
            (r.id, r.document_id, r.revizyon_no, r.dosya_adi, r.dosya_yolu, r.icerik_hash)
            for r in db.query(DocumentRevision).all()
        ]
        doc_kayitlar = [
            (d.id, d.revizyon_no, d.dosya_adi, d.dosya_yolu)
            for d in db.query(Document).all()
        ]
    finally:
        db.close()

    # 2) Yavaş dosya kopyalama işlemlerini DB kilidi tutmadan yap; güncellemeleri biriktir.
    tasinan = 0
    atlanan = 0
    eksik = 0
    rev_guncelle = []   # (id, yeni_yol, hash)
    doc_guncelle = []   # (id, yeni_yol)

    print(f"[..] {len(rev_kayitlar)} revizyon dosyası kopyalanıyor...", flush=True)
    for i, (rid, doc_id, rev_no, ad, yol, mevcut_hash) in enumerate(rev_kayitlar, 1):
        if i % 200 == 0:
            print(f"    ... {i}/{len(rev_kayitlar)}", flush=True)
        if not ad:
            continue
        if _already_versioned(yol) and yol and os.path.exists(yol):
            atlanan += 1
            continue
        kaynak = _resolve(yol, ad)
        if not kaynak:
            eksik += 1
            continue
        hedef_dir = document_storage_dir(doc_id, rev_no)
        os.makedirs(hedef_dir, exist_ok=True)
        hedef = os.path.join(hedef_dir, ad)
        if os.path.abspath(kaynak) != os.path.abspath(hedef):
            shutil.copy2(kaynak, hedef)
        rev_guncelle.append((rid, hedef, mevcut_hash or file_sha256(hedef)))
        tasinan += 1

    print(f"[..] {len(doc_kayitlar)} doküman dosyası kopyalanıyor...", flush=True)
    for i, (did, rev_no, ad, yol) in enumerate(doc_kayitlar, 1):
        if i % 200 == 0:
            print(f"    ... {i}/{len(doc_kayitlar)}", flush=True)
        if not ad:
            continue
        if _already_versioned(yol) and yol and os.path.exists(yol):
            atlanan += 1
            continue
        kaynak = _resolve(yol, ad)
        if not kaynak:
            eksik += 1
            continue
        hedef_dir = document_storage_dir(did, rev_no)
        os.makedirs(hedef_dir, exist_ok=True)
        hedef = os.path.join(hedef_dir, ad)
        if os.path.abspath(kaynak) != os.path.abspath(hedef):
            shutil.copy2(kaynak, hedef)
        doc_guncelle.append((did, hedef))
        tasinan += 1

    # 3) DB güncellemelerini küçük partiler halinde, kısa transaction'larla uygula.
    print(f"[..] Veritabanı güncelleniyor ({len(rev_guncelle)} rev + {len(doc_guncelle)} doküman)...", flush=True)
    db = SessionLocal()
    try:
        for j, (rid, yeni_yol, h) in enumerate(rev_guncelle, 1):
            db.query(DocumentRevision).filter_by(id=rid).update(
                {"dosya_yolu": yeni_yol, "icerik_hash": h}, synchronize_session=False
            )
            if j % 100 == 0:
                db.commit()
        db.commit()
        for j, (did, yeni_yol) in enumerate(doc_guncelle, 1):
            db.query(Document).filter_by(id=did).update(
                {"dosya_yolu": yeni_yol}, synchronize_session=False
            )
            if j % 100 == 0:
                db.commit()
        db.commit()
    finally:
        db.close()

    print(f"[OK] Migrasyon tamamlandı. Taşınan: {tasinan}, Atlanan: {atlanan}, Eksik/bulunamayan: {eksik}")


if __name__ == "__main__":
    migrate()
