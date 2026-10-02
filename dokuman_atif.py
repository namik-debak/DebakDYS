"""
DYS — Doküman atıf (referans) analizi (2026)
Dokümanların DYS içeriğinde (icerik_json: prosedür / iş akışı metinleri) geçen doküman kodlarını çıkarır ve
  * atif_yapanlar(no)   : bu dokümana atıf yapan yürürlükteki dokümanlar ("nerede kullanılıyor" — revizyon etki analizi)
  * atiflar(doc)        : bu dokümanın atıf yaptığı kodlar ve hedeflerin durumu
  * sorunlu_atiflar()   : DYS'de olmayan, Eskimiş / İptal ya da hariç tutulan dokümana verilen atıflar (rapor)
Şema değişikliği yoktur; dizin bellekte tutulur ve doküman sayısı / son güncelleme değişince yeniden kurulur.
Not: yalnız DYS'de metni olan dokümanlar (şablondan üretilen prosedür / iş akışı) taranır; Word / Excel dosya içleri taranmaz.
"""
import json
import os
import re
from datetime import datetime

from sqlalchemy import func

from models import Document

# '11 süreçlik yapı' kodları (D04.2 T03, M03 P01, Y01.6 F01) ve eski DYS kodları (Y01-PR-001)
KOD_RE = re.compile(r"(?<![\w.])([MDY]\d{2}(?:\.\d{1,2})? (?:GT|[PATF])\d{2,3}|[A-Z]\d{2}-[A-Z]{2}-\d{3})(?![\w])")
PASIF = ("Eskimiş", "İptal")
# Eski koda yapılan bilgi amaçlı anmalar atıf sayılmaz: "(eski: D08 P09 / D01.3 P01)", "eski D05 P02'deki ..."
ESKI_RE = re.compile(r"\((?:eski|önceki)\b[^)]*\)|\b(?:eski|önceki)(?: kod)?:? (?:" + KOD_RE.pattern + r")", re.I)
_CACHE = {"imza": None, "dizin": {}, "ters": {}, "docs": {}}


def _metin(doc):
    ham = doc.icerik_json or ""
    if not ham:
        return ""
    try:  # JSON kaçışlarını çöz (ç vb.) ki kodlar bölünmesin
        return ESKI_RE.sub(" ", json.dumps(json.loads(ham), ensure_ascii=False))
    except ValueError:
        return ESKI_RE.sub(" ", ham)


def _haric_kodlar():
    """Canlıya aktarımda bilerek dışarıda bırakılan kodlar (varsa) — atıfları 'hariç' olarak işaretlenir."""
    yol = os.environ.get("DYS_HARIC_LISTESI") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "haric_tutulanlar.json")
    try:
        return set(json.load(open(yol, encoding="utf-8")).get("dokumanlar") or []) if os.path.isfile(yol) else set()
    except (OSError, ValueError):
        return set()


def dizin(db):
    """{doc_id: set(kod)} ve ters dizin {kod: set(doc_id)} — imza değişmedikçe önbellekten."""
    imza = db.query(func.count(Document.id), func.max(Document.guncelleme_tarihi)).one()
    if _CACHE["imza"] == imza:
        return _CACHE
    d, ters, docs = {}, {}, {}
    for doc in db.query(Document).all():
        docs[doc.dokuman_no] = (doc.id, doc.durum, doc.baslik, doc.yerine_gecen_id)
        kodlar = {k for k in KOD_RE.findall(_metin(doc)) if k != doc.dokuman_no}
        if kodlar:
            d[doc.id] = kodlar
            for k in kodlar:
                ters.setdefault(k, set()).add(doc.id)
    _CACHE.update(imza=imza, dizin=d, ters=ters, docs=docs)
    return _CACHE


def atif_yapanlar(db, dokuman_no, yalniz_yururlukte=True):
    c = dizin(db)
    ids = c["ters"].get(dokuman_no) or set()
    if not ids:
        return []
    q = db.query(Document).filter(Document.id.in_(ids))
    if yalniz_yururlukte:
        q = q.filter(Document.durum.notin_(PASIF))
    return q.order_by(Document.dokuman_no).all()


def atiflar(db, doc):
    """[(kod, durum_etiketi, hedef_id veya None)] — durum: 'Yürürlükte' / 'Taslak' / 'Eskimiş' / 'İptal' / 'DYS'de yok'."""
    c = dizin(db)
    out = []
    for k in sorted(c["dizin"].get(doc.id) or []):
        h = c["docs"].get(k)
        out.append((k, ("Yürürlükte" if h[1] == "Onaylı" else h[1]) if h else "DYS'de yok", h[0] if h else None))
    return out


def sorunlu_atiflar(db):
    """Yürürlükteki / taslak dokümanlardaki sorunlu atıflar: [{kaynak, kod, sorun, oneri}]"""
    c = dizin(db)
    haric = _haric_kodlar()
    kaynaklar = {d.id: d for d in db.query(Document).filter(Document.id.in_(list(c["dizin"])), Document.durum.notin_(PASIF)).all()} if c["dizin"] else {}
    id_no = {v[0]: k for k, v in c["docs"].items()}
    out = []
    for did, kodlar in c["dizin"].items():
        kaynak = kaynaklar.get(did)
        if not kaynak:
            continue
        for k in sorted(kodlar):
            h = c["docs"].get(k)
            if h and h[1] not in PASIF:
                continue
            if h:
                sorun = f"hedef doküman {h[1]}"
                oneri = f"yerine geçen: {id_no.get(h[3])}" if h[3] and id_no.get(h[3]) else "güncel dokümana yönlendirin veya atfı kaldırın"
            elif k in haric:
                sorun, oneri = "hariç tutulan doküman", "atfı kaldırın ya da ilgili DYS modülünü yazın"
            else:
                sorun, oneri = "DYS'de böyle bir doküman yok", "kodu kontrol edin (yazım / eski kod)"
            out.append({"kaynak": kaynak, "kod": k, "sorun": sorun, "oneri": oneri})
    out.sort(key=lambda x: (x["kaynak"].dokuman_no, x["kod"]))
    return out


def ozet(db):
    c = dizin(db)
    return {"taranan": len(c["dizin"]), "atif": sum(len(v) for v in c["dizin"].values()), "zaman": datetime.now()}
