"""
DYS — Performans Değerlendirme (KPI) ve Uygunsuzluk (CAPA) (2026) — kpi.debak.com'un DYS'deki hali
Arayüz kpi.debak.com'un kendisidir (static/performans: sitenin derlenmiş React uygulaması, dosyalar değiştirilmeden).
Sunulurken yalnız iki yol öneki eklenir: uygulama adresi (/performans/uygulama) ve API adresi (/performans/api).
Sitenin API'si burada DYS veritabanı (pk_* tabloları) üzerinde çalışır:
  GET  /api/state, /api/health, /api/access
  PUT  /api/kpis · DELETE /api/kpis/<id>                       (yönetici)
  PUT  /api/measurements {m, months} · PUT /api/measurements/batch {items} · DELETE /api/measurements/<id>
  PUT  /api/ncrs · POST /api/ncrs/append {ncrs} · DELETE /api/ncrs/<id> (yönetici)
  PUT  /api/state (içe aktarma, yönetici) · POST /api/reset (DYS'de veriyi silmez, güncel durumu döndürür)
  PUT  /api/plant · POST/DELETE /api/people                     (yönetici)
  /api/users…  kullanıcılar DYS'den gelir (DYS oturumu); arayüzdeki kullanıcı / PIN işlemleri DYS'de etkisizdir
Kimlik ve yetki DYS oturumundan: yönetici = Admin / Doküman Kontrol; "Sadece Görüntüleme" veri giremez.
Her NCR DYS DÖF modülüne yansır (pk_veri.dof_esle).
"""
import json
import os
import re
from datetime import datetime

from flask import render_template, request, abort, session, jsonify, Response, send_from_directory, url_for

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action
csrf = getattr(_h, "csrf", None)

from models import PkKpi, PkOlcum  # noqa: E402
import pk_veri  # noqa: E402

KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "performans")
_JS_ONBELLEK = {}


def _yonetici():
    return session.get("rol") in ("Admin", "Doküman Kontrol")


def _giris():
    return session.get("rol") != "Sadece Görüntüleme"


def _kid():
    return f"dys-{session.get('user_id')}"


def _ad():
    return session.get("ad_soyad") or "DYS kullanıcısı"


def _hata(kod, metin):
    return jsonify({"detail": metin}), kod


def _islem(tur, detay):
    db = get_db()
    try:
        log_action(db, tur, detay=detay)
    finally:
        db.close()


# ───────────────────────── Arayüz (sitenin kendisi) ─────────────────────────
@app.route("/performans")
@login_required
def pk_panel():
    """DYS menüsü içinde kpi.debak.com arayüzü. ?yol=/uygunsuzluk/<id> ile doğrudan bir ekrana gidilir."""
    yol = request.args.get("yol") or "/"
    if not yol.startswith("/") or yol.startswith("//"):
        yol = "/"
    return render_template("pk_cerceve.html", yol=yol)


@app.route("/performans/uygulama/assets/<path:dosya>")
@login_required
def pk_varlik(dosya):
    if dosya.endswith(".js"):
        yol = os.path.join(KLASOR, "assets", os.path.basename(dosya))
        if not os.path.exists(yol):
            abort(404)
        anahtar = (yol, os.path.getmtime(yol))
        if anahtar not in _JS_ONBELLEK:
            js = open(yol, encoding="utf-8").read()
            # 1) API adresi: /api/… → <DYS>/performans/api/…   2) yönlendirici tabanı: /performans/uygulama
            js = js.replace("jr(`/api/", "jr(window.__PK_API+`/api/")
            js = js.replace("(0,L.jsx)(kn,{children:", "(0,L.jsx)(kn,{basename:window.__PK_TABAN,children:", 1)
            # 3) oturum kullanıcısı DYS'den (sitenin tarayıcıda hatırladığı kullanıcı ve örnek kişi listesi kullanılmaz)
            js = js.replace("function Mr(){try{", "function Mr(){if(window.__PK_KULLANICI)return window.__PK_KULLANICI;try{", 1)
            js = js.replace("function Cr(e){", "function Cr(e){if(window.__PK_KULLANICI)return e;", 1)
            _JS_ONBELLEK.clear(); _JS_ONBELLEK[anahtar] = js
        return Response(_JS_ONBELLEK[anahtar], mimetype="text/javascript", headers={"Cache-Control": "no-cache"})
    return send_from_directory(os.path.join(KLASOR, "assets"), dosya)


@app.route("/performans/uygulama/")
@app.route("/performans/uygulama/<path:yol>")
@login_required
def pk_uygulama(yol=""):
    if yol == "favicon.svg":
        return send_from_directory(KLASOR, "favicon.svg")
    h = open(os.path.join(KLASOR, "index.html"), encoding="utf-8").read()
    kok = request.script_root or ""
    h = re.sub(r'(src|href)="/', lambda m: f'{m.group(1)}="{kok}/performans/uygulama/', h)
    ayar = (f"<script>window.__PK_API={json.dumps(kok + '/performans')};window.__PK_TABAN={json.dumps(kok + '/performans/uygulama')};"
            f"window.__PK_KULLANICI={json.dumps(_kid())};</script>")
    h = h.replace("<head>", "<head>\n    " + ayar, 1)
    return Response(h, mimetype="text/html", headers={"Cache-Control": "no-cache"})


