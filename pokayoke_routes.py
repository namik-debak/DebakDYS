"""
DYS — Poka-Yoke (Hata Önleme) Route'ları
==========================================
IATF 16949 § 10.2.4 uyumlu hata önleme cihaz yönetimi ve periyodik test takibi.
"""

from datetime import date, datetime, timedelta

from flask import (
    render_template, request, redirect, url_for, flash, abort, session,
)

from app_runtime import host as _host

_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    User, Process, PokaYokeDevice, PokaYokeTest,
    POKAYOKE_DURUMLARI, POKAYOKE_TIPLERI, POKAYOKE_TEST_SONUCLARI,
)


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Poka-Yoke Liste / Dashboard
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/pokayoke")
@login_required
def pokayoke_list():
    db = get_db()
    try:
        devices = db.query(PokaYokeDevice).order_by(PokaYokeDevice.olusturma_tarihi.desc()).all()
        geciken = [d for d in devices if d.test_gecikti]
        return render_template(
            "pokayoke.html",
            devices=devices,
            geciken=geciken,
            tipler=POKAYOKE_TIPLERI,
            durumlar=POKAYOKE_DURUMLARI,
            test_sonuclari=POKAYOKE_TEST_SONUCLARI,
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Yeni Poka-Yoke Cihazı
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/pokayoke/new", methods=["POST"])
@login_required
def pokayoke_new():
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        periyot = _int(request.form.get("test_periyodu_gun")) or 30
        device = PokaYokeDevice(
            ad=(request.form.get("ad") or "").strip() or "Yeni Cihaz",
            tip=request.form.get("tip") or "Mekanik",
            konum=(request.form.get("konum") or "").strip() or None,
            makine=(request.form.get("makine") or "").strip() or None,
            ilgili_proses_id=_int(request.form.get("ilgili_proses_id")),
            test_periyodu_gun=periyot,
            sonraki_test_tarihi=date.today() + timedelta(days=periyot),
            sorumlu_id=_int(request.form.get("sorumlu_id")),
            aciklama=(request.form.get("aciklama") or "").strip() or None,
        )
        db.add(device)
        db.commit()
        log_action(db, "Oluşturma", detay=f"Poka-Yoke cihazı: {device.ad}")
        flash(f"Poka-Yoke cihazı eklendi: {device.ad}", "success")
        return redirect(url_for("pokayoke_list"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Poka-Yoke Test Kaydı
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/pokayoke/<int:device_id>/test", methods=["POST"])
@login_required
def pokayoke_test(device_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        device = db.query(PokaYokeDevice).get(device_id)
        if not device:
            abort(404)

        sonuc = request.form.get("sonuc") or "Başarılı"
        test = PokaYokeTest(
            device_id=device.id,
            test_tarihi=date.today(),
            sonuc=sonuc,
            tester_id=session.get("kullanici_id"),
            bulgu=(request.form.get("bulgu") or "").strip() or None,
        )
        db.add(test)

        # Cihaz durumunu ve sonraki test tarihini güncelle
        device.son_test_tarihi = date.today()
        if sonuc == "Başarılı":
            periyot = device.test_periyodu_gun or 30
            device.sonraki_test_tarihi = date.today() + timedelta(days=periyot)
            device.durum = "Aktif"
        else:
            device.durum = "Test Başarısız"

        db.commit()
        log_action(db, "Oluşturma", detay=f"Poka-Yoke test: {device.ad} → {sonuc}")
        flash(f"Test kaydı eklendi: {sonuc}", "success")
        return redirect(url_for("pokayoke_list"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Poka-Yoke Cihazı Silme
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/pokayoke/<int:device_id>/delete", methods=["POST"])
@login_required
def pokayoke_delete(device_id):
    if session.get("rol") not in ("Admin",):
        abort(403)
    db = get_db()
    try:
        device = db.query(PokaYokeDevice).get(device_id)
        if not device:
            abort(404)
        ad = device.ad
        db.delete(device)
        db.commit()
        log_action(db, "Silme", detay=f"Poka-Yoke cihazı silindi: {ad}")
        flash(f"Cihaz silindi: {ad}", "success")
        return redirect(url_for("pokayoke_list"))
    finally:
        db.close()
