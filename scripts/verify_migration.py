#!/usr/bin/env python3
"""
Compare row counts between two DSNs (source vs target).

Exits 0 when all compared tables match; 2 on mismatch; 1 on usage error.
"""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _engine(url: str):
    from sqlalchemy import create_engine

    kwargs = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def compare(source_url: str, target_url: str, tables: list[str] | None = None) -> int:
    from sqlalchemy import inspect, text

    src = _engine(source_url)
    dst = _engine(target_url)
    src_tables = set(inspect(src).get_table_names())
    dst_tables = set(inspect(dst).get_table_names())
    names = sorted(tables or (src_tables & dst_tables))

    print(f"Source: {source_url}")
    print(f"Target: {target_url}")
    print("-" * 60)

    mismatches = 0
    for name in names:
        if name not in src_tables:
            print(f"  MISS-SRC {name}")
            mismatches += 1
            continue
        if name not in dst_tables:
            print(f"  MISS-DST {name}")
            mismatches += 1
            continue
        with src.connect() as c:
            sc = c.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
        with dst.connect() as c:
            tc = c.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
        status = "OK" if sc == tc else "MISMATCH"
        if sc != tc:
            mismatches += 1
        print(f"  [{status}] {name}: source={sc} target={tc}")

    print("-" * 60)
    if mismatches:
        print(f"{mismatches} table(s) mismatched.")
        return 2
    print("All compared tables match.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare row counts between two DSNs.")
    parser.add_argument("--source", required=True, help="Source DSN")
    parser.add_argument("--target", required=True, help="Target DSN")
    parser.add_argument("--tables", nargs="*", default=None, help="Optional table subset")
    args = parser.parse_args(argv)
    return compare(args.source, args.target, args.tables)


if __name__ == "__main__":
    raise SystemExit(main())
