# -*- coding: utf-8 -*-
"""Tarama kaynaklı yan etkileri araştır (salt okuma)."""
import os
import sqlite3
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect("dys.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== BUGÜNÜN DENETİM KAYITLARI (2026-08-07) ===")
cur.execute(
    "SELECT id, kullanici_id, islem_tipi, document_id, detay, tarih FROM audit_logs "
    "WHERE tarih >= '2026-08-07' ORDER BY id"
)
for r in cur.fetchall():
    print(f"  #{r['id']} [{r['tarih']}] {r['islem_tipi']:12s} uid={r['kullanici_id']} — {r['detay']}")

print("\n=== QRQC #1 TÜM ALANLAR ===")
cur.execute("SELECT * FROM qrqc_items WHERE id=1")
row = cur.fetchone()
if row:
    for k in row.keys():
        print(f"  {k:26s} = {row[k]}")

print("\n=== QRQC durum dağılımı ===")
cur.execute("SELECT durum, COUNT(1) n FROM qrqc_items GROUP BY durum")
for r in cur.fetchall():
    print(f"  {r['durum']}: {r['n']}")

print("\n=== DÖF #16 TÜM ALANLAR ===")
cur.execute("SELECT * FROM corrective_actions WHERE id=16")
row = cur.fetchone()
if row:
    for k in row.keys():
        v = row[k]
        if isinstance(v, str) and len(v) > 90:
            v = v[:90] + "..."
        print(f"  {k:26s} = {v}")

print("\n=== DÖF #16'ya bağlı alt kayıtlar ===")
for tbl, col in [("audit_findings", "capa_id"), ("qrqc_items", "dof_id")]:
    try:
        n = cur.execute(f"SELECT COUNT(1) FROM {tbl} WHERE {col}=16").fetchone()[0]
        print(f"  {tbl}.{col}=16 -> {n} kayıt")
    except Exception as e:
        print(f"  {tbl}: {e}")

conn.close()
