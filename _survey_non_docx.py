# -*- coding: utf-8 -*-
import sqlite3
import zipfile
from pathlib import Path
from collections import Counter

DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"
BASE = Path(r"D:\UYGULAMA PROJELER\debak dijital\dys")


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


conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    "SELECT dokuman_no, dosya_adi, dosya_yolu FROM documents WHERE dokuman_tipi='Talimat'"
)
by_ext = {"xlsx": [], "xls": [], "doc": []}
for no, name, path in cur.fetchall():
    ext = Path(name or path or "").suffix.lower()
    fp = resolve(path)
    if not fp or not fp.exists():
        continue
    if ext == ".xlsx":
        by_ext["xlsx"].append((no, fp))
    elif ext == ".xls":
        by_ext["xls"].append((no, fp))
    elif ext == ".doc":
        by_ext["doc"].append((no, fp))

print("Counts:", {k: len(v) for k, v in by_ext.items()})

# xlsx sample
try:
    import openpyxl
    for no, fp in by_ext["xlsx"][:3]:
        wb = openpyxl.load_workbook(fp)
        ws = wb.active
        print(f"\nXLSX {no}:")
        print("  oddFooter R:", repr(getattr(ws.oddFooter, "right", None) and ws.oddFooter.right.text))
        print("  oddHeader R:", repr(getattr(ws.oddHeader, "right", None) and ws.oddHeader.right.text))
        # first row sample
        r1 = [ws.cell(1, c).value for c in range(1, 6)]
        print("  row1:", r1)
except Exception as e:
    print("xlsx err", e)

# xls sample with xlrd
try:
    import xlrd
    for no, fp in by_ext["xls"][:3]:
        bk = xlrd.open_workbook(str(fp), formatting_info=True)
        sh = bk.sheet_by_index(0)
        print(f"\nXLS {no}: rows={sh.nrows} cols={sh.ncols}")
        for r in range(min(5, sh.nrows)):
            vals = [sh.cell_value(r, c) for c in range(min(6, sh.ncols))]
            print(" ", vals)
except Exception as e:
    print("xls err", e)
