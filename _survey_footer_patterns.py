# -*- coding: utf-8 -*-
"""Survey footer/header meta patterns in talimat docx files."""
import re
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path

DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"
BASE = Path(r"D:\UYGULAMA PROJELER\debak dijital\dys")

META_RE = re.compile(
    r"(?:Dok[üu]man\s*No|Rev|Revizyon|Tarih|[A-Z]\d{2}(?:\.\d+)?\s*T\d+|\(\d+\)|\d{2}\.\d{2}\.\d{4})",
    re.I,
)


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
        return c if c.exists() else None
    return None


def footer_texts(docx):
    texts = []
    with zipfile.ZipFile(docx) as z:
        for name in z.namelist():
            if "footer" in name.lower() and name.endswith(".xml"):
                data = z.read(name).decode("utf-8", errors="ignore")
                parts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", data)
                joined = "".join(parts).strip()
                if joined:
                    texts.append((name, joined, len(parts)))
    return texts


conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    "SELECT dokuman_no, dosya_yolu FROM documents WHERE dokuman_tipi='Talimat'"
)
patterns = Counter()
examples = {}
checked = 0
for no, p in cur.fetchall():
    fp = resolve(p)
    if not fp or fp.suffix.lower() != ".docx":
        continue
    checked += 1
    fts = footer_texts(fp)
    if not fts:
        patterns["(bos)"] += 1
        continue
    for _, txt, runs in fts:
        key = "compact" if re.search(r"T\d+", txt) and re.search(r"\d{2}\.\d{4}", txt) else "other"
        if "Dok" in txt or "Rev" in txt:
            key = "labeled"
        patterns[key] += 1
        if key not in examples:
            examples[key] = (no, txt, runs)

print(f"Checked docx: {checked}")
print("Patterns:", dict(patterns))
for k, v in examples.items():
    print(f"\n[{k}] {v[0]} runs={v[2]}")
    print(f"  {v[1]!r}")
