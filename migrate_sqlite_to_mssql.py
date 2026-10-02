"""
SQLite (dys.db) → MS SQL Server (DBKDYS) veri aktarımı
======================================================
1) Hedefte tabloları oluşturur (create_all)
2) SQLite'taki tüm tabloları FK sırasına göre kopyalar
3) IDENTITY insert için SET IDENTITY_INSERT kullanır

Kullanım (proje kökünde, .env hazır):
    python migrate_sqlite_to_mssql.py
    python migrate_sqlite_to_mssql.py --sqlite dys.db
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, create_engine, inspect, text
# dotenv + Config
from config import Config
from models import Base, init_db


def _sqlite_url(path: str) -> str:
    path = os.path.abspath(path)
    return f"sqlite:///{path.replace(os.sep, '/')}"


def _table_order(metadata):
    """FK bağımlılık sırası (ebeveyn önce)."""
    return list(metadata.sorted_tables)


def _python_type(col):
    t = col.type
    for _ in range(5):
        if isinstance(t, (DateTime, Date, Boolean)):
            return type(t)
        impl = getattr(t, "impl", None)
        if impl is None or impl is t:
            break
        t = impl
    return type(col.type)


def _parse_dt(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime(val.year, val.month, val.day)
    if isinstance(val, (int, float)):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null"):
        return None
    if s.endswith("Z"):
        s = s[:-1]
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _parse_date(val):
    dt = _parse_dt(val)
    if dt is None:
        return None
    return dt.date() if isinstance(dt, datetime) else dt


def _coerce_row(row, table):
    out = {}
    for col in table.columns:
        val = row[col.name] if col.name in row else None
        kind = _python_type(col)
        if kind is DateTime:
            out[col.name] = _parse_dt(val)
        elif kind is Date:
            out[col.name] = _parse_date(val)
        elif kind is Boolean:
            if val is None:
                out[col.name] = None
            else:
                out[col.name] = bool(val) if not isinstance(val, str) else val.strip().lower() in (
                    "1", "true", "yes", "on",
                )
        else:
            out[col.name] = val
    return out


def _copy_table(src_conn, dst_conn, table, identity: bool) -> int:
    # SQLite: çift tırnak; köşeli parantez de çoğu sürücüde çalışır
    rows = src_conn.execute(text(f'SELECT * FROM "{table.name}"')).mappings().all()
    if not rows:
        return 0

    cols = [c.name for c in table.columns]
    # Kaynakta olmayan kolonları atla (şema farkı)
    src_keys = set(rows[0].keys())
    cols = [c for c in cols if c in src_keys]
    col_list = ", ".join(f"[{c}]" for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    insert_sql = text(f"INSERT INTO [{table.name}] ({col_list}) VALUES ({placeholders})")

    dialect = dst_conn.dialect.name
    if identity and dialect == "mssql":
        dst_conn.execute(text(f"SET IDENTITY_INSERT [{table.name}] ON"))

    batch = []
    for r in rows:
        coerced = _coerce_row(r, table)
        batch.append({c: coerced[c] for c in cols})
        if len(batch) >= 100:
            dst_conn.execute(insert_sql, batch)
            batch.clear()
    if batch:
        dst_conn.execute(insert_sql, batch)

    if identity and dialect == "mssql":
        dst_conn.execute(text(f"SET IDENTITY_INSERT [{table.name}] OFF"))

    return len(rows)


def _has_identity(table) -> bool:
    return any(getattr(c, "autoincrement", False) and c.primary_key for c in table.columns)


def migrate(sqlite_path: str):
    if not os.path.isfile(sqlite_path):
        print(f"[HATA] SQLite bulunamadı: {sqlite_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[..] Kaynak SQLite: {sqlite_path}")
    print(f"[..] Hedef MSSQL  : {Config.DATABASE_URL.split('@')[-1] if '@' in str(Config.DATABASE_URL) else Config.DATABASE_URL}")

    # 1) Bağlantı + şema (önceki yarım create_all varsa temizle)
    engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as c:
        row = c.execute(text("SELECT DB_NAME(), @@SERVERNAME")).fetchone()
        print(f"[OK] Bağlantı: {row}")

    print("[..] Mevcut tablolar temizleniyor (drop_all)...")
    Base.metadata.drop_all(bind=engine)
    init_db()
    print("[OK] Tablolar oluşturuldu / doğrulandı")

    src = create_engine(_sqlite_url(sqlite_path), future=True)
    dst = create_engine(Config.DATABASE_URL, pool_pre_ping=True, future=True)

    src_insp = inspect(src)
    src_tables = set(src_insp.get_table_names())

    total = 0
    with src.connect() as sc, dst.begin() as dc:
        for table in _table_order(Base.metadata):
            if table.name not in src_tables:
                print(f"  - {table.name}: kaynakta yok, atlandı")
                continue
            # Hedefi temizle (yeniden çalıştırılabilirlik)
            if dc.dialect.name == "mssql":
                dc.execute(text(f"DELETE FROM [{table.name}]"))
            else:
                dc.execute(text(f"DELETE FROM {table.name}"))
            n = _copy_table(sc, dc, table, identity=_has_identity(table))
            total += n
            print(f"  + {table.name}: {n} satır")

    print(f"[OK] Aktarım tamam: {total} satır")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sqlite", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dys.db"))
    args = p.parse_args()
    migrate(args.sqlite)


if __name__ == "__main__":
    main()
