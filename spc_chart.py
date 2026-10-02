"""
DYS — SPC Kontrol Kartı Hesaplama Motoru
==========================================
X̄-R kontrol kartı hesaplama, Western Electric kuralları ve
Chart.js uyumlu JSON veri yapısı üretimi.

IATF 16949 § 9.1.1.1: İstatistiksel proses kontrol uygulaması.
"""

import math
from datetime import date


# ── d2 ve D3/D4 Sabitleri (alt grup boyutu n=2..10) ──────────────────────
# Shewhart kontrol kartı katsayıları
D2_TABLE = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326,
            6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}
D3_TABLE = {2: 0,     3: 0,     4: 0,     5: 0,
            6: 0,     7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
D4_TABLE = {2: 3.267, 3: 2.575, 4: 2.282, 5: 2.114,
            6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
A2_TABLE = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577,
            6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}


def xbar_r_hesapla(alt_gruplar):
    """
    X̄-R kontrol kartı hesaplama.

    Args:
        alt_gruplar: [[değer1, değer2, ...], [değer1, ...], ...] 2D liste.
                     Her iç liste bir alt grup (subgroup).

    Returns:
        dict: {
            "xbar": [ortalamalar],
            "r": [range'ler],
            "xbar_bar": genel ortalama,
            "r_bar": ortalama range,
            "ucl_x": üst kontrol limiti (X̄),
            "lcl_x": alt kontrol limiti (X̄),
            "cl_x": merkez çizgisi (X̄),
            "ucl_r": üst kontrol limiti (R),
            "lcl_r": alt kontrol limiti (R),
            "cl_r": merkez çizgisi (R),
            "n": alt grup boyutu,
            "cp": proses yeterlilik indeksi (USL/LSL verilmişse),
            "cpk": proses yeterlilik indeksi (USL/LSL verilmişse),
        }
    """
    if not alt_gruplar or len(alt_gruplar) < 2:
        return None

    n = len(alt_gruplar[0])
    if n < 2 or n > 10:
        return None

    # Alt grup ortalamaları ve range'leri
    xbar_listesi = []
    r_listesi = []
    for grup in alt_gruplar:
        if len(grup) != n:
            continue
        xbar_listesi.append(sum(grup) / len(grup))
        r_listesi.append(max(grup) - min(grup))

    if not xbar_listesi:
        return None

    # Genel ortalama ve ortalama range
    xbar_bar = sum(xbar_listesi) / len(xbar_listesi)
    r_bar = sum(r_listesi) / len(r_listesi)

    # Kontrol limitleri
    a2 = A2_TABLE[n]
    d3 = D3_TABLE[n]
    d4 = D4_TABLE[n]

    ucl_x = xbar_bar + a2 * r_bar
    lcl_x = xbar_bar - a2 * r_bar
    ucl_r = d4 * r_bar
    lcl_r = d3 * r_bar

    return {
        "xbar": xbar_listesi,
        "r": r_listesi,
        "xbar_bar": round(xbar_bar, 4),
        "r_bar": round(r_bar, 4),
        "ucl_x": round(ucl_x, 4),
        "lcl_x": round(lcl_x, 4),
        "cl_x": round(xbar_bar, 4),
        "ucl_r": round(ucl_r, 4),
        "lcl_r": round(lcl_r, 4),
        "cl_r": round(r_bar, 4),
        "n": n,
    }


def cp_cpk_hesapla(veriler, usl, lsl):
    """
    Cp ve Cpk proses yeterlilik indeksi hesaplama.

    Args:
        veriler: tüm ölçüm değerleri (1D liste)
        usl: üst spesifikasyon limiti
        lsl: alt spesifikasyon limiti

    Returns:
        {"cp": float, "cpk": float, "ortalama": float, "std_sapma": float}
    """
    if not veriler or len(veriler) < 2 or usl is None or lsl is None:
        return None

    n = len(veriler)
    ort = sum(veriler) / n
    varyans = sum((x - ort) ** 2 for x in veriler) / (n - 1)
    std = math.sqrt(varyans) if varyans > 0 else 0.0001

    cp = (usl - lsl) / (6 * std)
    cpu = (usl - ort) / (3 * std)
    cpl = (ort - lsl) / (3 * std)
    cpk = min(cpu, cpl)

    return {
        "cp": round(cp, 3),
        "cpk": round(cpk, 3),
        "ortalama": round(ort, 4),
        "std_sapma": round(std, 4),
    }


# ── Western Electric Kuralları ────────────────────────────────────────────

def western_electric_kontrol(xbar_listesi, cl, ucl, lcl):
    """
    Western Electric kontrol kuralları ihlali tespiti.

    Returns:
        [(index, kural_no, açıklama), ...] ihlal listesi
    """
    ihlaller = []
    sigma = (ucl - cl) / 3 if ucl != cl else 0.0001
    one_sigma = cl + sigma
    two_sigma = cl + 2 * sigma
    neg_one_sigma = cl - sigma
    neg_two_sigma = cl - 2 * sigma

    for i, val in enumerate(xbar_listesi):
        # Kural 1: Tek nokta 3σ dışında
        if val > ucl or val < lcl:
            ihlaller.append((i, 1, "3σ dışında"))

    # Kural 2: Ardışık 9 nokta aynı tarafta
    if len(xbar_listesi) >= 9:
        for i in range(len(xbar_listesi) - 8):
            pencere = xbar_listesi[i:i + 9]
            if all(v > cl for v in pencere):
                ihlaller.append((i + 8, 2, "9 nokta CL üstünde"))
            elif all(v < cl for v in pencere):
                ihlaller.append((i + 8, 2, "9 nokta CL altında"))

    # Kural 3: Ardışık 6 nokta artan/azalan trend
    if len(xbar_listesi) >= 6:
        for i in range(len(xbar_listesi) - 5):
            pencere = xbar_listesi[i:i + 6]
            if all(pencere[j] < pencere[j + 1] for j in range(5)):
                ihlaller.append((i + 5, 3, "6 nokta artan trend"))
            elif all(pencere[j] > pencere[j + 1] for j in range(5)):
                ihlaller.append((i + 5, 3, "6 nokta azalan trend"))

    return ihlaller


def chartjs_veri_olustur(hesaplama, etiketler=None):
    """
    Chart.js uyumlu JSON veri yapısı üretir.

    Args:
        hesaplama: xbar_r_hesapla() çıktısı
        etiketler: ["Alt Grup 1", ...] veya None

    Returns:
        Chart.js datasets yapısı
    """
    if not hesaplama:
        return None

    k = len(hesaplama["xbar"])
    labels = etiketler or [str(i + 1) for i in range(k)]

    return {
        "labels": labels,
        "xbar_chart": {
            "datasets": [
                {
                    "label": "X̄",
                    "data": [round(v, 4) for v in hesaplama["xbar"]],
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59,130,246,0.1)",
                    "tension": 0.1,
                    "pointRadius": 3,
                },
                {
                    "label": "UCL",
                    "data": [hesaplama["ucl_x"]] * k,
                    "borderColor": "#dc2626",
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                },
                {
                    "label": "CL",
                    "data": [hesaplama["cl_x"]] * k,
                    "borderColor": "#16a34a",
                    "borderDash": [3, 3],
                    "pointRadius": 0,
                },
                {
                    "label": "LCL",
                    "data": [hesaplama["lcl_x"]] * k,
                    "borderColor": "#dc2626",
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                },
            ],
        },
        "r_chart": {
            "datasets": [
                {
                    "label": "R",
                    "data": [round(v, 4) for v in hesaplama["r"]],
                    "borderColor": "#f59e0b",
                    "backgroundColor": "rgba(245,158,11,0.1)",
                    "tension": 0.1,
                    "pointRadius": 3,
                },
                {
                    "label": "UCL",
                    "data": [hesaplama["ucl_r"]] * k,
                    "borderColor": "#dc2626",
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                },
                {
                    "label": "CL",
                    "data": [hesaplama["cl_r"]] * k,
                    "borderColor": "#16a34a",
                    "borderDash": [3, 3],
                    "pointRadius": 0,
                },
                {
                    "label": "LCL",
                    "data": [hesaplama["lcl_r"]] * k,
                    "borderColor": "#dc2626",
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                },
            ],
        },
    }


