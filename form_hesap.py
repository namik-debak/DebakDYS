"""
DYS — Dinamik formlarda hesaplanan alanlar (2026)
Alan tanımı:  {"ad": "Ara toplam", "kod": "ara_toplam", "tip": "hesap", "formul": "b_hammadde + b_kalip", "birim": "EUR/adet",
               "ondalik": 4, "ozet": true, "yuzde_goster": false}
Sayı alanları "kod" ile formüllerde değişken olur; "yuzde": true olan alana kullanıcı 5 yazar, formülde 0.05 olarak girer.
Formüller yalnız + - * / ( ), sayılar, alan kodları ve min / max / round / abs / karekok / ilk(...) içerebilir (ast ile denetlenir,
eval kullanılmaz). Boş sayı alanı 0 sayılır (Excel gibi); sıfıra bölme sonucu boş (—) olur ve bağlı alanlara yayılır.
Ekranda aynı formüller JavaScript ile anında hesaplanır; kayıtta sunucu değerleri yeniden hesaplar (istemciye güvenilmez).
"""
import ast
import math
import operator
import re

FONKSIYONLAR = {
    "min": min, "max": max, "abs": abs, "karekok": math.sqrt,          # karekok(negatif) → boş
    "round": lambda x, n=0: round(x, int(n)),
    "ilk": lambda *a: next((x for x in a if x not in (None, 0)), 0),   # ilk dolu (sıfırdan farklı) değer
}
_OP = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.USub: operator.neg, ast.UAdd: operator.pos}
KOD_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class FormulHatasi(ValueError):
    pass


def _dogrula(node, adlar):
    if isinstance(node, ast.Expression):
        return _dogrula(node.body, adlar)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return
    if isinstance(node, ast.Name):
        if node.id not in adlar:
            raise FormulHatasi(f"bilinmeyen alan kodu: {node.id}")
        return
    if isinstance(node, ast.BinOp) and type(node.op) in _OP:
        _dogrula(node.left, adlar); _dogrula(node.right, adlar); return
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OP:
        _dogrula(node.operand, adlar); return
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FONKSIYONLAR and not node.keywords:
        for a in node.args:
            _dogrula(a, adlar)
        return
    raise FormulHatasi(f"izin verilmeyen ifade: {ast.dump(node)[:60]}")


def formul_dogrula(formul, adlar):
    """Formül geçerliyse None, değilse hata metni."""
    try:
        agac = ast.parse(str(formul or ""), mode="eval")
        _dogrula(agac, set(adlar))
        return None
    except (SyntaxError, FormulHatasi) as exc:
        return str(exc)


def _hesap(node, d):
    if isinstance(node, ast.Expression):
        return _hesap(node.body, d)
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return d.get(node.id)
    if isinstance(node, ast.UnaryOp):
        v = _hesap(node.operand, d)
        return None if v is None else _OP[type(node.op)](v)
    if isinstance(node, ast.BinOp):
        a, b = _hesap(node.left, d), _hesap(node.right, d)
        if a is None or b is None:
            return None
        if isinstance(node.op, ast.Div) and b == 0:
            return None
        return _OP[type(node.op)](a, b)
    if isinstance(node, ast.Call):
        args = [_hesap(a, d) for a in node.args]
        if node.func.id != "ilk" and any(a is None for a in args):
            return None
        return FONKSIYONLAR[node.func.id](*args)
    raise FormulHatasi("desteklenmeyen ifade")


def _sayi(v):
    if v in (None, ""):
        return 0.0
    try:
        return float(str(v).replace(" ", "").replace(",", "."))
    except ValueError:
        return 0.0


def hesap_alanlari_var(alanlar):
    return any(a.get("tip") == "hesap" or (a.get("tip") == "tablo" and (a.get("hesap_sutunlar") or a.get("toplamlar"))) for a in alanlar)


_SUTUN_RE = re.compile(r"\[([^\]]+)\]")


def sutun_formulu(formul, sutunlar):
    """'[Miktar] * [Birim Fiyat]' → 'c2 * c4' (sütun sırasına göre değişken; min/max/abs/round/karekok kullanılabilir). Bilinmeyen sütun FormulHatasi."""
    def cevir(m):
        ad = m.group(1).strip()
        if ad not in sutunlar:
            raise FormulHatasi(f"tabloda '{ad}' sütunu yok")
        return f"c{sutunlar.index(ad)}"
    return _SUTUN_RE.sub(cevir, str(formul or ""))


