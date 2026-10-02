"""
DYS — Yerel uploads → UNC dosya sunucusu migrasyonu
===================================================
Eski UPLOAD_FOLDER (veya --source) altındaki dosyaları
Config.UPLOAD_FOLDER (hedef UNC) altına kopyalar ve DB yollarını günceller.

Örnek:
  set DYS_UPLOAD_FOLDER=\\\\192.168.0.249\\kalite\\AL DOSYALAR
  python migrate_uploads_to_unc.py --source "D:\\...\\dys\\uploads"

Güvenlik: dosyalar KOPYALANIR (silinmez). Idempotent.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from config import Config
from models import SessionLocal, init_db, Document, DocumentRevision


def _norm(p: str) -> str:
    return os.path.normpath(p).replace("/", "\\") if p else ""


def _copy_if_needed(src: str, dst: str) -> bool:
    if not src or not os.path.isfile(src):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        if os.path.abspath(src) == os.path.abspath(dst) and os.path.isfile(dst):
            return True
    except Exception:
        pass
    if os.path.isfile(dst):
        if os.path.getsize(src) == os.path.getsize(dst):
            return True
    shutil.copy2(src, dst)
    return os.path.isfile(dst)


def _resolve(path, ad, source_root):
    """Kaynak dosya yolunu bul (yalnızca gerçek dosya)."""
    if path and os.path.isfile(path):
        return path

    for root in (source_root, Config.UPLOAD_FOLDER):
        if not root:
            continue
        if ad:
            cand = os.path.join(root, ad)
            if os.path.isfile(cand):
                return cand
        if path:
            lowered = path.replace("/", "\\").lower()
            rel = None
            for marker in ("uploads\\", "uploads/"):
                idx = lowered.find(marker.replace("/", "\\"))
                if idx >= 0:
                    rel = path.replace("/", "\\")[idx + len("uploads\\") :]
                    break
            if rel is None and ("documents\\" in lowered or "documents/" in path.replace("\\", "/").lower()):
                idx = lowered.find("documents\\")
                if idx < 0:
                    idx = path.replace("/", "\\").lower().find("documents\\")
                if idx >= 0:
                    rel = path.replace("/", "\\")[idx:]
            if rel:
                cand2 = os.path.join(root, rel)
                if os.path.isfile(cand2):
                    return cand2
            # düz basename
            base = os.path.basename(path.replace("/", "\\"))
            if base:
                cand3 = os.path.join(root, base)
                if os.path.isfile(cand3):
                    return cand3
    return None


def migrate(source_root: str):
    init_db()
    target_root = Config.UPLOAD_FOLDER
    print(f"[..] Kaynak : {source_root}")
    print(f"[..] Hedef  : {target_root}")

    n_ok = n_skip = n_miss = n_upd = 0

    def remap_path(old_path: str, ad: str, doc_id: int, rev_no: int) -> str | None:
        nonlocal n_ok, n_skip, n_miss
        src = _resolve(old_path, ad, source_root)
        if not src:
            n_miss += 1
            return None
        fname = (ad or os.path.basename(src) or "").strip()
        if not fname:
            n_miss += 1
            return None
        dest_dir = os.path.join(target_root, "documents", str(doc_id), f"rev{rev_no}")
        dest = os.path.join(dest_dir, fname)
        if _copy_if_needed(src, dest):
            if os.path.isfile(dest):
                # yeni kopya vs zaten vardı ayrımı kabaca
                if _norm(old_path) == _norm(dest):
                    n_skip += 1
                else:
                    # boyut aynıysa skip sayılmış olabilir; yine de OK
                    n_ok += 1
                return dest
        n_miss += 1
        return None

    db = SessionLocal()
    try:
        docs = db.query(Document).all()
        revs = db.query(DocumentRevision).all()

        for d in docs:
            new_path = remap_path(d.dosya_yolu, d.dosya_adi, d.id, d.revizyon_no or 0)
            if new_path:
                if _norm(d.dosya_yolu or "") != _norm(new_path):
                    d.dosya_yolu = new_path
                    n_upd += 1
                elif not (d.dosya_yolu or "").startswith("\\\\"):
                    d.dosya_yolu = new_path
                    n_upd += 1
            else:
                # Bozuk UNC klasör yolu (dosya adı yok) temizle / eskiye dokunma
                p = d.dosya_yolu or ""
                if p.startswith("\\\\") and (p.endswith("\\") or not os.path.isfile(p)):
                    # lokal kaynak varsa bırak; yoksa UNC kırık yolu tutma
                    local = _resolve(None, d.dosya_adi, source_root)
                    if local:
                        repaired = remap_path(local, d.dosya_adi, d.id, d.revizyon_no or 0)
                        if repaired:
                            d.dosya_yolu = repaired
                            n_upd += 1

        for r in revs:
            new_path = remap_path(r.dosya_yolu, r.dosya_adi, r.document_id, r.revizyon_no or 0)
            if new_path and _norm(r.dosya_yolu or "") != _norm(new_path):
                r.dosya_yolu = new_path
                n_upd += 1
            elif new_path and not (r.dosya_yolu or "").startswith("\\\\"):
                r.dosya_yolu = new_path
                n_upd += 1

        db.commit()
    finally:
        db.close()

    print(f"[OK] kopyalanan/hazir={n_ok} atlanan={n_skip} eksik={n_miss} db_guncellenen={n_upd}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads"),
        help="Eski uploads kökü",
    )
    args = parser.parse_args()
    if not os.path.isdir(args.source):
        print(f"[HATA] Kaynak klasör yok: {args.source}", file=sys.stderr)
        sys.exit(1)
    migrate(args.source)


if __name__ == "__main__":
    main()