# ───────────────────────── API (kpi.debak.com ile aynı) ─────────────────────────
@app.route("/performans/api/health")
@login_required
def pk_api_saglik():
    db = get_db()
    try:
        a = pk_veri.ayar(db)
        return jsonify({"ok": True, "sql": True, "plant": a.get("tesis") or "Debak", "seedRev": a.get("seed_rev") or "",
                        "kpis": db.query(PkKpi).count(), "ncrs": db.query(pk_veri_ncr()).count()})
    finally:
        db.close()


def pk_veri_ncr():
    from models import PkNcr
    return PkNcr


@app.route("/performans/api/state", methods=["GET", "PUT"])
@login_required
def pk_api_durum():
    db = get_db()
    try:
        if request.method == "PUT":
            if not _yonetici():
                return _hata(403, "Yalnızca KYS yöneticisi içe aktarabilir.")
            s = request.get_json(force=True) or {}
            R = pk_veri.durum_yaz(db, s, tam=True); db.commit()
            log_action(db, "Düzenleme", detay=f"Performans: tüm veri içe aktarıldı {R}")
        return jsonify(pk_veri.durum_uret(db))
    finally:
        db.close()


@app.route("/performans/api/reset", methods=["POST"])
@login_required
def pk_api_sifirla():
    if not _yonetici():
        return _hata(403, "Yalnızca KYS yöneticisi.")
    db = get_db()
    try:   # DYS'de örnek veriye dönülmez; kayıtlar korunur
        return jsonify(pk_veri.durum_uret(db))
    finally:
        db.close()


@app.route("/performans/api/access")
@login_required
def pk_api_erisim():
    kullanicilar = [{"id": _kid(), "name": _ad(), "role": "admin" if _yonetici() else "user"}]
    if _yonetici():
        kullanicilar[0]["pinHash"] = "dys-oturumu"
    else:   # arayüz yöneticisiz listeye varsayılan yöneticiyi ekler; PIN'le açılamayan yer tutucu verilir
        kullanicilar.append({"id": "dys-yonetici", "name": "KYS yöneticisi (DYS yetkisi)", "role": "admin", "pinHash": "dys-oturumu"})
    return jsonify({"users": kullanicilar, "sessionUserId": _kid()})


@app.route("/performans/api/users", methods=["PUT"])
@app.route("/performans/api/users/<path:uid>", methods=["DELETE"])
@login_required
def pk_api_kullanici(uid=None):
    return pk_api_erisim()     # kullanıcılar ve yetkiler DYS Kullanıcı Yönetimi'nden


@app.route("/performans/api/users/<path:uid>/pin", methods=["PUT"])
@login_required
def pk_api_pin(uid):
    return "", 204


@app.route("/performans/api/plant", methods=["PUT"])
@login_required
def pk_api_tesis():
    if not _yonetici():
        return _hata(403, "Yalnızca KYS yöneticisi.")
    db = get_db()
    try:
        pk_veri.ayar_yaz(db, tesis=((request.get_json(force=True) or {}).get("name") or "Debak")[:80]); db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()


@app.route("/performans/api/people", methods=["POST", "DELETE"])
@login_required
def pk_api_kisi():
    if not _yonetici():
        return _hata(403, "Yalnızca KYS yöneticisi.")
    db = get_db()
    try:
        a = pk_veri.ayar(db); kisiler = list(a.get("kisiler") or [])
        if request.method == "POST":
            ad = ((request.get_json(force=True) or {}).get("name") or "").strip()
            if ad and ad not in kisiler:
                kisiler.append(ad[:120])
        else:
            kisiler = [k for k in kisiler if k != request.args.get("name")]
        pk_veri.ayar_yaz(db, kisiler=kisiler); db.commit()
        return jsonify({"people": kisiler})
    finally:
        db.close()


@app.route("/performans/api/kpis", methods=["PUT"])
@app.route("/performans/api/kpis/<path:kid>", methods=["DELETE"])
@login_required
def pk_api_kpi(kid=None):
    if not _yonetici():
        return _hata(403, "Yalnızca KYS yöneticisi KPI tanımlayabilir.")
    db = get_db()
    try:
        if request.method == "PUT":
            k = request.get_json(force=True) or {}
            if not k.get("id"):
                return _hata(400, "KPI kimliği yok.")
            yeni = db.get(PkKpi, k["id"]) is None
            pk_veri.kpi_yaz(db, k); db.commit()
            log_action(db, "Oluşturma" if yeni else "Düzenleme", detay=f"Performans KPI {k['id']} {k.get('name', '')[:80]} · hedef {k.get('targetLabel', '')}")
        else:
            e = db.get(PkKpi, kid)
            if e:
                db.query(PkOlcum).filter(PkOlcum.kpi_id == kid).delete(); db.delete(e); db.commit()
                log_action(db, "Silme", detay=f"Performans KPI {kid} silindi (ölçümleriyle)")
        return jsonify({"ok": True})
    finally:
        db.close()


