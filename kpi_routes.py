"""
DYS — Süreç Performans İzleme (Y03 F06)
======================================
Süreç bazlı KPI paneli, dönemsel ölçüm girişi, uyumsuzlukta isteğe bağlı DÖF.
"""

from datetime import date, datetime, timedelta
import os

from flask import render_template, request, redirect, url_for, flash, abort, session

from app_runtime import host as _host
_h = _host()
app = _h.app
login_required = _h.login_required
admin_required = _h.admin_required
get_db = _h.get_db
log_action = _h.log_action

from models import (
    Process, ProcessKPI, ProcessKPIMeasurement, CorrectiveAction,
    KPI_OLCUM_DURUMLARI,
)
from helpers import next_sequence_no
from kpi_engine import evaluate_kpi, _to_float, suggest_donem, donem_secenekleri
from kpi_import import import_kpis_to_db, DEFAULT_KPI_XLSX
import notifications


def _can_edit():
    return session.get("rol") in ("Admin", "Doküman Kontrol")


def _latest_by_kpi(db, kpi_ids=None):
    """Her KPI için en güncel ölçüm (güncelleme tarihine göre)."""
    q = db.query(ProcessKPIMeasurement).order_by(
        ProcessKPIMeasurement.guncelleme_tarihi.desc()
    )
    if kpi_ids is not None:
        if not kpi_ids:
            return {}
        q = q.filter(ProcessKPIMeasurement.kpi_id.in_(kpi_ids))
    son = {}
    for m in q.limit(5000).all():
        if m.kpi_id not in son:
            son[m.kpi_id] = m
    return son


def _summarize(kpis, son):
    uyumlu = uyumsuz = izleme = girilmedi = 0
    for k in kpis:
        m = son.get(k.id)
        if not m or m.durum == "Girilmedi":
            girilmedi += 1
        elif m.durum == "Uyumlu":
            uyumlu += 1
        elif m.durum == "Uyumsuz":
            uyumsuz += 1
        else:
            izleme += 1
    toplam = len(kpis)
    degerlendirilen = uyumlu + uyumsuz
    return {
        "toplam": toplam,
        "uyumlu": uyumlu,
        "uyumsuz": uyumsuz,
        "izleme": izleme,
        "girilmedi": girilmedi,
        "oran": round(100 * uyumlu / degerlendirilen) if degerlendirilen else None,
    }


def _open_capa_for_kpi(db, kpi, measurement, user_id):
    """Uyumsuz KPI için DÖF açar (aynı ölçüm / açık DÖF için tekrar açmaz)."""
    if measurement.capa_id:
        return None
    prefix = f"KPI sapması — {kpi.surec_kod}:"
    acik = (
        db.query(CorrectiveAction)
        .filter(
            CorrectiveAction.kaynak_tipi == "Performans / KPI",
            CorrectiveAction.durum != "Kapatıldı",
            CorrectiveAction.baslik.like(f"{prefix}%"),
            CorrectiveAction.baslik.ilike(f"%{kpi.parametre[:80]}%"),
        )
        .first()
    )
    if acik:
        measurement.capa_id = acik.id
        return acik

    tanim = (
        f"Süreç: {kpi.surec_kod}\n"
        f"KPI: {kpi.parametre}\n"
        f"Hedef: {kpi.hedef_metin} {kpi.birim or ''}\n"
        f"Dönem: {measurement.donem}\n"
        f"Gerçekleşen: {measurement.gerceklesen if measurement.gerceklesen is not None else measurement.gerceklesen_metin}\n"
        f"Sonuç: UYUMSUZ — hedef karşılanmadı."
    )
    capa = CorrectiveAction(
        dof_no=next_sequence_no(db, CorrectiveAction, "dof_no", "DÖF"),
        baslik=f"{prefix} {kpi.parametre[:120]}",
        kaynak_tipi="Performans / KPI",
        ilgili_surec_id=kpi.surec_id,
        tespit_tarihi=date.today(),
        acan_id=user_id,
        tanim=tanim,
        durum="Açık",
        planlanan_tarih=date.today() + timedelta(days=30),
    )
    db.add(capa)
    db.flush()
    measurement.capa_id = capa.id
    return capa


