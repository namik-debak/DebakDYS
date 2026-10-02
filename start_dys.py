"""
DYS — Waitress WSGI Sunucusu (NSSM Wrapper)
=============================================
Bu dosya NSSM (Non-Sucking Service Manager) tarafından
Windows servisi olarak çalıştırılır.

Çalıştırmak için:
    python start_dys.py

NSSM Kurulumu:
    nssm install DebakDYS "C:\\Python314\\python.exe"
    nssm set DebakDYS AppParameters "start_dys.py"
    nssm set DebakDYS AppDirectory "C:\\inetpub\\wwwroot\\debak-dijital\\dys"
"""

import os
import sys

# Çalışma dizinini script'in bulunduğu yer yap
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Flask uygulamasını import et
from app import app

if __name__ == "__main__":
    from waitress import serve

    host = os.environ.get("DYS_HOST", "127.0.0.1")
    port = int(os.environ.get("DYS_PORT", "5000"))
    threads = int(os.environ.get("DYS_THREADS", "4"))

    print(f"[START] DYS Waitress sunucusu baslatiliyor http://{host}:{port}")
    print(f"   Threads: {threads}")

    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        url_scheme="http",
        channel_timeout=120,
        cleanup_interval=30,
    )
