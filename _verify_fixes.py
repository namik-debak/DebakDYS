# -*- coding: utf-8 -*-
"""Düzeltmeleri canlı sunucu üzerinden doğrular."""
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"

CHECKS = [
    ("GET", "/login", (200,), "Giriş sayfası"),
    ("GET", "/health", (200,), "Sağlık ucu"),
    ("GET", "/healthz", (200,), "Hazırlık ucu"),
    # Artık GET ile tetiklenmemeli -> 405 Method Not Allowed
    ("GET", "/qrqc/1/close", (405,), "QRQC kapatma GET ile engellendi"),
    ("GET", "/qrqc/1/trigger-dof", (405,), "DÖF tetikleme GET ile engellendi"),
    # Oturumsuz erişim login'e yönlenmeli
    ("GET", "/", (301, 302), "Kimlik doğrulama zorunlu"),
    ("GET", "/documents", (301, 302), "Doküman listesi korunuyor"),
]


def request(method, path):
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"HATA: {e}"


ok = fail = 0
for method, path, expected, label in CHECKS:
    # yönlendirmeleri takip etmemek için özel opener
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with opener.open(req, timeout=20) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = f"HATA: {e}"

    good = code in expected
    print(f"  [{'OK   ' if good else 'BAŞARISIZ'}] {method:4s} {path:28s} -> {code} (beklenen {expected})  {label}")
    ok += good
    fail += (not good)

print(f"\nToplam: {ok} başarılı, {fail} başarısız")
