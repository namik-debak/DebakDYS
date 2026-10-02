"""
MS SQL üzerinde tabloları oluşturur (create_all + hafif migrate).
Sunucuda .env hazırken:  python init_mssql.py
"""
from models import init_db, engine
from sqlalchemy import text


def main():
    with engine.connect() as conn:
        row = conn.execute(text("SELECT DB_NAME(), @@SERVERNAME")).fetchone()
        print("[OK] Baglanti:", row)
    init_db()
    print("[OK] Tablolar olusturuldu / guncellendi.")


if __name__ == "__main__":
    main()
