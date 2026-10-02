"""
DYS — M03 F08 Ürün Enjeksiyon Parametreleri: veri işlevleri (Flask'tan bağımsız; yeni_yapi_aktar.py da kullanır).
"""
import json
import re
from datetime import datetime

from models import EnjeksiyonUrun, EnjeksiyonParametreKaydi, SistemAyar


def tolerans(sapma):
    """'+/-100', '±0,5', '± 5' → 100.0 / 0.5 / 5.0; yüzde ya da metin ise None."""
    m = re.search(r"(?:\+/-|±|\+-)\s*(\d+(?:[.,]\d+)?)", str(sapma or ""))
    return float(m.group(1).replace(",", ".")) if m else None


def sayi(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def karsilastir(onceki, yeni):
    """Önceki kayda göre değişen ve tolerans dışına çıkan parametreler."""
    o = {p["ad"]: p for p in (onceki.parametreler if onceki else [])}
    sonuc = []
    for p in yeni:
        q = o.get(p["ad"])
        a, b, t = sayi(p.get("deger")), sayi(q.get("deger")) if q else None, tolerans(p.get("sapma") or (q or {}).get("sapma"))
        degisti = q is not None and (p.get("deger") or "") != (q.get("deger") or "")
        disi = degisti and a is not None and b is not None and t is not None and abs(a - b) > t + 1e-9
        sonuc.append({**p, "onceki": q.get("deger") if q else None, "degisti": degisti, "tolerans_disi": disi})
    return sonuc


def sablonlar(db):
    kayit = db.get(SistemAyar, "enjeksiyon_sablonlari")
    try:
        return json.loads(kayit.deger) if kayit and kayit.deger else []
    except ValueError:
        return []


def paketten_yukle(db, paket, degistir=False):
    """enjeksiyon_parametreleri.json → EnjeksiyonUrun + Excel geçmişi kayıtları (Onaylandı). Tekrar çalıştırılabilir:
    aynı kaynak sayfası varsa yalnız eksik geçmiş kayıtlar eklenir; DYS'de girilmiş kayıtlara dokunulmaz."""
    R = {"urun_yeni": 0, "urun_var": 0, "kayit": 0}
    mevcut = {u.kaynak: u for u in db.query(EnjeksiyonUrun).all() if u.kaynak}
    for u in paket.get("urunler", []):
        e = mevcut.get(u["kaynak"])
        if not e:
            e = EnjeksiyonUrun(urun_adi=u["urun_adi"][:200], musteri=(u.get("musteri") or "")[:100] or None,
                               tanim=(u.get("tanim") or "")[:250] or None, sablon=u.get("sablon"), kaynak=u["kaynak"][:300], aktif=True)
            db.add(e); db.flush(); R["urun_yeni"] += 1
        else:
            R["urun_var"] += 1
        var = {(k.tarih.isoformat() if k.tarih else None, k.makina or "", k.parametreler_json) for k in e.kayitlar if k.kaynak == "Excel geçmişi"}
        for k in u.get("kayitlar", []):
            pj = json.dumps(k["parametreler"], ensure_ascii=False)
            anahtar = (k.get("tarih"), (k.get("makina") or "")[:60], pj)
            if anahtar in var:
                continue
            db.add(EnjeksiyonParametreKaydi(
                urun_id=e.id, tarih=datetime.strptime(k["tarih"], "%Y-%m-%d").date() if k.get("tarih") else None,
                makina=(k.get("makina") or "")[:60] or None, malzeme=(k.get("malzeme") or "")[:100] or None,
                parametreler_json=pj, kaynak="Excel geçmişi", durum="Onaylandı",
                aciklama=f"Excel'den aktarıldı: {u['kaynak']} (sütun {k.get('sutun')})"))
            var.add(anahtar); R["kayit"] += 1
    if paket.get("sablonlar"):
        s = db.get(SistemAyar, "enjeksiyon_sablonlari")
        if not s:
            db.add(SistemAyar(anahtar="enjeksiyon_sablonlari", deger=json.dumps(paket["sablonlar"], ensure_ascii=False), guncelleme_tarihi=datetime.now()))
        elif degistir:
            s.deger = json.dumps(paket["sablonlar"], ensure_ascii=False); s.guncelleme_tarihi = datetime.now()
    db.commit()
    return R