def _tablo_hesapla(a, veri, d):
    """Tablo satırlarında hesaplanan sütunları doldurur; 'toplamlar' sütun toplamlarını d[kod]'a yazar."""
    sut = a.get("sutunlar") or []
    satirlar = veri.get(a["ad"]) if isinstance(veri.get(a["ad"]), list) else []
    hs = {}
    for kol, f in (a.get("hesap_sutunlar") or {}).items():
        try:
            hs[kol] = ast.parse(sutun_formulu(f, sut), mode="eval")
        except (SyntaxError, FormulHatasi):
            hs[kol] = None
    ondalik = int(a.get("ondalik", 4))
    for r in satirlar:
        if not isinstance(r, dict):
            continue
        dd = {f"c{i}": _sayi(r.get(s)) for i, s in enumerate(sut)}
        for kol, ag in hs.items():
            try:
                v = _hesap(ag, dd) if ag is not None else None
            except (FormulHatasi, OverflowError, ValueError, TypeError, ZeroDivisionError):
                v = None
            r[kol] = "" if v is None else round(v, ondalik)
            dd[f"c{sut.index(kol)}"] = v or 0.0
    for kol, kod in (a.get("toplamlar") or {}).items():
        d[kod] = sum(_sayi(r.get(kol)) for r in satirlar if isinstance(r, dict))


def hesapla(alanlar, veri):
    """veri (alan adı → değer) üzerinde hesap alanlarını doldurur. Dönüş: {kod: değer} (hesap alanları dahil)."""
    d = {}
    for a in alanlar:
        if a.get("tip") == "tablo" and (a.get("hesap_sutunlar") or a.get("toplamlar")):
            _tablo_hesapla(a, veri, d)
    for a in alanlar:
        if a.get("kod") and a.get("tip") == "sayi":
            v = _sayi(veri.get(a["ad"]))
            d[a["kod"]] = v / 100.0 if a.get("yuzde") else v
    hesaplar = [a for a in alanlar if a.get("tip") == "hesap" and a.get("kod")]
    agaclar = {}
    for a in hesaplar:
        try:
            agaclar[a["kod"]] = ast.parse(str(a.get("formul") or "0"), mode="eval")
        except SyntaxError:
            agaclar[a["kod"]] = None
        d.setdefault(a["kod"], None)
    for _ in range(len(hesaplar) + 1):          # bağımlılık sırasından bağımsız: sabitlenene kadar tekrarla
        degisti = False
        for a in hesaplar:
            ag = agaclar[a["kod"]]
            try:
                v = _hesap(ag, d) if ag is not None else None
            except (FormulHatasi, OverflowError, ValueError, TypeError, ZeroDivisionError):
                v = None
            if v is not None and (math.isnan(v) or math.isinf(v)):
                v = None
            if v != d.get(a["kod"]):
                d[a["kod"]] = v; degisti = True
        if not degisti:
            break
    for a in hesaplar:
        v = d.get(a["kod"])
        veri[a["ad"]] = None if v is None else round(v * (100 if a.get("yuzde_goster") else 1), int(a.get("ondalik", 4)))
    return d


def tanim_dogrula(alanlar):
    """Form tanımı kaydedilirken: kodlar benzersiz ve geçerli, formüller yalnız sayı / hesap alanlarına başvuruyor."""
    hatalar, kodlar = [], []
    for a in alanlar:
        if a.get("tip") == "tablo":
            sut = a.get("sutunlar") or []
            for kol, f in (a.get("hesap_sutunlar") or {}).items():
                if kol not in sut:
                    hatalar.append(f"'{a.get('ad')}': hesap sütunu '{kol}' tabloda yok")
                    continue
                try:
                    h = formul_dogrula(sutun_formulu(f, sut), [f"c{i}" for i in range(len(sut))])
                except FormulHatasi as exc:
                    h = str(exc)
                if h:
                    hatalar.append(f"'{a.get('ad')}' › {kol} formülü: {h}")
            for kol, kod in (a.get("toplamlar") or {}).items():
                if kol not in sut:
                    hatalar.append(f"'{a.get('ad')}': toplam sütunu '{kol}' tabloda yok")
                elif not KOD_RE.match(str(kod)) or kod in kodlar:
                    hatalar.append(f"'{a.get('ad')}': toplam kodu geçersiz ya da tekrar ediyor ({kod})")
                else:
                    kodlar.append(kod)
        k = a.get("kod")
        if k:
            if not KOD_RE.match(k):
                hatalar.append(f"'{a.get('ad')}': kod yalnız küçük harf, rakam ve _ içermeli ({k})")
            elif k in kodlar:
                hatalar.append(f"kod tekrar ediyor: {k}")
            elif a.get("tip") in ("sayi", "hesap"):
                kodlar.append(k)
        if a.get("tip") == "hesap" and not k:
            hatalar.append(f"'{a.get('ad')}': hesap alanının kodu olmalı")
    for a in alanlar:
        if a.get("tip") == "hesap":
            h = formul_dogrula(a.get("formul"), kodlar)
            if h:
                hatalar.append(f"'{a.get('ad')}' formülü: {h}")
    return hatalar
