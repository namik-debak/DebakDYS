# -*- coding: utf-8 -*-
"""Tüm Flask rotalarını ve parametrelerini döker (salt okuma)."""
import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

os.environ.setdefault("DYS_NOTIFICATIONS_ENABLED", "false")
os.environ.setdefault("DYS_SCHEDULER_ENABLED", "false")

import app as A  # noqa: E402

PARAM_RE = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")

rows = []
for rule in A.app.url_map.iter_rules():
    methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
    params = PARAM_RE.findall(str(rule))
    rows.append((str(rule), rule.endpoint, ",".join(methods), ",".join(params)))

rows.sort()
print(f"TOTAL_RULES={len(rows)}")
gets = [r for r in rows if "GET" in r[2]]
print(f"GET_RULES={len(gets)}")
print(f"GET_NO_PARAM={len([r for r in gets if not r[3]])}")

all_params = sorted({p for r in rows for p in r[3].split(',') if p})
print(f"DISTINCT_PARAMS={all_params}")

print("\n--- ALL RULES ---")
for path, ep, methods, params in rows:
    print(f"{methods:20s} {path:60s} {ep:40s} {params}")
