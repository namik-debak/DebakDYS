"""
DYS — ISO 14001 Çevre Yönetim Sistemi Modülü
==============================================
Çevre boyut/etki analizi, çevresel ölçümler (enerji/atık vb.) ve çevre kazaları/olayları.
"""

from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    User, Process, CorrectiveAction, EnvironmentalAspect,
    EnvironmentalMeasurement, EnvironmentalIncident,
    CEVRE_BOYUT_TURLERI, CEVRE_KOSULLARI, CEVRE_OLAY_TURLERI
)

def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol", "Çevre Temsilcisi")

def _int(v):
    if not v:
        return None
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return None

def _float(v):
    if not v:
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None

def _date(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  ÇEVRE BOYUT VE ETKİ SİCİLİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/env/aspects", methods=["GET", "POST"])
@login_required
def env_aspects():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            faaliyet = (request.form.get("faaliyet") or "").strip()
            boyut = (request.form.get("boyut") or "").strip()
            if not faaliyet or not boyut:
                flash("Faaliyet ve Boyut alanları zorunludur.", "error")
                return redirect(url_for("env_aspects"))
                
            olasilik = _int(request.form.get("olasilik")) or 1
            siddet = _int(request.form.get("siddet")) or 1
            onemli_mi = (olasilik * siddet) >= 12 or request.form.get("onemli_mi") == "1"
            
            aspect = EnvironmentalAspect(
                faaliyet=faaliyet,
                boyut=boyut,
                etki=(request.form.get("etki") or "").strip() or None,
                tur=request.form.get("tur") or "Atık",
                kosul=request.form.get("kosul") or "Normal",
                yasam_dongusu=(request.form.get("yasam_dongusu") or "").strip() or None,
                olasilik=olasilik,
                siddet=siddet,
                onemli_mi=onemli_mi,
                operasyonel_kontrol=(request.form.get("operasyonel_kontrol") or "").strip() or None,
                ilgili_surec_id=_int(request.form.get("ilgili_surec_id")),
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(aspect)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Çevre Boyutu eklendi: {aspect.boyut}")
            flash("Çevre boyut ve etki kaydı başarıyla eklendi.", "success")
            return redirect(url_for("env_aspects"))
            
        kayitlar = db.query(EnvironmentalAspect).order_by(EnvironmentalAspect.id.desc()).all()
        processes = db.query(Process).order_by(Process.ad).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "env_aspects.html",
            kayitlar=kayitlar,
            processes=processes,
            users=users,
            boyut_turleri=CEVRE_BOYUT_TURLERI,
            cevre_kosullari=CEVRE_KOSULLARI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ÇEVRESEL ÖLÇÜMLER (ATIK, EMİSYON, SU, ENERJİ)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/env/measurements", methods=["GET", "POST"])
@login_required
def env_measurements():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            deger = _float(request.form.get("deger"))
            limit_deger = _float(request.form.get("limit_deger"))
            
            asim_mi = False
            if deger is not None and limit_deger is not None:
                asim_mi = deger > limit_deger
                
            measurement = EnvironmentalMeasurement(
                tur=request.form.get("tur") or "Atık",
                tarih=_date(request.form.get("tarih")) or date.today(),
                deger=deger,
                birim=(request.form.get("birim") or "").strip() or None,
                limit_deger=limit_deger,
                asim_mi=asim_mi,
                aksiyon=(request.form.get("aksiyon") or "").strip() or None,
                capa_id=_int(request.form.get("capa_id"))
            )
            db.add(measurement)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Çevresel Ölçüm eklendi: {measurement.tur}")
            flash("Çevresel ölçüm kaydı başarıyla eklendi.", "success")
            return redirect(url_for("env_measurements"))
            
        kayitlar = db.query(EnvironmentalMeasurement).order_by(EnvironmentalMeasurement.id.desc()).all()
        capas = db.query(CorrectiveAction).order_by(CorrectiveAction.id.desc()).all()
        return render_template(
            "env_measurements.html",
            kayitlar=kayitlar,
            capas=capas,
            boyut_turleri=CEVRE_BOYUT_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ÇEVRE OLAYLARI / SIZINTI / ACİL DURUM
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/env/incidents", methods=["GET", "POST"])
@login_required
def env_incidents():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            tanim = (request.form.get("tanim") or "").strip()
            if not tanim:
                flash("Olay açıklaması zorunludur.", "error")
                return redirect(url_for("env_incidents"))
                
            incident = EnvironmentalIncident(
                olay_no=(request.form.get("olay_no") or "").strip() or None,
                tur=request.form.get("tur") or "Sızıntı/Dökülme",
                tarih=_date(request.form.get("tarih")) or date.today(),
                tanim=tanim,
                etki=(request.form.get("etki") or "").strip() or None,
                aksiyon=(request.form.get("aksiyon") or "").strip() or None,
                tatbikat_mi=request.form.get("tatbikat_mi") == "1",
                capa_id=_int(request.form.get("capa_id")),
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(incident)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Çevre Olayı eklendi: {incident.olay_no or incident.id}")
            flash("Çevre olayı/tatbikatı başarıyla kaydedildi.", "success")
            return redirect(url_for("env_incidents"))
            
        kayitlar = db.query(EnvironmentalIncident).order_by(EnvironmentalIncident.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        capas = db.query(CorrectiveAction).order_by(CorrectiveAction.id.desc()).all()
        return render_template(
            "env_incidents.html",
            kayitlar=kayitlar,
            users=users,
            capas=capas,
            olay_turleri=CEVRE_OLAY_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()
