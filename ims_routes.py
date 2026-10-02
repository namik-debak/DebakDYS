"""
DYS — Entegre Yönetim Sistemi (IMS) Modülü
===========================================
Gereklilikler (Requirements), Uyum Matrisi, Bağlam ve Taraflar, Mevzuat Uygunluk ve Yönetim Gözden Geçirme (YGG).
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
    User, Document, Requirement, RequirementStatus, StandardEdition,
    OrganizationContext, InterestedParty, ManagementReview, LegalRequirement,
    ComplianceEvaluation, Process, ProcessKPI,
    IMS_UYGULANABILIRLIK, IMS_UYGULAMA_DURUMLARI, IMS_ETKINLIK_DURUMLARI,
    BAGLAM_TURLERI
)

def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol")

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
#  IMS GENEL BAKIŞ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ims")
@login_required
def ims_overview():
    db = get_db()
    try:
        ozet = {
            'gereksinim': db.query(Requirement).count(),
            'baglam': db.query(OrganizationContext).count(),
            'taraf': db.query(InterestedParty).count(),
            'ygg': db.query(ManagementReview).count(),
            'yasal': db.query(LegalRequirement).count(),
            'kpi': db.query(ProcessKPI).count()
        }
        return render_template(
            "ims_overview.html",
            ozet=ozet
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  UYUM MATRİSİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ims/requirements", methods=["GET"])
@login_required
def ims_requirements():
    db = get_db()
    try:
        editions = db.query(StandardEdition).all()
        kayitlar = db.query(Requirement).order_by(Requirement.madde_no).limit(500).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "ims_requirements.html",
            kayitlar=kayitlar,
            editions=editions,
            users=users,
            uygulanabilirlik_secenekleri=IMS_UYGULANABILIRLIK,
            uygulama_durumlari=IMS_UYGULAMA_DURUMLARI,
            etkinlik_durumlari=IMS_ETKINLIK_DURUMLARI,
            can_edit=_can_edit()
        )
    finally:
        db.close()

@app.route("/ims/requirements/update/<int:req_id>", methods=["POST"])
@login_required
def ims_requirements_update(req_id):
    if not _can_edit():
        abort(403)
    db = get_db()
    try:
        req = db.query(Requirement).get(req_id)
        if not req:
            flash("Standart maddesi bulunamadı.", "error")
            return redirect(url_for("ims_requirements"))
            
        status = req.status
        if not status:
            status = RequirementStatus(requirement_id=req_id)
            db.add(status)
            
        status.uygulanabilirlik = request.form.get("uygulanabilir_mi") or "Uygulanabilir"
        status.gerekce = (request.form.get("gerekce") or "").strip() or None
        status.uygulama_durumu = request.form.get("uygulama_durumu") or "Uygulanmadı"
        status.etkinlik = request.form.get("etkinlik") or "Değerlendirilmedi"
        status.sorumlu_id = _int(request.form.get("sorumlu_id"))
        status.notlar = (request.form.get("notlar") or "").strip() or None
        status.son_dogrulama_tarihi = _date(request.form.get("son_dogrulama_tarihi"))
        
        db.commit()
        log_action(db, "Güncelleme", detay=f"Requirement status güncellendi: {req.madde_no}")
        flash(f"{req.madde_no} maddesinin uyum durumu güncellendi.", "success")
        return redirect(url_for("ims_requirements"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  BAĞLAM VE TARAFLAR
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ims/context", methods=["GET", "POST"])
@login_required
def ims_context():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            action = request.form.get("action")
            if action == "context":
                tanim = (request.form.get("tanim") or "").strip()
                if not tanim:
                    flash("Tanım açıklaması zorunludur.", "error")
                    return redirect(url_for("ims_context"))
                    
                ctx = OrganizationContext(
                    konu=(request.form.get("konu") or "").strip() or "İç/Dış Konu",
                    tur=request.form.get("tur") or "İç",
                    etki_yonu=request.form.get("etki_yonu") or "Nötr",
                    tanim=tanim,
                    izleme_frekansi=(request.form.get("izleme_frekansi") or "").strip() or None,
                    ilgili_surec_id=_int(request.form.get("ilgili_surec_id")),
                    sorumlu_id=_int(request.form.get("sorumlu_id"))
                )
                db.add(ctx)
                db.commit()
                log_action(db, "Oluşturma", detay=f"Bağlam konusu eklendi: {ctx.konu}")
                flash("Bağlam konusu başarıyla eklendi.", "success")
                
            elif action == "party":
                ad = (request.form.get("ad") or "").strip()
                if not ad:
                    flash("Taraf adı zorunludur.", "error")
                    return redirect(url_for("ims_context"))
                    
                party = InterestedParty(
                    ad=ad,
                    beklenti=(request.form.get("beklenti") or "").strip() or None,
                    etki_derecesi=request.form.get("etki_derecesi") or "Orta",
                    aksiyon=(request.form.get("aksiyon") or "").strip() or None,
                    sorumlu_id=_int(request.form.get("sorumlu_id"))
                )
                db.add(party)
                db.commit()
                log_action(db, "Oluşturma", detay=f"İlgili taraf eklendi: {party.ad}")
                flash("İlgili taraf başarıyla eklendi.", "success")
                
            return redirect(url_for("isms_context")) # Veya ims_context
            
        contexts = db.query(OrganizationContext).order_by(OrganizationContext.id.desc()).all()
        parties = db.query(InterestedParty).order_by(InterestedParty.id.desc()).all()
        processes = db.query(Process).order_by(Process.ad).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        
        return render_template(
            "ims_context.html",
            contexts=contexts,
            parties=parties,
            processes=processes,
            users=users,
            baglam_turleri=BAGLAM_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  MEVZUAT UYGUNLUK MATRİSİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ims/legal", methods=["GET", "POST"])
@login_required
def ims_legal():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            baslik = (request.form.get("baslik") or "").strip()
            if not baslik:
                flash("Mevzuat başlığı zorunludur.", "error")
                return redirect(url_for("ims_legal"))
                
            req = LegalRequirement(
                baslik=baslik,
                tur=request.form.get("tur") or "Genel",
                referans=(request.form.get("referans") or "").strip() or None,
                yukumluluk=(request.form.get("yukumluluk") or "").strip() or None,
                uygunluk_durumu=request.form.get("uygunluk_durumu") or "Değerlendirilmedi",
                son_degerlendirme_tarihi=_date(request.form.get("son_degerlendirme_tarihi")),
                sonraki_degerlendirme_tarihi=_date(request.form.get("sonraki_degerlendirme_tarihi")),
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(req)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Mevzuat eklendi: {req.baslik}")
            flash("Mevzuat kaydı başarıyla eklendi.", "success")
            return redirect(url_for("ims_legal"))
            
        kayitlar = db.query(LegalRequirement).order_by(LegalRequirement.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "ims_legal.html",
            kayitlar=kayitlar,
            users=users,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  YÖNETİM GÖZDEN GEÇİRME (YGG)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/ims/reviews", methods=["GET", "POST"])
@login_required
def ims_reviews():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            baslik = (request.form.get("baslik") or "").strip()
            if not baslik:
                flash("YGG toplantı başlığı zorunludur.", "error")
                return redirect(url_for("ims_reviews"))
                
            review = ManagementReview(
                baslik=baslik,
                toplanti_tarihi=_date(request.form.get("toplanti_tarihi")) or date.today(),
                katilimcilar=(request.form.get("katilimcilar") or "").strip() or None,
                girdiler=(request.form.get("girdiler") or "").strip() or None,
                kararlar=(request.form.get("kararlar") or "").strip() or None,
                aksiyonlar=(request.form.get("aksiyonlar") or "").strip() or None,
                durum=request.form.get("durum") or "Planlandı",
                olusturan_id=session.get("user_id")
            )
            db.add(review)
            db.commit()
            log_action(db, "Oluşturma", detay=f"YGG Toplantısı eklendi: {review.baslik}")
            flash("Yönetim gözden geçirme kaydı başarıyla eklendi.", "success")
            return redirect(url_for("ims_reviews"))
            
        kayitlar = db.query(ManagementReview).order_by(ManagementReview.id.desc()).all()
        docs = db.query(Document).order_by(Document.dokuman_no).all()
        return render_template(
            "ims_reviews.html",
            kayitlar=kayitlar,
            documents=docs,
            can_edit=_can_edit()
        )
    finally:
        db.close()
