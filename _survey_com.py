# -*- coding: utf-8 -*-
import win32com.client
import sqlite3
from pathlib import Path

BASE = Path(r"D:/UYGULAMA PROJELER/debak dijital/dys")
DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"


def resolve(p):
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
    "SELECT dokuman_no, dosya_yolu FROM documents WHERE dokuman_tipi='Talimat' AND dosya_adi LIKE '%.xls'"
)
rows = cur.fetchall()[:3]
cur.execute(
    "SELECT dokuman_no, dosya_yolu FROM documents WHERE dokuman_tipi='Talimat' AND dosya_adi LIKE '%.doc'"
)
rows2 = cur.fetchall()[:3]
conn.close()

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
for no, p in rows:
    fp = resolve(p)
    print("XLS", no, fp)
    wb = excel.Workbooks.Open(str(fp))
    ws = wb.Worksheets(1)
    ps = ws.PageSetup
    print("  L/H/R footer:", repr(ps.LeftFooter), repr(ps.CenterFooter), repr(ps.RightFooter))
    print("  L/H/R header:", repr(ps.LeftHeader), repr(ps.CenterHeader), repr(ps.RightHeader))
    wb.Close(False)
excel.Quit()

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
for no, p in rows2:
    fp = resolve(p)
    print("DOC", no, fp)
    doc = word.Documents.Open(str(fp))
    sec = doc.Sections(1)
    for which, name in [(1, "primary footer"), (2, "first page footer"), (3, "even footer")]:
        ft = sec.Footers(which).Range.Text.strip()
        if ft:
            print(" ", name, repr(ft[:120]))
    for which, name in [(1, "primary header"), (2, "first page header"), (3, "even header")]:
        hd = sec.Headers(which).Range.Text.strip()
        if hd:
            print(" ", name, repr(hd[:120]))
    doc.Close(False)
word.Quit()