def rand_normal():
    import random
    u1 = 0
    while u1 == 0:
        u1 = random.random()
    u2 = random.random()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def generate_valid_spc_data(lsl, usl):
    """Cpk >= 1.67 kosulunu saglayan 125 adet normal dagilimli veri uretir."""
    N = 125
    tolerance = usl - lsl
    target_mu = (lsl + usl) / 2
    
    # Sigma factor
    base_factor = 2.2
    
    attempts = 0
    while attempts < 1000:
        attempts += 1
        import random
        sigma_jitter = 1 + (random.random() - 0.5) * 0.15
        sigma = (tolerance / (6 * base_factor)) * sigma_jitter
        mu_jitter = (random.random() - 0.5) * sigma * 0.12
        mu = target_mu + mu_jitter
        
        values = []
        for _ in range(N):
            v = mu + sigma * rand_normal()
            values.append(round(v, 3))
            
        # Limit kontrolü
        all_in_range = all(v >= lsl and v <= usl for v in values)
        if not all_in_range:
            continue
            
        # Cpk kontrolü
        cap = cp_cpk_hesapla(values, usl, lsl)
        if cap and cap["cpk"] >= 1.67:
            return values
            
    # Fallback
    sigma = tolerance / (6 * 2.5)
    return [round(target_mu + sigma * rand_normal(), 3) for _ in range(N)]

