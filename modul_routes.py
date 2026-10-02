"""
DYS — Modül Yönetimi (2026)
Sol menüdeki modüller yönetici tarafından açılıp kapatılır. Kapatılan modül menüden kalkar ve adresine
erişilemez. Kod ve veriler silinmez (geri açılabilir). Modül listesi base.html menüsünden otomatik çıkarılır.
"""
import os
import re

from flask import render_template, request, redirect, url_for, flash, session, abort

from app_runtime import host as _host

_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import SistemAyar  # noqa: E402

AYAR_ANAHTARI = "kapali_moduller"
# Kapatılamayan temel modüller (sisteme erişim için gerekli)
ZORUNLU = {"nav-dashboard", "nav-documents", "nav-processes", "nav-users", "nav-modules"}
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "base.html")
_CACHE = {"mtime": None, "moduller": [], "kapali": None}


def modul_listesi():
    """base.html menüsünden [{id, url, ad, bolum, zorunlu}] çıkarır."""
    mt = os.path.getmtime(_BASE)
    if _CACHE["mtime"] == mt:
        return _CACHE["moduller"]
    html = open(_BASE, encoding="utf-8-sig").read()
    out, bolum = [], ""
    for m in re.finditer(r"nav-section-title\">\{\{ _\('([^']+)'\) \}\}|<a href=\"\{\{ request\.script_root \}\}(/[^\"]*)\" class=\"nav-item\" id=\"(nav-[\w-]+)\">(.*?)</a>", html, re.S):
        if m.group(1):
            bolum = m.group(1)
            continue
        ad = re.findall(r"_\('([^']+)'\)", m.group(4))
        ad = ad[-1] if ad else m.group(3)
        if "modul_basligi(" in m.group(4):  # şirket başlığı (data/modul_dokumanlari.json)
            try:
                from modul_dokuman import modul_basligi
                ad = modul_basligi(m.group(3), ad)
            except Exception:  # noqa: BLE001
                pass
        out.append({"id": m.group(3), "url": m.group(2) or "/", "ad": ad, "bolum": bolum,
                    "zorunlu": m.group(3) in ZORUNLU})
    _CACHE["mtime"], _CACHE["moduller"] = mt, out
    return out


def kapali_moduller():
    if _CACHE["kapali"] is None:
        db = get_db()
        try:
            a = db.get(SistemAyar, AYAR_ANAHTARI)
            _CACHE["kapali"] = set(filter(None, (a.deger or "").split(","))) if a else set()
        except Exception:  # tablo henüz yoksa (eski veritabanı) tüm modüller açık
            _CACHE["kapali"] = set()
        finally:
            db.close()
    return _CACHE["kapali"]


def modul_acik(nav_id):
    return nav_id in ZORUNLU or nav_id not in kapali_moduller()


app.jinja_env.globals["modul_acik"] = modul_acik


@app.before_request
def _kapali_modul_engeli():
    kapali = kapali_moduller()
    if not kapali or request.endpoint in (None, "static", "login", "logout"):
        return None
    yol = request.path[len(request.script_root):] if request.script_root and request.path.startswith(request.script_root) else request.path
    eslesen = None
    for m in modul_listesi():
        u = m["url"]
        if u != "/" and (yol == u or yol.startswith(u.rstrip("/") + "/")):
            if eslesen is None or len(u) > len(eslesen["url"]):
                eslesen = m
    if eslesen and eslesen["id"] in kapali and not eslesen["zorunlu"]:
        flash(f"'{eslesen['ad']}' modülü kapatılmıştır (Yönetim › Modül Yönetimi).", "warning")
        return redirect(url_for("dashboard"))
    return None


@app.route("/admin/modules", methods=["GET", "POST"])
@login_required
def admin_modules():
    if session.get("rol") != "Admin":
        abort(403)
    moduller = modul_listesi()
    db = get_db()
    try:
        if request.method == "POST":
            acik = set(request.form.getlist("acik"))
            kapali = sorted(m["id"] for m in moduller if not m["zorunlu"] and m["id"] not in acik)
            a = db.get(SistemAyar, AYAR_ANAHTARI)
            eski = set(filter(None, (a.deger or "").split(","))) if a else set()
            if a is None:
                a = SistemAyar(anahtar=AYAR_ANAHTARI); db.add(a)
            a.deger = ",".join(kapali)
            db.commit()
            _CACHE["kapali"] = None
            ad = {m["id"]: m["ad"] for m in moduller}
            yeni_kapali = [ad[i] for i in kapali if i not in eski]
            yeni_acik = [ad[i] for i in eski if i not in kapali and i in ad]
            log_action(db, "Düzenleme", detay=f"Modül yönetimi — kapatılan: {', '.join(yeni_kapali) or '-'}; açılan: {', '.join(yeni_acik) or '-'}")
            flash(f"Kaydedildi. Kapalı modül sayısı: {len(kapali)}.", "success")
            return redirect(url_for("admin_modules"))
        kapali = kapali_moduller()
        bolumler = []
        for m in moduller:
            if not bolumler or bolumler[-1][0] != m["bolum"]:
                bolumler.append((m["bolum"], []))
            bolumler[-1][1].append(m)
        return render_template("admin_modules.html", bolumler=bolumler, kapali=kapali)
    finally:
        db.close()