def _upsert_measurement(db, kpi, donem, raw, notlar, user_id, open_dof=True):
    """Ölçüm kaydeder; uyumsuz + open_dof ise DÖF açar. Dönüş: (measurement, capa|None)."""
    raw = (raw or "").strip()
    if not raw:
        return None, None
    gercek = _to_float(raw)
    durum = evaluate_kpi(
        kpi.hedef_tip, kpi.hedef_deger, kpi.hedef_deger_ust, gercek, kpi.birim
    )
    m = (
        db.query(ProcessKPIMeasurement)
        .filter_by(kpi_id=kpi.id, donem=donem)
        .first()
    )
    if not m:
        m = ProcessKPIMeasurement(kpi_id=kpi.id, donem=donem)
        db.add(m)
    m.gerceklesen = gercek
    m.gerceklesen_metin = raw if gercek is None else None
    m.durum = durum
    m.notlar = (notlar or "").strip() or m.notlar
    m.giren_id = user_id
    m.guncelleme_tarihi = datetime.now()
    db.flush()
    capa = None
    if durum == "Uyumsuz" and open_dof:
        capa = _open_capa_for_kpi(db, kpi, m, user_id)
    return m, capa


# ── Panel: süreç kartları ───────────────────────────────────────────────────
@app.route("/performance")
@login_required
def performance_dashboard():
    db = get_db()
    try:
        kpis = (
            db.query(ProcessKPI)
            .filter_by(aktif=True)
            .order_by(ProcessKPI.surec_kod, ProcessKPI.sira_no)
            .all()
        )
        son = _latest_by_kpi(db, [k.id for k in kpis])
        stats = _summarize(kpis, son)

        procs = {p.kod: p for p in db.query(Process).all()}
        by_kod = {}
        for k in kpis:
            by_kod.setdefault(k.surec_kod, []).append(k)

        kartlar = []
        for kod in sorted(by_kod.keys()):
            grup = by_kod[kod]
            p = procs.get(kod)
            s = _summarize(grup, son)
            kartlar.append({
                "kod": kod,
                "ad": p.ad if p else kod,
                "kategori": (p.kategori if p else "Destek"),
                "sorumlu": (p.sorumlu if p else None),
                "stats": s,
            })

        # Kategori sırası
        kat_sira = {"Yönetim": 0, "Ana": 1, "Destek": 2}
        kartlar.sort(key=lambda c: (kat_sira.get(c["kategori"], 9), c["kod"]))

        return render_template(
            "performance.html",
            kartlar=kartlar,
            stats=stats,
            excel_var=os.path.isfile(DEFAULT_KPI_XLSX),
            kpi_yuklu=bool(kpis),
        )
    finally:
        db.close()


@app.route("/performance/import", methods=["POST"])
@login_required
@admin_required
def performance_import():
    db = get_db()
    temp_path = None
    try:
        replace = bool(request.form.get("replace"))
        file = request.files.get("file")
        
        if file and file.filename:
            # Uploaded file
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
            os.close(fd)
            file.save(temp_path)
            import_path = temp_path
        else:
            # Fallback to default
            if not os.path.isfile(DEFAULT_KPI_XLSX):
                flash("KPI Excel dosyası seçilmedi ve varsayılan şablon bulunamadı.", "error")
                return redirect(url_for("performance_dashboard"))
            import_path = DEFAULT_KPI_XLSX
            
        added, skipped, olcum_add, olcum_upd = import_kpis_to_db(db, path=import_path, replace=replace)
        log_action(db, "Oluşturma", detay=f"KPI import: +{added}, atlanan={skipped}")
        flash(f"KPI tanımları aktarıldı: {added} yeni, {skipped} atlandı. Ölçümler: {olcum_add} yeni, {olcum_upd} güncellendi.", "success")
        return redirect(url_for("performance_dashboard"))
    except Exception as exc:
        db.rollback()
        import traceback
        traceback.print_exc()
        flash(f"KPI aktarımı başarısız: {exc}", "error")
        return redirect(url_for("performance_dashboard"))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        db.close()


