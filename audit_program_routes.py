"""
DYS — Yıllık iç tetkik programı
================================
Risk temelli yıllık tetkik programı ve kalemleri.
app.py sonunda import edilir (blueprint'siz, geriye uyumlu).
"""
from datetime import date

from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action
from models import (
    User, Process, InternalAudit, AuditProgram, AuditProgramItem,
    AUDIT_PROGRAM_DURUMLARI, AUDIT_PROGRAM_ITEM_DURUMLARI, AUDIT_TIPLERI, STANDARTLAR,
)


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@app.route("/audits/program", methods=["GET", "POST"])
@login_required
def audit_program():
    db = get_db()
    try:
        if request.method == "POST":
            if session.get("rol") not in ("Admin", "Doküman Kontrol"):
                abort(403)
            action = request.form.get("action") or "program"
            if action == "item":
                program_id = _int(request.form.get("program_id"))
                prog = db.query(AuditProgram).get(program_id) if program_id else None
                if not prog:
                    flash("Program bulunamadı.", "error")
                    return redirect(url_for("audit_program"))
                tip = request.form.get("denetim_tipi") or "Sistem Denetimi"
                if tip not in AUDIT_TIPLERI:
                    tip = "Sistem Denetimi"
                db.add(AuditProgramItem(
                    program_id=program_id,
                    planlanan_ay=_int(request.form.get("planlanan_ay")),
                    denetim_tipi=tip,
                    surec_id=_int(request.form.get("surec_id")),
                    ilgili_standart=request.form.get("ilgili_standart") or None,
                    urun_adi=(request.form.get("urun_adi") or "").strip() or None,
                    tetkik_eden_id=_int(request.form.get("tetkik_eden_id")),
                    audit_id=_int(request.form.get("audit_id")),
                    durum=request.form.get("durum") or "Planlandı",
                ))
                db.commit()
                log_action(db, "Oluşturma", detay=f"Tetkik programı kalemi eklendi: {prog.baslik}")
                flash("Program kalemi eklendi.", "success")
            else:
                baslik = (request.form.get("baslik") or "").strip()
                yil = _int(request.form.get("yil")) or date.today().year
                if not baslik:
                    flash("Başlık zorunludur.", "error")
                    return redirect(url_for("audit_program"))
                db.add(AuditProgram(
                    yil=yil,
                    baslik=baslik,
                    kapsam=request.form.get("kapsam") or None,
                    risk_temelli_mi=bool(request.form.get("risk_temelli_mi")),
                    durum=request.form.get("durum") or "Planlandı",
                ))
                db.commit()
                log_action(db, "Oluşturma", detay=f"Tetkik programı eklendi: {baslik}")
                flash("Tetkik programı eklendi.", "success")
            return redirect(url_for("audit_program"))

        programlar = db.query(AuditProgram).order_by(AuditProgram.yil.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        procs = db.query(Process).order_by(Process.kod).all()
        audits = db.query(InternalAudit).order_by(InternalAudit.tetkik_no.desc()).all()
        return render_template(
            "audit_program.html",
            programlar=programlar, users=users, procs=procs, audits=audits,
            DURUMLAR=AUDIT_PROGRAM_DURUMLARI, ITEM_DURUMLAR=AUDIT_PROGRAM_ITEM_DURUMLARI,
            STANDARTLAR=STANDARTLAR, tipler=AUDIT_TIPLERI,
        )
    finally:
        db.close()
