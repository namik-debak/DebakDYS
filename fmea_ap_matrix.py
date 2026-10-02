"""
DYS — VDA/AIAG FMEA Handbook Action Priority (AP) Matrisi
==========================================================
C2.5 ACTION PRIORITY TABLE FOR PFMEA (1st Edition, 2019)

S × O × D kombinasyonunu Action Priority seviyesine (H / M / L) çevirir.
RPN (S×O×D çarpımı) kullanılmaz; bunun yerine grup-tabanlı matris kullanılır.
"""

# ── Grup sınıflandırma fonksiyonları ──────────────────────────────────────

def s_grubu(s: int) -> str:
    """Severity (Şiddet) değerini grup etiketine çevirir."""
    if s <= 0 or s > 10:
        raise ValueError(f"S değeri 1-10 arasında olmalıdır, verilen: {s}")
    if s == 1:
        return "1"
    if s <= 3:
        return "2-3"
    if s <= 6:
        return "4-6"
    if s <= 8:
        return "7-8"
    return "9-10"


def o_grubu(o: int) -> str:
    """Occurrence (Oluşma) değerini grup etiketine çevirir."""
    if o <= 0 or o > 10:
        raise ValueError(f"O değeri 1-10 arasında olmalıdır, verilen: {o}")
    if o == 1:
        return "1"
    if o <= 3:
        return "2-3"
    if o <= 5:
        return "4-5"
    if o <= 7:
        return "6-7"
    return "8-10"


def d_grubu(d: int) -> str:
    """Detection (Tespit) değerini grup etiketine çevirir."""
    if d <= 0 or d > 10:
        raise ValueError(f"D değeri 1-10 arasında olmalıdır, verilen: {d}")
    if d == 1:
        return "1"
    if d <= 4:
        return "2-4"
    if d <= 6:
        return "5-6"
    return "7-10"


# ── C2.5 PFMEA Action Priority Tablosu ───────────────────────────────────
# Anahtar: (S_grup, O_grup, D_grup) → AP seviyesi
# Handbook'taki tablo satır satır kodlanmıştır.

_PFMEA_AP: dict[tuple[str, str, str], str] = {
    # ────────── S = 9-10 ──────────
    # O = 8-10
    ("9-10", "8-10", "7-10"): "H",
    ("9-10", "8-10", "5-6"):  "H",
    ("9-10", "8-10", "2-4"):  "H",
    ("9-10", "8-10", "1"):    "H",
    # O = 6-7
    ("9-10", "6-7", "7-10"):  "H",
    ("9-10", "6-7", "5-6"):   "H",
    ("9-10", "6-7", "2-4"):   "H",
    ("9-10", "6-7", "1"):     "H",
    # O = 4-5
    ("9-10", "4-5", "7-10"):  "H",
    ("9-10", "4-5", "5-6"):   "H",
    ("9-10", "4-5", "2-4"):   "H",
    ("9-10", "4-5", "1"):     "M",
    # O = 2-3
    ("9-10", "2-3", "7-10"):  "H",
    ("9-10", "2-3", "5-6"):   "H",
    ("9-10", "2-3", "2-4"):   "M",
    ("9-10", "2-3", "1"):     "L",
    # O = 1
    ("9-10", "1", "7-10"):    "M",
    ("9-10", "1", "5-6"):     "L",
    ("9-10", "1", "2-4"):     "L",
    ("9-10", "1", "1"):       "L",

    # ────────── S = 7-8 ──────────
    # O = 8-10
    ("7-8", "8-10", "7-10"):  "H",
    ("7-8", "8-10", "5-6"):   "H",
    ("7-8", "8-10", "2-4"):   "H",
    ("7-8", "8-10", "1"):     "H",
    # O = 6-7
    ("7-8", "6-7", "7-10"):   "H",
    ("7-8", "6-7", "5-6"):    "H",
    ("7-8", "6-7", "2-4"):    "H",
    ("7-8", "6-7", "1"):      "M",
    # O = 4-5
    ("7-8", "4-5", "7-10"):   "H",
    ("7-8", "4-5", "5-6"):    "M",
    ("7-8", "4-5", "2-4"):    "M",
    ("7-8", "4-5", "1"):      "L",
    # O = 2-3
    ("7-8", "2-3", "7-10"):   "M",
    ("7-8", "2-3", "5-6"):    "M",
    ("7-8", "2-3", "2-4"):    "L",
    ("7-8", "2-3", "1"):      "L",
    # O = 1
    ("7-8", "1", "7-10"):     "L",
    ("7-8", "1", "5-6"):      "L",
    ("7-8", "1", "2-4"):      "L",
    ("7-8", "1", "1"):        "L",

    # ────────── S = 4-6 ──────────
    # O = 8-10
    ("4-6", "8-10", "7-10"):  "H",
    ("4-6", "8-10", "5-6"):   "H",
    ("4-6", "8-10", "2-4"):   "M",
    ("4-6", "8-10", "1"):     "M",
    # O = 6-7
    ("4-6", "6-7", "7-10"):   "M",
    ("4-6", "6-7", "5-6"):    "M",
    ("4-6", "6-7", "2-4"):    "M",
    ("4-6", "6-7", "1"):      "L",
    # O = 4-5
    ("4-6", "4-5", "7-10"):   "M",
    ("4-6", "4-5", "5-6"):    "L",
    ("4-6", "4-5", "2-4"):    "L",
    ("4-6", "4-5", "1"):      "L",
    # O = 2-3
    ("4-6", "2-3", "7-10"):   "L",
    ("4-6", "2-3", "5-6"):    "L",
    ("4-6", "2-3", "2-4"):    "L",
    ("4-6", "2-3", "1"):      "L",
    # O = 1
    ("4-6", "1", "7-10"):     "L",
    ("4-6", "1", "5-6"):      "L",
    ("4-6", "1", "2-4"):      "L",
    ("4-6", "1", "1"):        "L",

    # ────────── S = 2-3 ──────────
    # O = 8-10
    ("2-3", "8-10", "7-10"):  "M",
    ("2-3", "8-10", "5-6"):   "M",
    ("2-3", "8-10", "2-4"):   "L",
    ("2-3", "8-10", "1"):     "L",
    # O = 6-7
    ("2-3", "6-7", "7-10"):   "M",
    ("2-3", "6-7", "5-6"):    "L",
    ("2-3", "6-7", "2-4"):    "L",
    ("2-3", "6-7", "1"):      "L",
    # O = 4-5
    ("2-3", "4-5", "7-10"):   "L",
    ("2-3", "4-5", "5-6"):    "L",
    ("2-3", "4-5", "2-4"):    "L",
    ("2-3", "4-5", "1"):      "L",
    # O = 2-3
    ("2-3", "2-3", "7-10"):   "L",
    ("2-3", "2-3", "5-6"):    "L",
    ("2-3", "2-3", "2-4"):    "L",
    ("2-3", "2-3", "1"):      "L",
    # O = 1
    ("2-3", "1", "7-10"):     "L",
    ("2-3", "1", "5-6"):      "L",
    ("2-3", "1", "2-4"):      "L",
    ("2-3", "1", "1"):        "L",

    # ────────── S = 1 ──────────
    # Tüm O ve D kombinasyonları için L
    ("1", "8-10", "7-10"):    "L",
    ("1", "8-10", "5-6"):     "L",
    ("1", "8-10", "2-4"):     "L",
    ("1", "8-10", "1"):       "L",
    ("1", "6-7", "7-10"):     "L",
    ("1", "6-7", "5-6"):      "L",
    ("1", "6-7", "2-4"):      "L",
    ("1", "6-7", "1"):        "L",
    ("1", "4-5", "7-10"):     "L",
    ("1", "4-5", "5-6"):      "L",
    ("1", "4-5", "2-4"):      "L",
    ("1", "4-5", "1"):        "L",
    ("1", "2-3", "7-10"):     "L",
    ("1", "2-3", "5-6"):      "L",
    ("1", "2-3", "2-4"):      "L",
    ("1", "2-3", "1"):        "L",
    ("1", "1", "7-10"):       "L",
    ("1", "1", "5-6"):        "L",
    ("1", "1", "2-4"):        "L",
    ("1", "1", "1"):          "L",
}


