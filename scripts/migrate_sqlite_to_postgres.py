#!/usr/bin/env python3
"""
Copy tables from a source DSN to a target DSN via SQLAlchemy reflection.

Dry-run by default (no writes). Use --execute to perform the copy.

Examples:
  python scripts/migrate_sqlite_to_postgres.py --help
  python scripts/migrate_sqlite_to_postgres.py \\
      --source sqlite:///dys.db \\
      --target postgresql+psycopg://user:pass@localhost:5432/dys
  python scripts/migrate_sqlite_to_postgres.py --execute ...
"""

from __future__ import annotations

import argparse
import os
import sys

# Project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _engine(url: str):
    from sqlalchemy import create_engine

    kwargs = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def migrate(source_url: str, target_url: str, *, execute: bool, tables: list[str] | None):
    from sqlalchemy import MetaData, Table, inspect, text
    from sqlalchemy.engine import Engine

    src: Engine = _engine(source_url)
    dst: Engine = _engine(target_url)

    src_meta = MetaData()
    src_meta.reflect(bind=src)

    insp_src = inspect(src)
    insp_dst = inspect(dst)

    table_names = tables or list(src_meta.tables.keys())
    # Prefer FK-safe order when reflecting relationships
    try:
        ordered = list(src_meta.sorted_tables)
        ordered_names = [t.name for t in ordered if t.name in table_names]
        for name in table_names:
            if name not in ordered_names:
                ordered_names.append(name)
        table_names = ordered_names
    except Exception:
        pass

    print(f"Source: {source_url}")
    print(f"Target: {target_url}")
    print(f"Mode:   {'EXECUTE' if execute else 'DRY-RUN (default)'}")
    print(f"Tables: {len(table_names)}")
    print("-" * 60)

    summary = []
    for name in table_names:
        if name not in src_meta.tables:
            print(f"  SKIP {name}: not in source")
            continue
        src_table: Table = src_meta.tables[name]
        with src.connect() as conn:
            rows = conn.execute(src_table.select()).mappings().all()
        src_count = len(rows)

        dst_count_before = None
        if name in insp_dst.get_table_names():
            with dst.connect() as conn:
                dst_count_before = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
        else:
            dst_count_before = 0

        print(f"  {name}: source={src_count} target_before={dst_count_before}")

        if execute:
            # Ensure table exists on target (create from reflected source schema)
            dst_meta = MetaData()
            dst_table = Table(name, dst_meta, *[c.copy() for c in src_table.columns])
            for fk in src_table.foreign_keys:
                # Foreign keys may reference tables not yet created; create without FKs first.
                pass
            dst_meta.create_all(bind=dst, tables=[dst_table], checkfirst=True)

            with dst.begin() as conn:
                if rows:
                    conn.execute(dst_table.insert(), [dict(r) for r in rows])

            with dst.connect() as conn:
                dst_count_after = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
        else:
            dst_count_after = dst_count_before

        summary.append((name, src_count, dst_count_before, dst_count_after))

    print("-" * 60)
    print("Reconciliation:")
    ok = True
    for name, src_c, before, after in summary:
        expected = src_c if execute else before
        # In dry-run, report projected target == source for planning
        projected = src_c if not execute else after
        match = (projected == src_c) if not execute else (after == src_c)
        status = "OK" if match else "MISMATCH"
        if not match:
            ok = False
        print(f"  [{status}] {name}: source={src_c} target={projected}"
              + (f" (was {before})" if execute else " (projected)"))
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy SQLite (or any) tables to PostgreSQL via SQLAlchemy reflection."
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("DYS_MIGRATE_SOURCE", os.environ.get("DYS_DATABASE_URL", "sqlite:///dys.db")),
        help="Source DSN (default: DYS_MIGRATE_SOURCE or DYS_DATABASE_URL or sqlite:///dys.db)",
    )
    parser.add_argument(
        "--target",
        default=os.environ.get("DYS_MIGRATE_TARGET", ""),
        help="Target DSN (e.g. postgresql+psycopg://user:pass@host/dys)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform writes (default is dry-run)",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        default=None,
        help="Optional subset of table names",
    )
    args = parser.parse_args(argv)

    if not args.target:
        # Dry-run / help-friendly: allow missing target when only checking CLI
        if not args.execute:
            print("No --target given; dry-run against source only is not supported.")
            print("Provide --target or set DYS_MIGRATE_TARGET. Exiting 0 (scaffold check).")
            return 0
        parser.error("--target is required when using --execute")

    return migrate(args.source, args.target, execute=args.execute, tables=args.tables)


if __name__ == "__main__":
    raise SystemExit(main())
