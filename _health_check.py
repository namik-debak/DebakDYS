# -*- coding: utf-8 -*-
"""
DYS — Sistem Sağlık Taraması (salt okuma)

Gerçek veritabanı üzerinde tüm GET rotalarını Admin oturumuyla çağırır,
HTTP durum kodlarını raporlar. Hiçbir POST/yazma isteği yapılmaz.
"""
import os
import re
import sys
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

os.environ["DYS_NOTIFICATIONS_ENABLED"] = "false"
os.environ["DYS_SCHEDULER_ENABLED"] = "false"

import app as A  # noqa: E402
from models import SessionLocal, User  # noqa: E402
from sqlalchemy import text  # noqa: E402

PARAM_RE = re.compile(r"<(?:([^:<>]+):)?([^<>]+)>")

# Rota parametresi -> (tablo, birincil anahtar kolonu)
ID_SOURCES = {
    "doc_id": ("documents", "id"),
    "process_id": ("processes", "id"),
    "approval_id": ("document_approvals", "id"),
    "dist_id": ("document_distributions", "id"),
    "disposal_id": ("record_disposals", "id"),
    "user_id": ("users", "id"),
    "capa_id": ("corrective_actions", "id"),
    "audit_id": ("internal_audits", "id"),
    "finding_id": ("audit_findings", "id"),
    "risk_id": ("risk_register", "id"),
    "ppap_id": ("ppap_submissions", "id"),
    "group_id": ("distribution_groups", "id"),
    "kpi_id": ("process_kpis", "id"),
    "fmea_id": ("fmeas", "id"),
    "device_id": ("pokayoke_devices", "id"),
    "claim_id": ("warranty_claims", "id"),
    "qrqc_id": ("qrqc_items", "id"),
    "drill_id": ("emergency_drills", "id"),
    "control_id": ("soa_controls", "id"),
    "req_id": ("requirements", "id"),
    "item_id": ("audit_program_items", "id"),
    "ev_id": ("audit_evidences", "id"),
    "kanit_id": ("audit_ek_kanitlar", "id"),
    "kayit_id": ("calibration_equipment", "id"),
}

LITERAL_VALUES = {
    "fmt": ["xlsx", "csv"],
    "rapor": ["compliance", "inventory"],
    "locale": ["tr", "en"],
    "elem_no": [1],
    "kod": None,      # süreç kodu -> DB'den
    "karar": None,    # atla (yazma etkisi olabilir)
    "filename": None, # statik dosya -> atla
}

# Yan etkisi olan veya anlamlı test edilemeyen GET rotaları
SKIP_ENDPOINTS = {
    "logout",
    "static",
    "set_locale",
}