def hesapla_ap(s: int, o: int, d: int) -> str:
    """
    Severity, Occurrence ve Detection değerlerinden Action Priority hesaplar.

    Args:
        s: Severity (Şiddet) 1-10
        o: Occurrence (Oluşma) 1-10
        d: Detection (Tespit) 1-10

    Returns:
        "H" (High), "M" (Medium) veya "L" (Low)
    """
    key = (s_grubu(s), o_grubu(o), d_grubu(d))
    ap = _PFMEA_AP.get(key)
    if ap is None:
        raise ValueError(f"AP tablosunda bulunamadı: S={s}, O={o}, D={d} → {key}")
    return ap


# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────

AP_RENKLER = {
    "H": {"bg": "#dc2626", "fg": "#ffffff", "label": "High"},
    "M": {"bg": "#f59e0b", "fg": "#000000", "label": "Medium"},
    "L": {"bg": "#16a34a", "fg": "#ffffff", "label": "Low"},
}


def ap_renk(ap: str) -> dict:
    """AP seviyesinin CSS renk bilgisini döndürür."""
    return AP_RENKLER.get(ap, AP_RENKLER["L"])


def ap_ozet(items) -> dict:
    """
    FMEA satırlarının AP dağılım özetini döndürür.

    Args:
        items: FMEAItem listesi (her biri .siddet, .olusma, .tespit alanlarına sahip)

    Returns:
        {"H": count, "M": count, "L": count, "toplam": count}
    """
    sonuc = {"H": 0, "M": 0, "L": 0, "toplam": 0}
    for item in items:
        try:
            ap = hesapla_ap(item.siddet or 1, item.olusma or 1, item.tespit or 1)
            sonuc[ap] += 1
            sonuc["toplam"] += 1
        except (ValueError, TypeError):
            pass
    return sonuc


def toplu_ap_hesapla(items) -> list:
    """
    FMEA satırlarının AP değerlerini toplu hesaplar.

    Args:
        items: FMEAItem listesi

    Returns:
        [(item, ap_değeri), ...] listesi
    """
    sonuclar = []
    for item in items:
        try:
            ap = hesapla_ap(item.siddet or 1, item.olusma or 1, item.tespit or 1)
            sonuclar.append((item, ap))
        except (ValueError, TypeError):
            sonuclar.append((item, "L"))
    return sonuclar
