"""
DYS — Garanti, Tedarikçi Geliştirme ve Layout Muayene Route'ları (Faz C)
========================================================================
IATF 16949 § 10.2.5 (Garanti), § 8.4.2.3 (Tedarikçi Geliştirme) ve § 8.6.2 (Layout) uyumlu.
"""

from datetime import date, datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    User, CorrectiveAction, WarrantyClaim, SupplierDevelopmentPlan, LayoutInspection
)

def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _float(v):
    try:
        return float(v)
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
#  Garanti Yönetimi (Customer Complaints & Warranty Analysis § 10.2.5)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/warranty")
@login_required
def warranty_list():
    db = get_db()
    try:
        claims = db.query(WarrantyClaim).order_by(WarrantyClaim.olusturma_tarihi.desc()).all()
        users = db.query(User).filter_by(aktif=True).all()
        capas = db.query(CorrectiveAction).order_by(CorrectiveAction.dof_no.desc()).all()
        return render_template(
            "warranty.html",
            claims=claims,
            users=users,
            capas=capas
        )
    finally:
        db.close()


@app.route("/iatf/warranty/new", methods=["POST"])
@login_required
def warranty_new():
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        claim = WarrantyClaim(
            musteri=(request.form.get("musteri") or "").strip() or "Bilinmeyen Müşteri",
            parca_no=(request.form.get("parca_no") or "").strip() or "Bilinmeyen Parça",
            miktar=_int(request.form.get("miktar")) or 1,
            talep_tarihi=_date(request.form.get("talep_tarihi")) or date.today(),
            tutar=_float(request.form.get("tutar")),
            durum="Açık",
            aciklama=(request.form.get("aciklama") or "").strip() or None,
        )
        db.add(claim)
        db.commit()
        log_action(db, "Oluşturma", detay=f"Garanti talebi eklendi: {claim.musteri} - {claim.parca_no}")
        flash("Garanti talebi başarıyla oluşturuldu.", "success")
        return redirect(url_for("warranty_list"))
    finally:
        db.close()


@app.route("/iatf/warranty/<int:claim_id>/analyze", methods=["POST"])
@login_required
def warranty_analyze(claim_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        claim = db.query(WarrantyClaim).get(claim_id)
        if not claim:
            abort(404)
        
        claim.analiz_sonucu = (request.form.get("analiz_sonucu") or "").strip() or None
        claim.analiz_tarihi = date.today()
        claim.analiz_eden_id = session.get("kullanici_id")
        claim.capa_id = _int(request.form.get("capa_id"))
        claim.durum = "Sonuçlandırıldı" if request.form.get("sonuclandir") == "1" else "Analiz Ediliyor"
        
        db.commit()
        log_action(db, "Düzenleme", detay=f"Garanti analiz sonucu girildi: Claim ID {claim.id} → {claim.durum}")
        flash("Analiz bilgileri kaydedildi.", "success")
        return redirect(url_for("warranty_list"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Tedarikçi Geliştirme Planı (Supplier QMS Development § 8.4.2.3)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/supplier-dev")
@login_required
def supplier_dev_list():
    db = get_db()
    try:
        plans = db.query(SupplierDevelopmentPlan).order_by(SupplierDevelopmentPlan.olusturma_tarihi.desc()).all()
        return render_template(
            "supplier_dev.html",
            plans=plans
        )
    finally:
        db.close()


@app.route("/iatf/supplier-dev/new", methods=["POST"])
@login_required
def supplier_dev_new():
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        plan = SupplierDevelopmentPlan(
            tedarikci_adi=(request.form.get("tedarikci_adi") or "").strip() or "Bilinmeyen Tedarikçi",
            baslangic_tarihi=_date(request.form.get("baslangic_tarihi")),
            hedef_tarih=_date(request.form.get("hedef_tarih")),
            hedef_sertifikasyon=(request.form.get("hedef_sertifikasyon") or "").strip() or None,
            son_denetim_skoru=_float(request.form.get("son_denetim_skoru")),
            notlar=(request.form.get("notlar") or "").strip() or None,
            durum="Planlandı"
        )
        db.add(plan)
        db.commit()
        log_action(db, "Oluşturma", detay=f"Tedarikçi Geliştirme Planı: {plan.tedarikci_adi}")
        flash("Tedarikçi geliştirme planı eklendi.", "success")
        return redirect(url_for("supplier_dev_list"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Layout Muayenesi & Fonksiyonel Test (Layout Inspection § 8.6.2)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/layout-inspection")
@login_required
def layout_inspection_list():
    db = get_db()
    try:
        inspections = db.query(LayoutInspection).order_by(LayoutInspection.olusturma_tarihi.desc()).all()
        users = db.query(User).filter_by(aktif=True).all()
        return render_template(
            "layout_inspection.html",
            inspections=inspections,
            users=users
        )
    finally:
        db.close()


@app.route("/iatf/layout-inspection/new", methods=["POST"])
@login_required
def layout_inspection_new():
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        periyot = _int(request.form.get("periyot_ay")) or 12
        son_tarih = _date(request.form.get("son_muayene_tarihi")) or date.today()
        sonraki_tarih = son_tarih + timedelta(days=periyot * 30)

        inspection = LayoutInspection(
            parca_no=(request.form.get("parca_no") or "").strip() or "Bilinmeyen Parça No",
            parca_adi=(request.form.get("parca_adi") or "").strip() or "Bilinmeyen Parça Adı",
            periyot_ay=periyot,
            son_muayene_tarihi=son_tarih,
            sonraki_muayene_tarihi=sonraki_tarih,
            sonuc=request.form.get("sonuc") or "Değerlendirilmedi",
            rapor_no=(request.form.get("rapor_no") or "").strip() or None,
            sorumlu_id=_int(request.form.get("sorumlu_id")),
            aciklama=(request.form.get("aciklama") or "").strip() or None,
        )
        db.add(inspection)
        db.commit()
        log_action(db, "Oluşturma", detay=f"Layout Muayenesi eklendi: {inspection.parca_no}")
        flash("Yerleşim muayene kaydı başarıyla oluşturuldu.", "success")
        return redirect(url_for("layout_inspection_list"))
    finally:
        db.close()
