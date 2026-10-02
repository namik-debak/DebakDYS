# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, r"\\192.168.0.249\ortak\HARUN\dys\.venv\Lib\site-packages")
import sqlite3
import win32com.client
from _bulk_update_talimat_com import load_excel_map, norm, resolve_path, update_excel_xls

DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT dosya_yolu FROM documents WHERE dokuman_no=?", ("M04-T17",))
p = cur.fetchone()[0]
conn.close()
fp = resolve_path(p)
meta = load_excel_map()[norm("M04-T17")]
excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
try:
    print(update_excel_xls(excel, fp, meta))
finally:
    excel.Quit()