def _olcum(db, m, aylar):
    m = dict(m, enteredBy=_ad(), enteredAt=m.get("enteredAt") or datetime.utcnow().isoformat(timespec="milliseconds") + "Z")
    return pk_veri.olcum_pencere_yaz(db, m, aylar)


@app.route("/performans/api/measurements", methods=["PUT"])
@app.route("/performans/api/measurements/batch", methods=["PUT"])
@app.route("/performans/api/measurements/<path:mid>", methods=["DELETE"])
@login_required
def pk_api_olcum(mid=None):
    if not _giris():
        return _hata(403, "Veri girme yetkiniz yok.")
    db = get_db()
    try:
        if request.method == "DELETE":
            e = db.get(PkOlcum, mid)
            if e:
                db.delete(e); db.commit(); log_action(db, "Silme", detay=f"Performans ölçümü silindi {e.kpi_id} {e.donem}")
            return jsonify({"ok": True})
        g = request.get_json(force=True) or {}
        ogeler = g.get("items") if request.path.endswith("/batch") else [{"m": g.get("m"), "months": g.get("months")}]
        n = 0
        for o in ogeler or []:
            if o and o.get("m") and o["m"].get("kpiId") and o["m"].get("period"):
                _olcum(db, o["m"], o.get("months")); n += 1
        db.commit()
        log_action(db, "Düzenleme", detay=f"Performans ölçüm girişi: {n} değer" + (f" ({ogeler[0]['m']['kpiId']} {ogeler[0]['m']['period']})" if n == 1 else ""))
        return jsonify({"ok": True, "saved": n})
    finally:
        db.close()


@app.route("/performans/api/ncrs", methods=["PUT"])
@app.route("/performans/api/ncrs/append", methods=["POST"])
@app.route("/performans/api/ncrs/<path:nid>", methods=["DELETE"])
@login_required
def pk_api_ncr(nid=None):
    db = get_db()
    try:
        if request.method == "DELETE":
            if not _yonetici():
                return _hata(403, "Yalnızca KYS yöneticisi DÖF silebilir.")
            no = pk_veri.ncr_sil(db, nid); db.commit()
            if no:
                log_action(db, "Silme", detay=f"Performans uygunsuzluk kaydı {no} silindi")
            return jsonify({"ok": True})
        if not _giris():
            return _hata(403, "Veri girme yetkiniz yok.")
        g = request.get_json(force=True) or {}
        if request.path.endswith("/append"):
            N = pk_veri_ncr()
            var = {(x.kpi_id, x.donem) for x in db.query(N).all()}
            eklenen = []
            for n in g.get("ncrs") or []:
                if n.get("id") and (n.get("kpiId"), n.get("period")) not in var and not db.get(N, n["id"]):
                    pk_veri.ncr_yaz(db, n); var.add((n.get("kpiId"), n.get("period"))); eklenen.append(n.get("number") or n["id"])
            db.commit()
            if eklenen:
                log_action(db, "Oluşturma", detay=f"Performans: otomatik uygunsuzluk kaydı {', '.join(eklenen)[:300]}")
            return jsonify({"ok": True, "added": len(eklenen)})
        if not g.get("id"):
            return _hata(400, "Kayıt kimliği yok.")
        yeni = db.get(pk_veri_ncr(), g["id"]) is None
        pk_veri.ncr_yaz(db, g); db.commit()
        log_action(db, "Oluşturma" if yeni else "Düzenleme", detay=f"Performans uygunsuzluk kaydı {g.get('number', g['id'])} · aşama {g.get('stage', '')}")
        return jsonify({"ok": True})
    finally:
        db.close()


if csrf is not None:   # arayüz JSON ile yazar; kimlik DYS oturum çerezi + aynı köken (SameSite) ile doğrulanır
    for _v in (pk_api_durum, pk_api_sifirla, pk_api_kullanici, pk_api_pin, pk_api_tesis, pk_api_kisi, pk_api_kpi, pk_api_olcum, pk_api_ncr):
        csrf.exempt(_v)


@app.before_request
def _pk_koken_denetimi():
    """CSRF muafiyetinin karşılığı: performans API'sine yazma istekleri yalnız aynı kökenden kabul edilir."""
    if request.path.startswith((request.script_root or "") + "/performans/api/") or request.path.startswith("/performans/api/"):
        if request.method in ("PUT", "POST", "DELETE"):
            kaynak = request.headers.get("Origin") or request.headers.get("Referer") or ""
            if kaynak and not kaynak.startswith(request.host_url.rstrip("/")):
                return _hata(403, "Geçersiz istek kaynağı.")
            if not request.is_json and request.method != "DELETE" and request.content_length:
                return _hata(415, "JSON bekleniyor.")
    return None
