"""
DYS — ISO 45001 İş Sağlığı ve Güvenliği (OHS) Modülü
======================================================
Tehlike tanımlama ve risk değerlendirme, İSG olayları (kazalar/ramak kalalar), çalışan katılımı ve danışma.
"""

import json
from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    User, Process, CorrectiveAction, OHSHazard, OHSIncident, OHSParticipation,
    PPEItem, PPEIssue, EmergencyDrill,
    ISG_KONTROL_HIYERARSISI, ISG_RISK_DURUMLARI, ISG_OLAY_TURLERI, ISG_KATILIM_TURLERI
)

def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol", "İSG Uzmanı")

def _int(v):
    if not v:
        return None
    try:
        return int(float(str(v)))
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
#  TEHLİKE TANIMLAMA VE RİSK DEĞERLENDİRME
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ohs/hazards", methods=["GET", "POST"])
@login_required
def ohs_hazards():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            faaliyet = (request.form.get("faaliyet") or "").strip()
            tehlike = (request.form.get("tehlike") or "").strip()
            if not faaliyet or not tehlike:
                flash("Faaliyet ve Tehlike alanları zorunludur.", "error")
                return redirect(url_for("ohs_hazards"))
                
            olasilik = _int(request.form.get("olasilik")) or 1
            siddet = _int(request.form.get("siddet")) or 1
            artik_risk = _int(request.form.get("artik_risk"))
            
            hazard = OHSHazard(
                faaliyet=faaliyet,
                tehlike=tehlike,
                risk=(request.form.get("risk") or "").strip() or None,
                calisan_grubu=(request.form.get("calisan_grubu") or "").strip() or None,
                rutin_mi=request.form.get("rutin_mi") == "1",
                olasilik=olasilik,
                siddet=siddet,
                kontrol_hiyerarsisi=request.form.get("kontrol_hiyerarsisi") or "Kişisel Koruyucu Donanım",
                mevcut_kontroller=(request.form.get("mevcut_kontroller") or "").strip() or None,
                artik_risk=artik_risk,
                durum=request.form.get("durum") or "Açık",
                sorumlu_id=_int(request.form.get("sorumlu_id")),
                ilgili_surec_id=_int(request.form.get("ilgili_surec_id"))
            )
            db.add(hazard)
            db.commit()
            log_action(db, "Oluşturma", detay=f"İSG Tehlikesi eklendi: {hazard.tehlike}")
            flash("Tehlike ve risk değerlendirme kaydı başarıyla eklendi.", "success")
            return redirect(url_for("ohs_hazards"))
            
        kayitlar = db.query(OHSHazard).order_by(OHSHazard.id.desc()).all()
        processes = db.query(Process).order_by(Process.ad).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "ohs_hazards.html",
            kayitlar=kayitlar,
            processes=processes,
            users=users,
            kontrol_hiyerarsisi=ISG_KONTROL_HIYERARSISI,
            risk_durumlari=ISG_RISK_DURUMLARI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  İSG OLAYLARI (KAZA, RAMAK KALA, MESLEK HASTALIĞI)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ohs/incidents", methods=["GET", "POST"])
