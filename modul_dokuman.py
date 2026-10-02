"""
DYS — Modül ↔ DEBAK doküman eşlemesi (2026)
data/modul_dokumanlari.json: her modül için şirket başlığı, standart maddesi, ilgili prosedür / talimat / formlar.
Modül sayfasının üstünde 'Bağlı dokümanlar' şeridi olarak gösterilir (templates/_modul_dokumanlari.html).
app.py sonunda import edilir.
"""
import json
import os
import time

from flask import request, render_template, abort
from markupsafe import Markup, escape

from app_runtime import host as _host
_h = _host()
app = _h.app
get_db = _h.get_db

_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "modul_dokumanlari.json")
_ON = {"t": 0, "moduller": [], "docs": {}}
GRUP_SIRA = ("El Kitabı", "Politikalar", "Prosedürler", "İş Akışları", "Talimatlar", "Görev Tanımları", "Formlar")  # klasör sırası
ROL_ETIKET = {"prosedur": "Prosedür / İş akışı", "talimat": "Talimat", "form_modul": "Bu ekranda tutulan formlar", "form_ilgili": "İlgili formlar"}


def _yukle():
    if time.time() - _ON["t"] < 60:
        return
    try:
        _ON["moduller"] = json.load(open(_YOL, encoding="utf-8")).get("moduller", []) if os.path.exists(_YOL) else []
    except (OSError, ValueError):
        _ON["moduller"] = []
    from models import Document
    db = get_db()
    try:
        _ON["docs"] = {no: (i, b, d) for i, no, b, d in db.query(Document.id, Document.dokuman_no, Document.baslik, Document.durum).all()}
    finally:
        db.close()
    _ON["t"] = time.time()


def modul_bilgisi(nav_id=None, yol=None):
    """nav id'ye ya da istek yoluna (en uzun önek) göre modül kaydı + dokümanlar (DYS kaydı varsa bağlantılı)."""
    _yukle()
    m = None
    if nav_id:
        m = next((x for x in _ON["moduller"] if x.get("id") == nav_id), None)
    elif yol:
        adaylar = [x for x in _ON["moduller"] if yol == x.get("yol") or yol.startswith(x.get("yol", "~") + "/")]
        m = max(adaylar, key=lambda x: len(x["yol"])) if adaylar else None
    if not m:
        return None
    gruplar = {}
    for d in m.get("dokumanlar", []):
        kayit = _ON["docs"].get(d["no"])
        grup = d.get("grup") or ROL_ETIKET.get(d.get("rol"), "Diğer")
        gruplar.setdefault(grup, []).append({**d, "id": kayit[0] if kayit else None,
                                             "baslik": kayit[1] if kayit else "", "durum": kayit[2] if kayit else None,
                                             "modulde": d.get("kayit") == "modul" or d.get("rol") == "form_modul"})
    sira = lambda g: (next((i for i, k in enumerate(GRUP_SIRA) if g.startswith(k)), 9), g.count("›"), g)
    return {**m, "gruplar": sorted(gruplar.items(), key=lambda kv: sira(kv[0])), "toplam": sum(len(v) for v in gruplar.values())}


def modul_basligi(nav_id, varsayilan):
    """Menüde şirket başlığı (eşleme dosyasında yoksa mevcut başlık)."""
    _yukle()
    m = next((x for x in _ON["moduller"] if x.get("id") == nav_id), None)
    return (m or {}).get("baslik") or varsayilan


def _istek_modulu():
    """Etkin modülün nav id'si: modül ekranı (yol öneki) ya da o modülün Dokümanlar sayfası."""
    if request.endpoint == "modul_dokumanlar":
        return (request.view_args or {}).get("nav_id")
    m = modul_bilgisi(yol=request.path)
    return m["id"] if m else None


def modul_alt(nav_id):
    """Sol menü: her modül başlığının altında her zaman 'Dokümanlar · N' alt başlığı (Dokümanlar sayfasındayken vurgulu).
    Modül başlığının kendisi kayıt ekranını açar."""
    m = modul_bilgisi(nav_id=nav_id)
    if not m:
        return ""
    aktif = request.endpoint == "modul_dokumanlar" and (request.view_args or {}).get("nav_id") == nav_id
    stil = ("display:flex;align-items:center;gap:6px;padding:3px 12px 5px 44px;margin:-2px 8px 2px;font-size:12px;"
            "text-decoration:none;border-radius:6px;")
    renk = "background:var(--bg-secondary);color:var(--color-primary);font-weight:600;" if aktif else "color:var(--text-secondary);opacity:.9;"
    return Markup(f'<a href="{request.script_root}/moduller/{escape(nav_id)}/dokumanlar" class="nav-subitem" style="{stil}{renk}" '
                  f'title="{escape(m["baslik"])} — prosedür, talimat ve formlar">📂 Dokümanlar · {m["toplam"]}</a>')

@app.route("/moduller/<nav_id>/dokumanlar")
@_h.login_required
def modul_dokumanlar(nav_id):
    """Modülün Dokümanlar sekmesi: klasör gruplarına göre, her satırda doğrudan işlem."""
    import modul_routes
    if not modul_routes.modul_acik(nav_id):
        abort(404)
    m = modul_bilgisi(nav_id=nav_id)
    if not m:
        abort(404)
    from models import Document
    db = get_db()
    try:
        ids = [d["id"] for _, liste in m["gruplar"] for d in liste if d.get("id")]
        docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(ids)).all()} if ids else {}
        for d in docs.values():
            db.expunge(d)
    finally:
        db.close()
    return render_template("modul_dokumanlar.html", modul_md=m, docs=docs)


app.jinja_env.globals["modul_bilgisi"] = lambda: modul_bilgisi(yol=request.path)
app.jinja_env.globals["modul_alt"] = modul_alt
app.jinja_env.globals["modul_basligi"] = modul_basligi