# ── Süreç detayı + toplu ölçüm ──────────────────────────────────────────────
@app.route("/performance/process/<kod>", methods=["GET", "POST"])
@login_required
def performance_process(kod):
    kod = (kod or "").strip().upper()
    db = get_db()
    try:
        proc = db.query(Process).filter_by(kod=kod).first()
        kpis = (
            db.query(ProcessKPI)
            .filter_by(aktif=True, surec_kod=kod)
            .order_by(ProcessKPI.sira_no, ProcessKPI.id)
            .all()
        )
        if not kpis and not proc:
            flash("Süreç / KPI bulunamadı.", "error")
            return redirect(url_for("performance_dashboard"))

        if request.method == "POST":
            if not _can_edit():
                abort(403)
            donem = (request.form.get("donem") or "").strip() or str(date.today().year)
            open_dof = bool(request.form.get("dof_ac"))
            kaydedilen = 0
            dofler = []
            for k in kpis:
                raw = request.form.get(f"deger_{k.id}", "")
                if not (raw or "").strip():
                    continue
                m, capa = _upsert_measurement(
                    db, k, donem, raw, None, session.get("user_id"), open_dof=open_dof
                )
                if m:
                    kaydedilen += 1
                if capa:
                    dofler.append(capa.dof_no)
            db.commit()
            if dofler:
                log_action(db, "Oluşturma", detay=f"KPI toplu ölçüm → DÖF: {', '.join(dofler)}")
                flash(
                    f"{kaydedilen} ölçüm kaydedildi. Açılan DÖF: {', '.join(dofler)}",
                    "warning",
                )
            else:
                flash(f"{kaydedilen} ölçüm kaydedildi ({donem}).", "success")
            return redirect(url_for("performance_process", kod=kod, donem=donem))

        son = _latest_by_kpi(db, [k.id for k in kpis])
        stats = _summarize(kpis, son)

        # Varsayılan dönem: süreçteki en sık periyoda göre
        from collections import Counter
        per = Counter((k.gg_periyot or "1Y") for k in kpis).most_common(1)
        default_per = per[0][0] if per else "1Y"
        donem = (request.args.get("donem") or "").strip() or suggest_donem(default_per)

        # Bu dönemdeki mevcut değerler
        donem_map = {}
        if kpis:
            for m in (
                db.query(ProcessKPIMeasurement)
                .filter(
                    ProcessKPIMeasurement.kpi_id.in_([k.id for k in kpis]),
                    ProcessKPIMeasurement.donem == donem,
                )
                .all()
            ):
                donem_map[m.kpi_id] = m

        return render_template(
            "performance_process.html",
            proc=proc,
            kod=kod,
            kpis=kpis,
            son_olcum=son,
            donem_olcum=donem_map,
            stats=stats,
            donem=donem,
            donemler=donem_secenekleri(),
            can_edit=_can_edit(),
        )
    finally:
        db.close()


# ── Tek KPI detay ───────────────────────────────────────────────────────────
@app.route("/performance/kpi/<int:kpi_id>", methods=["GET", "POST"])
@app.route("/performance/<int:kpi_id>", methods=["GET", "POST"])
@login_required
def performance_kpi_detail(kpi_id):
    db = get_db()
    try:
        kpi = db.get(ProcessKPI, kpi_id)
        if not kpi:
            flash("KPI bulunamadı.", "error")
            return redirect(url_for("performance_dashboard"))

        if request.method == "POST":
            if not _can_edit():
                abort(403)
            donem = (request.form.get("donem") or "").strip() or suggest_donem(kpi.gg_periyot)
            raw = request.form.get("gerceklesen") or ""
            notlar = request.form.get("notlar")
            open_dof = bool(request.form.get("dof_ac", "1"))
            m, capa = _upsert_measurement(
                db, kpi, donem, raw, notlar, session.get("user_id"), open_dof=open_dof
            )
            if not m:
                flash("Gerçekleşen değer girilmedi.", "error")
                return redirect(url_for("performance_kpi_detail", kpi_id=kpi.id))
            db.commit()
            if capa:
                log_action(db, "Oluşturma", detay=f"KPI uyumsuzluğu → DÖF {capa.dof_no}")
                flash(f"Ölçüm kaydedildi ({m.durum}). DÖF açıldı: {capa.dof_no}", "warning")
                try:
                    if capa.sorumlu:
                        notifications.notify_capa_assigned(capa, capa.sorumlu)
                except Exception:
                    pass
            else:
                flash(f"Ölçüm kaydedildi: {m.durum}", "success")
            return redirect(url_for("performance_kpi_detail", kpi_id=kpi.id))

        olcumler = (
            db.query(ProcessKPIMeasurement)
            .filter_by(kpi_id=kpi.id)
            .order_by(ProcessKPIMeasurement.donem.asc())
            .all()
        )
        chart = {
            "labels": [m.donem for m in olcumler if m.gerceklesen is not None],
            "values": [m.gerceklesen for m in olcumler if m.gerceklesen is not None],
        }
        return render_template(
            "performance_kpi_detail.html",
            kpi=kpi,
            olcumler=list(reversed(olcumler)),
            chart=chart,
            durumlar=KPI_OLCUM_DURUMLARI,
            onerilen_donem=suggest_donem(kpi.gg_periyot),
            donemler=donem_secenekleri(),
            can_edit=_can_edit(),
        )
    finally:
        db.close()