@login_required
def ohs_incidents():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            tanim = (request.form.get("tanim") or "").strip()
            if not tanim:
                flash("Olay tanımı zorunludur.", "error")
                return redirect(url_for("ohs_incidents"))
                
            incident = OHSIncident(
                olay_no=(request.form.get("olay_no") or "").strip() or None,
                tur=request.form.get("tur") or "Ramak Kala",
                tarih=_date(request.form.get("tarih")) or date.today(),
                yaralanan=(request.form.get("yaralanan") or "").strip() or None,
                yer=(request.form.get("yer") or "").strip() or None,
                tanim=tanim,
                kok_neden=(request.form.get("kok_neden") or "").strip() or None,
                kayip_gun=_int(request.form.get("kayip_gun")) or 0,
                bildirim_yapildi=request.form.get("bildirim_yapildi") == "1",
                capa_id=_int(request.form.get("capa_id")),
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(incident)
            db.commit()
            log_action(db, "Oluşturma", detay=f"İSG Olayı eklendi: {incident.olay_no or incident.id}")
            flash("İSG kaza / ramak kala olayı başarıyla kaydedildi.", "success")
            return redirect(url_for("ohs_incidents"))
            
        kayitlar = db.query(OHSIncident).order_by(OHSIncident.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        capas = db.query(CorrectiveAction).order_by(CorrectiveAction.id.desc()).all()
        return render_template(
            "ohs_incidents.html",
            kayitlar=kayitlar,
            users=users,
            capas=capas,
            olay_turleri=ISG_OLAY_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ÇALIŞAN KATILIMI VE DANIŞMA (ÖNERİ, KURUL TOPLANTISI)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ohs/participation", methods=["GET", "POST"])
@login_required
def ohs_participation():
    db = get_db()
    try:
        if request.method == "POST":
            # Katılım formu tüm kullanıcılara açıktır (öneri sistemi)
            konu = (request.form.get("konu") or "").strip()
            if not konu:
                flash("Öneri / Katılım konusu zorunludur.", "error")
                return redirect(url_for("ohs_participation"))
                
            part = OHSParticipation(
                tur=request.form.get("tur") or "Öneri",
                tarih=_date(request.form.get("tarih")) or date.today(),
                konu=konu,
                katilimci=(request.form.get("katilimci") or session.get("ad_soyad") or "").strip() or None,
                karar=(request.form.get("karar") or "").strip() or None,
                kapatildi=request.form.get("kapatildi") == "1"
            )
            db.add(part)
            db.commit()
            log_action(db, "Oluşturma", detay=f"İSG Katılımı eklendi: {part.konu}")
            flash("Katılım / Öneri kaydınız başarıyla kaydedildi.", "success")
            return redirect(url_for("ohs_participation"))
            
        kayitlar = db.query(OHSParticipation).order_by(OHSParticipation.id.desc()).all()
        return render_template(
            "ohs_participation.html",
            kayitlar=kayitlar,
            katilim_turleri=ISG_KATILIM_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  KKD STOK VE ZİMMET
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ohs/ppe")
@login_required
def ohs_ppe():
    db = get_db()
    try:
        kayitlar = db.query(PPEItem).order_by(PPEItem.ad).all()
        return render_template(
            "ohs_ppe.html",
            kayitlar=kayitlar
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ACİL DURUM TATBİKATLARI
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ohs/drills", methods=["GET", "POST"])
@login_required
def ohs_drills():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            katilimci_ids = request.form.getlist("katilimci_ids")
            katilimci_ids_str = json.dumps([int(x) for x in katilimci_ids if str(x).isdigit()])
            
            drill = EmergencyDrill(
                drill_no=(request.form.get("drill_no") or "").strip() or None,
                planlanan_tarihi=_date(request.form.get("planlanan_tarihi")),
                gerceklesen_tarihi=_date(request.form.get("gerceklesen_tarihi")),
                senaryo=(request.form.get("senaryo") or "").strip() or None,
                katilimci_sayisi=len(katilimci_ids),
                katilimci_ids=katilimci_ids_str,
                etkinlik_sonucu=(request.form.get("etkinlik_sonucu") or "").strip() or None,
                aksiyon=(request.form.get("aksiyon") or "").strip() or None,
                capa_id=_int(request.form.get("capa_id"))
            )
            db.add(drill)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Tatbikat eklendi: {drill.drill_no}")
            flash("Acil durum tatbikatı başarıyla oluşturuldu.", "success")
            return redirect(url_for("ohs_drills"))
            
        kayitlar = db.query(EmergencyDrill).order_by(EmergencyDrill.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        user_map = {u.id: u.ad_soyad for u in users}
        capas = db.query(CorrectiveAction).order_by(CorrectiveAction.id.desc()).all()
        
        return render_template(
            "ohs_drills.html",
            kayitlar=kayitlar,
            users=users,
            user_map=user_map,
            capalar=capas
        )
    finally:
        db.close()

@app.route("/ohs/drills/<int:drill_id>")
@login_required
def ohs_drill_detail(drill_id):
    db = get_db()
    try:
        drill = db.query(EmergencyDrill).get(drill_id)
        if not drill:
            flash("Tatbikat bulunamadı.", "error")
            return redirect(url_for("ohs_drills"))
            
        # Katılımcıları çek
        user_ids = drill.katilimci_id_listesi()
        katilimcilar = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        
        return render_template(
            "ohs_drill_detail.html",
            drill=drill,
            katilimcilar=katilimcilar
        )
    finally:
        db.close()
