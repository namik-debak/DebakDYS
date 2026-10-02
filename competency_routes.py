"""
DYS — Yetkinlik Matrisi
"""
from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host

_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import RequiredCompetency, TrainingRecord, YETKINLIK_KAPSAM_TIPLERI


def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol")


@app.route("/competency")
@login_required
def competency_matrix():
    db = get_db()
    try:
        kayitlar = (
            db.query(RequiredCompetency)
            .order_by(RequiredCompetency.kapsam_tipi, RequiredCompetency.ad)
            .all()
        )
        egitimler = (
            db.query(TrainingRecord)
            .order_by(TrainingRecord.egitim_tarihi.desc())
            .limit(20)
            .all()
        )
        return render_template(
            "competency.html",
            kayitlar=kayitlar,
            egitimler=egitimler,
            kapsam_tipleri=YETKINLIK_KAPSAM_TIPLERI,
            can_edit=_can_edit(),
        )
    finally:
        db.close()


@app.route("/competency/new", methods=["POST"])
@login_required
def competency_new():
    if not _can_edit():
        abort(403)
    ad = (request.form.get("ad") or "").strip()
    kapsam_tipi = (request.form.get("kapsam_tipi") or "Rol").strip()
    kapsam_deger = (request.form.get("kapsam_deger") or "").strip()
    if not ad or not kapsam_deger:
        flash("Yetkinlik adı ve kapsam değeri zorunludur.", "error")
        return redirect(url_for("competency_matrix"))
    if kapsam_tipi not in YETKINLIK_KAPSAM_TIPLERI:
        kapsam_tipi = "Rol"
    gecerlilik = request.form.get("gecerlilik_ay")
    try:
        gecerlilik_ay = int(gecerlilik) if gecerlilik else None
    except (TypeError, ValueError):
        gecerlilik_ay = None
    db = get_db()
    try:
        rec = RequiredCompetency(
            ad=ad,
            kapsam_tipi=kapsam_tipi,
            kapsam_deger=kapsam_deger,
            gecerlilik_ay=gecerlilik_ay,
            kritik_mi=bool(request.form.get("kritik_mi")),
        )
        db.add(rec)
        db.commit()
        log_action(db, "Oluşturma", detay=f"Yetkinlik eklendi: {ad}")
        flash("Yetkinlik eklendi.", "success")
        return redirect(url_for("competency_matrix"))
    finally:
        db.close()