def first_ids(table, col, limit=1):
    db = SessionLocal()
    try:
        rows = db.execute(
            text(f"SELECT {col} FROM {table} ORDER BY {col} LIMIT :n"), {"n": limit}
        ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []
    finally:
        db.close()


def process_kod():
    db = SessionLocal()
    try:
        r = db.execute(text("SELECT kod FROM processes LIMIT 1")).fetchone()
        return r[0] if r else None
    finally:
        db.close()


def admin_session_values():
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(rol="Admin", aktif=True).first()
        if not u:
            u = db.query(User).filter_by(rol="Admin").first()
        if not u:
            return None
        return {
            "user_id": u.id,
            "rol": u.rol,
            "ad_soyad": u.ad_soyad,
            "departman": u.departman,
        }
    finally:
        db.close()


def build_urls():
    """Her GET rotası için denenecek gerçek URL'leri üretir."""
    urls = []       # (endpoint, url)
    unresolved = []  # (endpoint, rule, sebep)
    kod = process_kod()

    for rule in A.app.url_map.iter_rules():
        methods = {m for m in rule.methods if m not in ("HEAD", "OPTIONS")}
        if "GET" not in methods:
            continue
        if rule.endpoint in SKIP_ENDPOINTS:
            continue

        raw = str(rule)
        parts = PARAM_RE.findall(raw)
        if not parts:
            urls.append((rule.endpoint, raw))
            continue

        # Parametre değerlerini çöz
        values = {}
        ok = True
        reason = ""
        for _conv, name in parts:
            if name in ID_SOURCES:
                table, col = ID_SOURCES[name]
                ids = first_ids(table, col)
                if not ids:
                    ok = False
                    reason = f"{table} tablosu boş"
                    break
                values[name] = ids[0]
            elif name == "kod":
                if not kod:
                    ok = False
                    reason = "süreç kodu yok"
                    break
                values[name] = kod
            elif name in LITERAL_VALUES and LITERAL_VALUES[name]:
                values[name] = LITERAL_VALUES[name][0]
            else:
                ok = False
                reason = f"'{name}' parametresi çözülemedi"
                break

        if not ok:
            unresolved.append((rule.endpoint, raw, reason))
            continue

        url = raw
        for _conv, name in parts:
            url = re.sub(r"<(?:[^:<>]+:)?" + re.escape(name) + r">", str(values[name]), url)
        urls.append((rule.endpoint, url))

    return urls, unresolved


def main():
    A.app.config["TESTING"] = True
    A.app.config["WTF_CSRF_ENABLED"] = False

    sess = admin_session_values()
    if not sess:
        print("HATA: Veritabanında Admin kullanıcı bulunamadı.")
        return 1

    client = A.app.test_client()
    with client.session_transaction() as s:
        s.update(sess)

    urls, unresolved = build_urls()
    print(f"Test edilecek GET rotası: {len(urls)}")
    print(f"Parametresi çözülemeyen (atlanan): {len(unresolved)}\n")

    ok_2xx, redirects, client_err, server_err, exceptions = [], [], [], [], []

    for endpoint, url in sorted(urls, key=lambda x: x[1]):
        try:
            r = client.get(url, follow_redirects=False)
            code = r.status_code
            if 200 <= code < 300:
                ok_2xx.append((code, url, endpoint))
            elif 300 <= code < 400:
                loc = r.headers.get("Location", "")
                redirects.append((code, url, endpoint, loc))
            elif 400 <= code < 500:
                client_err.append((code, url, endpoint))
            else:
                server_err.append((code, url, endpoint))
        except Exception:
            exceptions.append((url, endpoint, traceback.format_exc(limit=6)))

    print("=" * 70)
    print(f"OK (2xx)          : {len(ok_2xx)}")
    print(f"Yönlendirme (3xx) : {len(redirects)}")
    print(f"İstemci hata (4xx): {len(client_err)}")
    print(f"SUNUCU HATA (5xx) : {len(server_err)}")
    print(f"İSTİSNA           : {len(exceptions)}")
    print("=" * 70)

    if server_err:
        print("\n### 500 HATALARI ###")
        for code, url, ep in server_err:
            print(f"  {code}  {url}   [{ep}]")

    if exceptions:
        print("\n### İSTİSNALAR ###")
        for url, ep, tb in exceptions:
            print(f"\n  {url}  [{ep}]")
            for line in tb.strip().splitlines()[-6:]:
                print(f"    {line}")

    if client_err:
        print("\n### 4xx ###")
        for code, url, ep in client_err:
            print(f"  {code}  {url}   [{ep}]")

    if redirects:
        print("\n### 3xx (yetki/akış kaynaklı olabilir) ###")
        for code, url, ep, loc in redirects:
            print(f"  {code}  {url}  ->  {loc}   [{ep}]")

    if unresolved:
        print("\n### ATLANAN (veri yok) ###")
        for ep, rule, reason in unresolved:
            print(f"  {rule}   [{ep}]  — {reason}")

    print("\n### BAŞARILI ROTALAR ###")
    for code, url, ep in ok_2xx:
        print(f"  {code}  {url}")

    return 0 if not server_err and not exceptions else 2


if __name__ == "__main__":
    sys.exit(main())
