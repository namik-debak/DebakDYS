"""
DYS — ISO 27001 Bilgi Güvenliği (ISMS) Modülü
===============================================
Varlık envanteri, SoA uygulanabilirlik beyanı, risk değerlendirmesi, olaylar, erişim incelemeleri ve yedekleme kanıtları.
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
    User, Document, InformationAsset, SoAControl, ISMSRisk,
    SecurityIncident, AccessReview, BackupEvidence,
    CIA_SEVIYELERI, VERI_SINIFLARI, SOA_DURUMLARI, ISMS_TEDAVI_SECENEKLERI,
    ISMS_OLAY_TURLERI, YEDEK_TIPLERI
)

def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol", "Bilgi Güvenliği Yöneticisi")

def _float(v):
    if not v:
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None

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

def _datetime(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  ISMS GENEL BAKIŞ / DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms")
@login_required
def isms_overview():
    db = get_db()
    try:
        ozet = {
            'varlik': db.query(InformationAsset).count(),
            'soa': db.query(SoAControl).count(),
            'risk': db.query(ISMSRisk).count(),
            'olay': db.query(SecurityIncident).count(),
            'erisim': db.query(AccessReview).count(),
            'yedek': db.query(BackupEvidence).count()
        }
        return render_template(
            "isms_overview.html",
            ozet=ozet
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  BİLGİ VARLIKLARI ENVANTERİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/assets", methods=["GET", "POST"])
@login_required
def isms_assets():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            ad = (request.form.get("ad") or "").strip()
            if not ad:
                flash("Varlık adı zorunludur.", "error")
                return redirect(url_for("isms_assets"))
                
            asset = InformationAsset(
                varlik_no=(request.form.get("varlik_no") or "").strip() or None,
                ad=ad,
                tur=(request.form.get("tur") or "").strip() or None,
                sahip_id=_int(request.form.get("sahip_id")),
                gizlilik=request.form.get("gizlilik") or "Orta",
                butunluk=request.form.get("butunluk") or "Orta",
                erisilebilirlik=request.form.get("erisilebilirlik") or "Orta",
                konum=(request.form.get("konum") or "").strip() or None,
                veri_sinifi=request.form.get("veri_sinifi") or "İç Kullanım",
                tedarikci=(request.form.get("tedarikci") or "").strip() or None,
                saklama_kurali=(request.form.get("saklama_kurali") or "").strip() or None
            )
            db.add(asset)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Bilgi Varlığı eklendi: {asset.ad}")
            flash("Bilgi varlığı başarıyla eklendi.", "success")
            return redirect(url_for("isms_assets"))
            
        kayitlar = db.query(InformationAsset).order_by(InformationAsset.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_assets.html",
            kayitlar=kayitlar,
            users=users,
            cia_seviyeleri=CIA_SEVIYELERI,
            veri_siniflari=VERI_SINIFLARI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  SoA UYGULANABİLİRLİK BEYANI
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/soa", methods=["GET"])
@login_required
def isms_soa():
    db = get_db()
    try:
        kayitlar = db.query(SoAControl).order_by(SoAControl.kontrol_no).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_soa.html",
            kayitlar=kayitlar,
            users=users,
            soa_durumlari=SOA_DURUMLARI,
            can_edit=_can_edit()
        )
    finally:
        db.close()

@app.route("/isms/soa/update/<int:control_id>", methods=["POST"])
@login_required
def isms_soa_update(control_id):
    if not _can_edit():
        abort(403)
    db = get_db()
    try:
        ctrl = db.query(SoAControl).get(control_id)
        if not ctrl:
            flash("Kontrol bulunamadı.", "error")
            return redirect(url_for("isms_soa"))
            
        ctrl.uygulanabilir_mi = request.form.get("uygulanabilir_mi") == "1"
        ctrl.gerekce = (request.form.get("gerekce") or "").strip() or None
        ctrl.uygulama_durumu = request.form.get("uygulama_durumu") or "Uygulanmadı"
        ctrl.kontrol_sahibi_id = _int(request.form.get("kontrol_sahibi_id"))
        ctrl.kanit = (request.form.get("kanit") or "").strip() or None
        
        db.commit()
        log_action(db, "Güncelleme", detay=f"SoA Kontrol güncellendi: {ctrl.kontrol_no}")
        flash("SoA kontrol durumu güncellendi.", "success")
        return redirect(url_for("isms_soa"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ISMS RİSK DEĞERLENDİRMESİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/risks", methods=["GET", "POST"])
@login_required
def isms_risks():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            tehdit = (request.form.get("tehdit") or "").strip()
            if not tehdit:
                flash("Tehdit açıklaması zorunludur.", "error")
                return redirect(url_for("isms_risks"))
                
            risk = ISMSRisk(
                risk_no=(request.form.get("risk_no") or "").strip() or None,
                asset_id=_int(request.form.get("asset_id")),
                tehdit=tehdit,
                zafiyet=(request.form.get("zafiyet") or "").strip() or None,
                olasilik=_int(request.form.get("olasilik")) or 1,
                etki=_int(request.form.get("etki")) or 1,
                tedavi=request.form.get("tedavi") or "Azaltma",
                tedavi_plani=(request.form.get("tedavi_plani") or "").strip() or None,
                soa_kontrol=(request.form.get("soa_kontrol") or "").strip() or None,
                artik_risk=_int(request.form.get("artik_risk")),
                kabul_edildi=request.form.get("kabul_edildi") == "1",
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(risk)
            db.commit()
            log_action(db, "Oluşturma", detay=f"ISMS Riski eklendi: {risk.risk_no or risk.id}")
            flash("Bilgi güvenliği riski başarıyla eklendi.", "success")
            return redirect(url_for("isms_risks"))
            
        kayitlar = db.query(ISMSRisk).order_by(ISMSRisk.id.desc()).all()
        assets = db.query(InformationAsset).order_by(InformationAsset.ad).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_risks.html",
            kayitlar=kayitlar,
            assets=assets,
            users=users,
            tedavi_secenekleri=ISMS_TEDAVI_SECENEKLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  GÜVENLİK OLAYLARI
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/incidents", methods=["GET", "POST"])
@login_required
def isms_incidents():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            tanim = (request.form.get("tanim") or "").strip()
            if not tanim:
                flash("Olay tanımı zorunludur.", "error")
                return redirect(url_for("isms_incidents"))
                
            incident = SecurityIncident(
                olay_no=(request.form.get("olay_no") or "").strip() or None,
                tur=request.form.get("tur") or "Diğer",
                tarih=_date(request.form.get("tarih")) or date.today(),
                tanim=tanim,
                etki=(request.form.get("etki") or "").strip() or None,
                mudahale=(request.form.get("mudahale") or "").strip() or None,
                sorumlu_id=_int(request.form.get("sorumlu_id")),
                kapatildi=request.form.get("kapatildi") == "1"
            )
            db.add(incident)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Güvenlik Olayı eklendi: {incident.olay_no or incident.id}")
            flash("Güvenlik olayı başarıyla kaydedildi.", "success")
            return redirect(url_for("isms_incidents"))
            
        kayitlar = db.query(SecurityIncident).order_by(SecurityIncident.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_incidents.html",
            kayitlar=kayitlar,
            users=users,
            olay_turleri=ISMS_OLAY_TURLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  ERİŞİM İNCELEMESİ
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/access-reviews", methods=["GET", "POST"])
@login_required
def isms_access_reviews():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            kapsam = (request.form.get("kapsam") or "").strip()
            if not kapsam:
                flash("Kapsam zorunludur.", "error")
                return redirect(url_for("isms_access_reviews"))
                
            review = AccessReview(
                tarih=_date(request.form.get("tarih")) or date.today(),
                kapsam=kapsam,
                inceleyen_id=_int(request.form.get("inceleyen_id")),
                bulgu=(request.form.get("bulgu") or "").strip() or None,
                aksiyon=(request.form.get("aksiyon") or "").strip() or None,
                tamamlandi=request.form.get("tamamlandi") == "1"
            )
            db.add(review)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Erişim İncelemesi eklendi: {review.id}")
            flash("Erişim inceleme kaydı başarıyla eklendi.", "success")
            return redirect(url_for("isms_access_reviews"))
            
        kayitlar = db.query(AccessReview).order_by(AccessReview.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_access_reviews.html",
            kayitlar=kayitlar,
            users=users,
            can_edit=_can_edit()
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  YEDEKLEME KANITLARI
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/isms/backups", methods=["GET", "POST"])
@login_required
def isms_backups():
    db = get_db()
    try:
        if request.method == "POST":
            if not _can_edit():
                abort(403)
                
            backup = BackupEvidence(
                yedek_tarihi=_datetime(request.form.get("yedek_tarihi")) or datetime.now(),
                yedek_tipi=request.form.get("yedek_tipi") or "Tam",
                konum=(request.form.get("konum") or "").strip() or None,
                boyut_mb=_float(request.form.get("boyut_mb")) or 0.0,
                geri_yukleme_testi_mi=request.form.get("geri_yukleme_testi_mi") == "1",
                test_tarihi=_date(request.form.get("test_tarihi")),
                test_sonucu=(request.form.get("test_sonucu") or "").strip() or None,
                sorumlu_id=_int(request.form.get("sorumlu_id"))
            )
            db.add(backup)
            db.commit()
            log_action(db, "Oluşturma", detay=f"Yedekleme Kanıtı eklendi: {backup.konum or backup.id}")
            flash("Yedekleme kanıtı başarıyla eklendi.", "success")
            return redirect(url_for("isms_backups"))
            
        kayitlar = db.query(BackupEvidence).order_by(BackupEvidence.id.desc()).all()
        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        return render_template(
            "isms_backups.html",
            kayitlar=kayitlar,
            users=users,
            yedek_tipleri=YEDEK_TIPLERI,
            can_edit=_can_edit()
        )
    finally:
        db.close()
