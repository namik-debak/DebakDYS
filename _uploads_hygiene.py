# -*- coding: utf-8 -*-
"""uploads/ klasöründeki geçici ve yedek dosyaları raporlar (salt okuma)."""
import os
from collections import Counter
from pathlib import Path

BASE = Path(r"D:\UYGULAMA PROJELER\debak dijital\dys\uploads")

bak_meta, bak_other, tmp_items = [], [], []
total_bak_bytes = 0

for root, dirs, files in os.walk(BASE):
    for d in list(dirs):
        if d.startswith("_tmp"):
            tmp_items.append(Path(root) / d)
    for f in files:
        p = Path(root) / f
        low = f.lower()
        if low.endswith(".bak_meta"):
            bak_meta.append(p)
            total_bak_bytes += p.stat().st_size
        elif low.endswith((".bak", ".bak2")):
            bak_other.append(p)
            total_bak_bytes += p.stat().st_size
        elif f.startswith("_tmp"):
            tmp_items.append(p)

print("=" * 66)
print("uploads/ HİJYEN RAPORU")
print("=" * 66)
print(f"  .bak_meta (talimat güncelleme yedeği) : {len(bak_meta)} dosya")
print(f"  .bak / .bak2 (eski yedekler)          : {len(bak_other)} dosya")
print(f"  _tmp* (geçici çıkarım artığı)         : {len(tmp_items)} öğe")
print(f"  Yedeklerin kapladığı alan             : {total_bak_bytes / (1024*1024):.1f} MB")

if tmp_items:
    print("\n  Geçici artıklar:")
    for p in tmp_items:
        print(f"    {p}")

if bak_other:
    print("\n  .bak / .bak2 dosyaları:")
    for p in bak_other:
        print(f"    {p}")

ext = Counter(p.suffixes[0] if p.suffixes else "?" for p in bak_meta)
print(f"\n  .bak_meta dağılımı (orijinal uzantıya göre): {dict(ext.most_common(8))}")
