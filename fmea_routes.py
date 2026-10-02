"""
DYS — FMEA Route'ları (VDA/AIAG FMEA Handbook 2019 Uyumlu)
============================================================
7-adım FMEA iş akışı, Action Priority (AP) hesaplama,
önleme/tespit kontrolü ayrımı ve aksiyon sonrası yeniden değerlendirme.
"""

from datetime import date, datetime

from flask import (
    render_template, request, redirect, url_for, flash, abort, session,
    jsonify,
)

from app_runtime import host as _host

_h = _host()
app = _h.app
login_required = _h.login_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    User, Process, Document, FMEA, FMEAItem, ControlPlanItem,
    FMEA_TIPLERI, FMEA_ADIMLARI, FMEA_AKSIYON_DURUMLARI,
    OZEL_KARAKTERISTIK_TIPLERI, AP_SEVIYELERI,
)
from fmea_ap_matrix import hesapla_ap, ap_renk, ap_ozet


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _clamp(v, lo=1, hi=10):
    """Değeri aralığa sıkıştırır."""
    n = _int(v)
    if n is None:
        return lo
    return max(lo, min(hi, n))


def _next_fmea_no(db):
    """Yeni FMEA numarası üretir: FMEA-2026-001"""
    yil = date.today().year
    prefix = f"FMEA-{yil}-"
    son = (
        db.query(FMEA)
        .filter(FMEA.fmea_no.like(f"{prefix}%"))
        .order_by(FMEA.fmea_no.desc())
        .first()
    )
    if son:
        try:
            sira = int(son.fmea_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            sira = 1
    else:
        sira = 1
    return f"{prefix}{sira:03d}"


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Listesi
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea")
@login_required
def fmea_list():
    db = get_db()
    try:
        tip_filtre = request.args.get("tip")
        ap_filtre = request.args.get("ap")
        q = db.query(FMEA).order_by(FMEA.olusturma_tarihi.desc())
        if tip_filtre and tip_filtre in FMEA_TIPLERI:
            q = q.filter(FMEA.tip == tip_filtre)
        kayitlar = q.all()

        # AP filtresi — item bazlı olduğu için Python'da filtrele
        if ap_filtre and ap_filtre in AP_SEVIYELERI:
            kayitlar = [
                f for f in kayitlar
                if any(i.action_priority == ap_filtre for i in f.items)
            ]

        return render_template(
            "iatf_fmea.html",
            kayitlar=kayitlar,
            tipler=FMEA_TIPLERI,
            adimlar=FMEA_ADIMLARI,
            ap_renkler={"H": ap_renk("H"), "M": ap_renk("M"), "L": ap_renk("L")},
            tip_filtre=tip_filtre,
            ap_filtre=ap_filtre,
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Oluşturma
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/new", methods=["GET", "POST"])
@login_required
def fmea_new():
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        if request.method == "POST":
            fmea = FMEA(
                fmea_no=_next_fmea_no(db),
                tip=request.form.get("tip") or "PFMEA",
                kapsam=(request.form.get("kapsam") or "").strip() or None,
                parca_proses=(request.form.get("parca_proses") or "").strip() or None,
                musteri=(request.form.get("musteri") or "").strip() or None,
                ekip=(request.form.get("ekip") or "").strip() or None,
                surec_id=_int(request.form.get("surec_id")),
                tarih=date.today(),
                mevcut_adim="1-Planlama",
                baslatma_tarihi=date.today(),
                aciklama=(request.form.get("aciklama") or "").strip() or None,
            )
            db.add(fmea)
            db.commit()
            log_action(db, "Oluşturma", detay=f"FMEA oluşturuldu: {fmea.fmea_no}")
            flash(f"FMEA {fmea.fmea_no} oluşturuldu.", "success")
            return redirect(url_for("fmea_detail", fmea_id=fmea.id))

        procs = db.query(Process).order_by(Process.kod).all()
        return render_template(
            "fmea_form.html",
            fmea=None,
            tipler=FMEA_TIPLERI,
            adimlar=FMEA_ADIMLARI,
            procs=procs,
            mode="new",
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Detay (7-Adım Görünümü)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>")
@login_required
def fmea_detail(fmea_id):
    db = get_db()
    try:
        fmea = db.query(FMEA).get(fmea_id)
        if not fmea:
            abort(404)

        users = db.query(User).filter_by(aktif=True).order_by(User.ad_soyad).all()
        ozet = ap_ozet(fmea.items)

        return render_template(
            "fmea_detail.html",
            fmea=fmea,
            items=fmea.items,
            users=users,
            ozet=ozet,
            adimlar=FMEA_ADIMLARI,
            aksiyon_durumlari=FMEA_AKSIYON_DURUMLARI,
            ozel_tipleri=OZEL_KARAKTERISTIK_TIPLERI,
            ap_renkler={"H": ap_renk("H"), "M": ap_renk("M"), "L": ap_renk("L")},
            hesapla_ap=hesapla_ap,
            ap_renk=ap_renk,
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Düzenleme
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/edit", methods=["GET", "POST"])
@login_required
def fmea_edit(fmea_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        fmea = db.query(FMEA).get(fmea_id)
        if not fmea:
            abort(404)

        if request.method == "POST":
            fmea.tip = request.form.get("tip") or fmea.tip
            fmea.kapsam = (request.form.get("kapsam") or "").strip() or None
            fmea.parca_proses = (request.form.get("parca_proses") or "").strip() or None
            fmea.musteri = (request.form.get("musteri") or "").strip() or None
            fmea.ekip = (request.form.get("ekip") or "").strip() or None
            fmea.surec_id = _int(request.form.get("surec_id"))
            fmea.mevcut_adim = request.form.get("mevcut_adim") or fmea.mevcut_adim
            fmea.aciklama = (request.form.get("aciklama") or "").strip() or None
            fmea.revizyon = (request.form.get("revizyon") or fmea.revizyon).strip()
            db.commit()
            log_action(db, "Düzenleme", detay=f"FMEA güncellendi: {fmea.fmea_no}")
            flash("FMEA güncellendi.", "success")
            return redirect(url_for("fmea_detail", fmea_id=fmea.id))

        procs = db.query(Process).order_by(Process.kod).all()
        return render_template(
            "fmea_form.html",
            fmea=fmea,
            tipler=FMEA_TIPLERI,
            adimlar=FMEA_ADIMLARI,
            procs=procs,
            mode="edit",
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Satır Ekleme
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/item/new", methods=["POST"])
@login_required
def fmea_item_new(fmea_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        fmea = db.query(FMEA).get(fmea_id)
        if not fmea:
            abort(404)

        item = FMEAItem(
            fmea_id=fmea.id,
            fonksiyon=(request.form.get("fonksiyon") or "").strip() or None,
            hata_turu=(request.form.get("hata_turu") or "").strip() or None,
            etki=(request.form.get("etki") or "").strip() or None,
            siddet=_clamp(request.form.get("siddet")),
            neden=(request.form.get("neden") or "").strip() or None,
            olusma=_clamp(request.form.get("olusma")),
            onleme_kontrolu=(request.form.get("onleme_kontrolu") or "").strip() or None,
            tespit_kontrolu=(request.form.get("tespit_kontrolu") or "").strip() or None,
            tespit=_clamp(request.form.get("tespit")),
            ozel_karakteristik=bool(request.form.get("ozel_karakteristik")),
            ozel_karakteristik_tip=request.form.get("ozel_karakteristik_tip") or None,
            filtre_kodu=(request.form.get("filtre_kodu") or "").strip() or None,
            onerilen_aksiyon=(request.form.get("onerilen_aksiyon") or "").strip() or None,
            sorumlu_id=_int(request.form.get("sorumlu_id")),
        )
        db.add(item)
        db.commit()
        log_action(db, "Oluşturma", detay=f"FMEA satırı eklendi: {fmea.fmea_no}")
        flash("FMEA satırı eklendi.", "success")
        return redirect(url_for("fmea_detail", fmea_id=fmea.id))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Satır Güncelleme
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/item/<int:item_id>/edit", methods=["POST"])
@login_required
def fmea_item_edit(fmea_id, item_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        item = db.query(FMEAItem).filter_by(id=item_id, fmea_id=fmea_id).first()
        if not item:
            abort(404)

        item.fonksiyon = (request.form.get("fonksiyon") or "").strip() or None
        item.hata_turu = (request.form.get("hata_turu") or "").strip() or None
        item.etki = (request.form.get("etki") or "").strip() or None
        item.siddet = _clamp(request.form.get("siddet"))
        item.neden = (request.form.get("neden") or "").strip() or None
        item.olusma = _clamp(request.form.get("olusma"))
        item.onleme_kontrolu = (request.form.get("onleme_kontrolu") or "").strip() or None
        item.tespit_kontrolu = (request.form.get("tespit_kontrolu") or "").strip() or None
        item.tespit = _clamp(request.form.get("tespit"))
        item.ozel_karakteristik = bool(request.form.get("ozel_karakteristik"))
        item.ozel_karakteristik_tip = request.form.get("ozel_karakteristik_tip") or None
        item.filtre_kodu = (request.form.get("filtre_kodu") or "").strip() or None
        item.onerilen_aksiyon = (request.form.get("onerilen_aksiyon") or "").strip() or None
        item.sorumlu_id = _int(request.form.get("sorumlu_id"))

        db.commit()
        log_action(db, "Düzenleme", detay=f"FMEA satırı güncellendi (id={item_id})")
        flash("FMEA satırı güncellendi.", "success")
        return redirect(url_for("fmea_detail", fmea_id=fmea_id))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Aksiyon Kaydetme + Yeniden Değerlendirme (Adım 6)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/item/<int:item_id>/action", methods=["POST"])
@login_required
def fmea_item_action(fmea_id, item_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        item = db.query(FMEAItem).filter_by(id=item_id, fmea_id=fmea_id).first()
        if not item:
            abort(404)

        item.aksiyon_durumu = request.form.get("aksiyon_durumu") or None
        item.aksiyon_alinan = (request.form.get("aksiyon_alinan") or "").strip() or None

        if item.aksiyon_durumu == "Tamamlandı":
            item.aksiyon_tamamlanma_tarihi = date.today()
            # Yeniden değerlendirme
            yeni_s = _int(request.form.get("yeni_siddet"))
            yeni_o = _int(request.form.get("yeni_olusma"))
            yeni_d = _int(request.form.get("yeni_tespit"))
            if yeni_s and yeni_o and yeni_d:
                item.yeni_siddet = _clamp(yeni_s)
                item.yeni_olusma = _clamp(yeni_o)
                item.yeni_tespit = _clamp(yeni_d)

        db.commit()
        log_action(db, "Düzenleme", detay=f"FMEA aksiyon güncellendi (item_id={item_id})")
        flash("Aksiyon kaydedildi.", "success")
        return redirect(url_for("fmea_detail", fmea_id=fmea_id))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Satır Silme
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/item/<int:item_id>/delete", methods=["POST"])
@login_required
def fmea_item_delete(fmea_id, item_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        item = db.query(FMEAItem).filter_by(id=item_id, fmea_id=fmea_id).first()
        if not item:
            abort(404)
        db.delete(item)
        db.commit()
        log_action(db, "Silme", detay=f"FMEA satırı silindi (item_id={item_id})")
        flash("FMEA satırı silindi.", "success")
        return redirect(url_for("fmea_detail", fmea_id=fmea_id))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  FMEA Adım İlerleme (JSON)
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/iatf/fmea/<int:fmea_id>/step", methods=["POST"])
@login_required
def fmea_step(fmea_id):
    if session.get("rol") not in ("Admin", "Doküman Kontrol"):
        abort(403)
    db = get_db()
    try:
        fmea = db.query(FMEA).get(fmea_id)
        if not fmea:
            abort(404)
        yeni_adim = request.form.get("adim")
        if yeni_adim and yeni_adim in FMEA_ADIMLARI:
            fmea.mevcut_adim = yeni_adim
            if yeni_adim == "7-Dokümantasyon":
                fmea.tamamlanma_tarihi = date.today()
            db.commit()
            log_action(db, "Düzenleme", detay=f"FMEA adım: {fmea.fmea_no} → {yeni_adim}")
            flash(f"FMEA adımı güncellendi: {yeni_adim}", "success")
        return redirect(url_for("fmea_detail", fmea_id=fmea.id))
    finally:
        db.close()
