# -*- coding: utf-8 -*-
import sqlite3
from collections import Counter
from pathlib import Path

DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT dosya_adi FROM documents WHERE dokuman_tipi='Talimat'")
exts = Counter()
for (name,) in cur.fetchall():
    if not name:
        exts["(bos)"] += 1
    else:
        ext = Path(name).suffix.lower() or "(uzantisiz)"
        exts[ext] += 1
print("Dosya turleri:")
for k, v in exts.most_common():
    print(f"  {k}: {v}")
