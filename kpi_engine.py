"""
Y03 F06 süreç performans KPI — hedef parse ve değerlendirme.
"""

from __future__ import annotations

import re
from typing import Optional


def _to_float(raw) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(" ", "").replace(",", ".")
    s = s.replace("%", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def parse_hedef(hedef_raw, birim=None):
    """
    Hedef ifadesini yapılandırılmış kurala çevirir.
    Dönüş: {tip, deger, deger_ust, metin}
      tip: monitor | min | max | eq | range
    """
    metin = ("" if hedef_raw is None else str(hedef_raw)).strip()
    low = metin.lower()
    if not metin or "izleme" in low:
        return {"tip": "monitor", "deger": None, "deger_ust": None, "metin": metin or "İzlemeye yönelik"}

    # 32<KKO<68 / 32 < x < 68
    m = re.match(
        r"^([\d]+(?:[.,]\d+)?)\s*<\s*[A-Za-zÇĞİÖŞÜçğıöşü%]*\s*<\s*([\d]+(?:[.,]\d+)?)$",
        metin.replace(" ", ""),
        re.I,
    )
    if m:
        return {
            "tip": "range",
            "deger": _to_float(m.group(1)),
            "deger_ust": _to_float(m.group(2)),
            "metin": metin,
        }

    # ppm =%0,9 → üst sınır (max)
    if "ppm" in low or re.search(r"=\s*%", metin):
        val = _to_float(metin)
        if val is not None:
            return {"tip": "max", "deger": val, "deger_ust": None, "metin": metin}

    # <3,4  >98  >=82  <=10
    m = re.match(r"^(<=|>=|<|>|=)\s*([\d]+(?:[.,]\d+)?)", metin.strip())
    if m:
        op, num = m.group(1), _to_float(m.group(2))
        if op in ("<", "<="):
            return {"tip": "max", "deger": num, "deger_ust": None, "metin": metin}
        if op in (">", ">="):
            return {"tip": "min", "deger": num, "deger_ust": None, "metin": metin}
        return {"tip": "eq", "deger": num, "deger_ust": None, "metin": metin}

    # Düz sayı: 0 → eq, 98.5 → eq (genelde tam hedef)
    val = _to_float(metin)
    if val is not None and re.fullmatch(r"[\d\s.,]+%?", metin.replace(" ", "")):
        return {"tip": "eq", "deger": val, "deger_ust": None, "metin": metin}

    return {"tip": "monitor", "deger": None, "deger_ust": None, "metin": metin}


def _normalize_actual(actual: float, hedef: float, birim: str | None) -> float:
    """Hedef yüzde (ör. 82) iken gerçekleşen 0–1 oran ise 100 ile çarp."""
    b = (birim or "").lower()
    if "%" in b or b.strip() == "%":
        if hedef is not None and hedef > 1 and 0 <= actual <= 1.5:
            return actual * 100.0
    return actual


def evaluate_kpi(hedef_tip, hedef_deger, hedef_deger_ust, gerceklesen, birim=None):
    """
    Dönüş: 'Uyumlu' | 'Uyumsuz' | 'İzleme' | 'Girilmedi'
    """
    if gerceklesen is None:
        return "Girilmedi"
    if hedef_tip == "monitor" or hedef_tip is None:
        return "İzleme"
    if hedef_deger is None and hedef_tip != "range":
        return "İzleme"

    actual = float(gerceklesen)
    if hedef_deger is not None:
        actual = _normalize_actual(actual, float(hedef_deger), birim)

    tip = hedef_tip
    if tip == "min":
        return "Uyumlu" if actual >= float(hedef_deger) else "Uyumsuz"
    if tip == "max":
        return "Uyumlu" if actual <= float(hedef_deger) else "Uyumsuz"
    if tip == "eq":
        # Küçük tolerans
        return "Uyumlu" if abs(actual - float(hedef_deger)) < 1e-6 else "Uyumsuz"
    if tip == "range":
        lo, hi = hedef_deger, hedef_deger_ust
        if lo is None or hi is None:
            return "İzleme"
        return "Uyumlu" if float(lo) < actual < float(hi) else "Uyumsuz"
    return "İzleme"


def suggest_donem(gg_periyot) -> str:
    from datetime import date
    bugun = date.today()
    y = bugun.year
    m = bugun.month
    
    p = (gg_periyot or "").lower()
    
    if "ay" in p or "month" in p:
        return f"{y}-{m:02d}"
    
    if "çeyrek" in p or "quarter" in p or p.strip() == "q":
        q = (m - 1) // 3 + 1
        return f"{y}-Q{q}"
        
    if "yarı" in p or "half" in p or "6" in p:
        if m <= 6:
            return f"{y}-H1"
        else:
            return f"{y}-H2"
            
    return str(y)


def donem_secenekleri(yil=None):
    from datetime import date
    if not yil:
        y = date.today().year
    else:
        y = int(yil)
        
    secenekler = [str(y), f"{y}-H1", f"{y}-H2"]
    
    for q in range(1, 5):
        secenekler.append(f"{y}-Q{q}")
        
    for m in range(1, 13):
        secenekler.append(f"{y}-{m:02d}")
        
    py = y - 1
    secenekler.extend([str(py), f"{py}-H1", f"{py}-H2"])
    
    return secenekler

