# -*- coding: utf-8 -*-
"""Shared meta line helpers for talimat bulk updates."""
from __future__ import annotations

import re
from datetime import datetime

DOC_CODE_RE = re.compile(r"[A-Z]\d{2}(?:\.\d+)?\s*T\s*\d+", re.I)
DATE_RE = re.compile(r"\d{1,2}\.\d{1,2}\.\d{4}")
REV_PAREN_RE = re.compile(r"\(\s*\d+\s*\)")
META_HINT_RE = re.compile(
    r"(dok[üu]man\s*no|rev(?:\.|izyon)?|tarih|[A-Z]\d{2}(?:\.\d+)?\s*T\s*\d+|\(\s*\d+\s*\)|\d{2}\.\d{2}\.\d{4})",
    re.I,
)


def norm(k: str | None) -> str:
    if not k:
        return ""
    return re.sub(r"[\s\-]+", "", str(k).upper())


def fmt_date(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%d.%m.%Y")
    s = str(v).strip()
    if " " in s:
        s = s.split(" ")[0]
    return s


def fmt_rev(v) -> str:
    if v is None or v == "":
        return "0"
    try:
        return str(int(v))
    except (TypeError, ValueError):
        return str(v).strip()


def detect_format(old: str) -> str:
    old = (old or "").strip()
    if re.search(r"dok[üu]man\s*no", old, re.I):
        return "labeled"
    if REV_PAREN_RE.search(old):
        if re.search(r"\(\s*\d+\s*\)\s*_", old):
            if re.search(r"\(\s*\d+\s*\)\s*_", old) and re.search(r"\s+\(\s*\d+\s*\)\s*_", old):
                return "compact_rev_space_underscore"
            return "compact_rev_underscore"
        return "compact_rev_space"
    if DOC_CODE_RE.search(old) and DATE_RE.search(old):
        return "compact_no_rev"
    return "compact_no_rev"


def build_meta_line_from_old(kod: str, rev, tarih, old: str) -> str:
    old = (old or "").strip()
    fmt = detect_format(old)
    rev_s = fmt_rev(rev)
    tarih_s = fmt_date(tarih)
    if fmt == "labeled":
        return f"Doküman No: {kod}    Rev: {rev_s}    Tarih: {tarih_s}"
    if fmt == "compact_rev_space_underscore":
        return f"{kod} ({rev_s})_{tarih_s}"
    if fmt == "compact_rev_underscore":
        return f"{kod}({rev_s})_{tarih_s}"
    if fmt == "compact_rev_space":
        return f"{kod}({rev_s}) {tarih_s}"
    return f"{kod} {tarih_s}"


def paragraph_has_meta(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if DOC_CODE_RE.search(t) or DATE_RE.search(t):
        return True
    if re.search(r"dok[üu]man|revizyon|rev\.|tarih", t, re.I):
        return True
    return False


def strip_excel_footer_codes(text: str) -> str:
    return re.sub(r"&[A-Za-z0-9+-]+", "", text or "").strip()
