# -*- coding: utf-8 -*-
"""Retry failed .xls talimat updates with Excel restart every N files."""
from __future__ import annotations

import sys
from pathlib import Path as _Path

_VENV_SITE = _Path(r"\\192.168.0.249\ortak\HARUN\dys\.venv\Lib\site-packages")
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

import re
import sqlite3
from pathlib import Path

import openpyxl
import win32com.client

from _bulk_update_talimat_com import (
    backup,
    load_excel_map,
    norm,
    resolve_path,
    update_excel_xls,
)

LOG = Path(r"D:\UYGULAMA PROJELER\debak dijital\dys\_talimat_com_log.txt")
OUT = Path(r"D:\UYGULAMA PROJELER\debak dijital\dys\_talimat_com_retry_log.txt")
DB = r"\\192.168.0.249\ortak\HARUN\dys\dys.db"
BATCH = 15


def failed_nos():
    if not LOG.exists():
        return []
    nos = []
    for line in LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("ERR\t"):
            nos.append(line.split("\t", 2)[1])
    return nos


def main():
    targets = set(failed_nos())
    excel_map = load_excel_map()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT dokuman_no, dosya_yolu, dosya_adi FROM documents WHERE dokuman_tipi='Talimat'"
    )
    jobs = []
    for no, p, name in cur.fetchall():
        if no not in targets:
            continue
        fp = resolve_path(p)
        if fp and fp.suffix.lower() == ".xls":
            key = norm(no)
            if key in excel_map:
                jobs.append((no, fp, excel_map[key]))
    conn.close()

    print(f"Retry jobs: {len(jobs)}")
    lines = []
    ok = err = 0
    excel_app = None

    def start_excel():
        nonlocal excel_app
        if excel_app is not None:
            try:
                excel_app.Quit()
            except Exception:
                pass
        excel_app = win32com.client.Dispatch("Excel.Application")
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

    start_excel()
    try:
        for i, (no, fp, meta) in enumerate(jobs, 1):
            if (i - 1) % BATCH == 0 and i > 1:
                start_excel()
            try:
                line = update_excel_xls(excel_app, fp, meta)
                lines.append(f"OK\t{no}\t{line}")
                ok += 1
            except Exception as e:
                lines.append(f"ERR\t{no}\t{e}")
                err += 1
                # RPC disconnect -> restart excel for next
                if "-2147417848" in str(e) or "-2147418111" in str(e):
                    start_excel()
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)} ok={ok} err={err}")
    finally:
        if excel_app is not None:
            try:
                excel_app.Quit()
            except Exception:
                pass

    summary = f"retry ok={ok} err={err}"
    OUT.write_text(summary + "\n\n" + "\n".join(lines), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
