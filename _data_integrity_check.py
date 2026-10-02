# -*- coding: utf-8 -*-
"""DYS — Veri ve dosya tutarlılığı denetimi (salt okuma)."""
import os
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import sqlite3

DB = "dys.db"
BASE = Path(os.getcwd())

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def resolve(p):
    if not p:
        return None
    path = Path(p)
    if path.exists():
        return path
    p2 = p.replace("/", "\\")
    if "uploads\\documents" in p2:
        rel = p2.split("uploads\\documents", 1)[1].lstrip("\\/")
        c = BASE / "uploads" / "documents" / rel
        if c.exists():
            return c
    return None


print("=" * 70)
print("1) DOKÜMAN DOSYA BÜTÜNLÜĞÜ")
print("=" * 70)
cur.execute(
    "SELECT id, dokuman_no, baslik, dokuman_tipi, durum, dosya_yolu, dosya_adi FROM documents"
)
rows = cur.fetchall()
total = len(rows)
no_path = []
missing = []
ok = 0
for r in rows:
    if not r["dosya_yolu"]:
        no_path.append(r)
        continue
    if resolve(r["dosya_yolu"]):
        ok += 1
    else:
        missing.append(r)

print(f"Toplam doküman      : {total}")
print(f"Dosyası mevcut      : {ok}")
print(f"Dosya yolu boş      : {len(no_path)}")
print(f"DOSYASI BULUNAMAYAN : {len(missing)}")

if missing:
    print("\n  Eksik dosyalar (ilk 25):")
    for r in missing[:25]:
        print(f"    #{r['id']:4d} {r['dokuman_no']:14s} {r['dokuman_tipi']:10s} {r['dosya_adi']}")
    # tip bazlı dağılım
    from collections import Counter
    c = Counter(r["dokuman_tipi"] for r in missing)
    print("\n  Tipe göre eksik dağılımı:")
    for k, v in c.most_common():
        print(f"    {k}: {v}")

if no_path:
    print("\n  Dosya yolu boş olanlar:")
    for r in no_path[:15]:
        print(f"    #{r['id']:4d} {r['dokuman_no']:14s} {r['baslik'][:50]}")

print()
print("=" * 70)
print("2) YETİM KAYITLAR (FK tutarlılığı)")
print("=" * 70)
checks = [
    ("documents.surec_id -> processes",
     "SELECT COUNT(1) FROM documents d LEFT JOIN processes p ON d.surec_id=p.id "
     "WHERE d.surec_id IS NOT NULL AND p.id IS NULL"),
    ("documents.hazirlayan_id -> users",
     "SELECT COUNT(1) FROM documents d LEFT JOIN users u ON d.hazirlayan_id=u.id "
     "WHERE d.hazirlayan_id IS NOT NULL AND u.id IS NULL"),
    ("documents.onaylayan_id -> users",
     "SELECT COUNT(1) FROM documents d LEFT JOIN users u ON d.onaylayan_id=u.id "
     "WHERE d.onaylayan_id IS NOT NULL AND u.id IS NULL"),
    ("document_approvals.document_id -> documents",
     "SELECT COUNT(1) FROM document_approvals a LEFT JOIN documents d ON a.document_id=d.id "
     "WHERE d.id IS NULL"),
    ("document_distributions.document_id -> documents",
     "SELECT COUNT(1) FROM document_distributions x LEFT JOIN documents d ON x.document_id=d.id "
     "WHERE d.id IS NULL"),
    ("document_revisions.document_id -> documents",
     "SELECT COUNT(1) FROM document_revisions x LEFT JOIN documents d ON x.document_id=d.id "
     "WHERE d.id IS NULL"),
]
for label, sql in checks:
    try:
        n = cur.execute(sql).fetchone()[0]
        flag = "OK" if n == 0 else "SORUN"
        print(f"  [{flag:5s}] {label}: {n}")
    except Exception as e:
        print(f"  [HATA ] {label}: {e}")

print()
print("=" * 70)
print("3) MÜKERRER DOKÜMAN NUMARASI")
print("=" * 70)
cur.execute(
    "SELECT dokuman_no, COUNT(1) n FROM documents WHERE dokuman_no IS NOT NULL "
    "GROUP BY dokuman_no HAVING n > 1 ORDER BY n DESC"
)
dups = cur.fetchall()
print(f"  Mükerrer doküman no sayısı: {len(dups)}")
for r in dups[:15]:
    print(f"    {r['dokuman_no']}: {r['n']} kayıt")

print()
print("=" * 70)
print("4) KULLANICI / ROL DURUMU")
print("=" * 70)
cur.execute("SELECT rol, COUNT(1) n, SUM(aktif) aktif FROM users GROUP BY rol")
for r in cur.fetchall():
    print(f"  {r['rol']:24s} toplam={r['n']:3d} aktif={r['aktif']}")
cur.execute("SELECT COUNT(1) FROM users WHERE aktif=1")
print(f"  Toplam aktif kullanıcı: {cur.fetchone()[0]}")

print()
print("=" * 70)
print("5) DENETİM İZİ (audit_logs) ZİNCİRİ")
print("=" * 70)
cur.execute("SELECT COUNT(1) FROM audit_logs")
print(f"  Kayıt sayısı: {cur.fetchone()[0]}")
cur.execute("SELECT MAX(tarih) FROM audit_logs")
print(f"  Son kayıt   : {cur.fetchone()[0]}")

print()
print("=" * 70)
print("6) TARAMA SIRASINDA OLUŞAN YAN ETKİLER")
print("=" * 70)
cur.execute("SELECT id, qrqc_no, durum, kapanis_tarihi, dof_id FROM qrqc_items ORDER BY id")
for r in cur.fetchall():
    print(f"  QRQC #{r['id']} {r['qrqc_no']}: durum={r['durum']} kapanis={r['kapanis_tarihi']} dof_id={r['dof_id']}")
cur.execute(
    "SELECT id, dof_no, baslik, kaynak_tipi, durum FROM corrective_actions ORDER BY id DESC LIMIT 5"
)
print("\n  Son 5 DÖF:")
for r in cur.fetchall():
    print(f"    #{r['id']} {r['dof_no']} [{r['kaynak_tipi']}] {r['durum']} — {r['baslik'][:60]}")

conn.close()
