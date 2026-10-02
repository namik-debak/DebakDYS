"""DÖF kök neden analizi — yöntem bazlı form/serileştirme yardımcıları."""

from __future__ import annotations

import json

ISHIKAWA_KEYS = (
    ("insan", "İnsan (Man)"),
    ("makine", "Makine (Machine)"),
    ("malzeme", "Malzeme (Material)"),
    ("yontem", "Yöntem (Method)"),
    ("olcum", "Ölçüm (Measurement)"),
    ("cevre", "Çevre (Environment)"),
)

A3_KEYS = (
    ("background", "Arka Plan"),
    ("current", "Mevcut Durum"),
    ("target", "Hedef"),
    ("analysis", "Kök Neden Analizi"),
    ("countermeasures", "Karşı Önlemler"),
    ("followup", "Takip / Doğrulama"),
)


def _strip(val):
    return (val or "").strip()


def parse_stored_kok_neden(raw):
    """kok_neden alanından yapılandırılmış dict veya düz metin döner."""
    if not raw:
        return {"kind": "empty"}
    text = raw.strip()
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("v") == 1:
                return data
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return {"kind": "plain", "text": text}


def build_kok_neden_from_form(form, yontem):
    """Form alanlarından yöntem bazlı kök neden JSON/metin üretir."""
    yontem = (yontem or "").strip()
    if not yontem:
        return None

    if yontem == "5 Neden":
        problem = _strip(form.get("five_why_problem"))
        whys = [_strip(form.get(f"five_why_{i}")) for i in range(1, 6)]
        if not problem and not any(whys):
            return None
        return json.dumps({
            "v": 1,
            "method": yontem,
            "problem": problem,
            "whys": whys,
        }, ensure_ascii=False)

    if yontem == "Ishikawa (Balık Kılçığı)":
        cats = {key: _strip(form.get(f"ishikawa_{key}")) for key, _label in ISHIKAWA_KEYS}
        if not any(cats.values()):
            return None
        return json.dumps({
            "v": 1,
            "method": yontem,
            "categories": cats,
        }, ensure_ascii=False)

    if yontem == "A3":
        fields = {key: _strip(form.get(f"a3_{key}")) for key, _label in A3_KEYS}
        if not any(fields.values()):
            return None
        return json.dumps({
            "v": 1,
            "method": yontem,
            **fields,
        }, ensure_ascii=False)

    if yontem == "8D":
        # Özet kök neden D4'ten gelir; yapılandırılmış adımlar ayrı kolonlarda
        d4 = _strip(form.get("d4_root_cause"))
        return d4 or None

    # Diğer / bilinmeyen
    text = _strip(form.get("kok_neden"))
    if not text:
        return None
    return json.dumps({
        "v": 1,
        "method": yontem or "Diğer",
        "text": text,
    }, ensure_ascii=False)


def kok_neden_form_context(raw, yontem=None):
    """Şablon için önceden doldurulmuş alan sözlüğü."""
    data = parse_stored_kok_neden(raw)
    ctx = {
        "five_why_problem": "",
        "five_whys": ["", "", "", "", ""],
        "ishikawa": {k: "" for k, _ in ISHIKAWA_KEYS},
        "a3": {k: "" for k, _ in A3_KEYS},
        "plain": "",
    }
    if data.get("kind") == "empty":
        return ctx
    if data.get("kind") == "plain":
        ctx["plain"] = data.get("text") or ""
        return ctx

    method = data.get("method") or yontem
    if method == "5 Neden":
        ctx["five_why_problem"] = data.get("problem") or ""
        whys = data.get("whys") or []
        ctx["five_whys"] = [(whys[i] if i < len(whys) else "") for i in range(5)]
    elif method == "Ishikawa (Balık Kılçığı)":
        cats = data.get("categories") or {}
        ctx["ishikawa"] = {k: cats.get(k, "") for k, _ in ISHIKAWA_KEYS}
    elif method == "A3":
        ctx["a3"] = {k: data.get(k, "") for k, _ in A3_KEYS}
    else:
        ctx["plain"] = data.get("text") or ""
    return ctx


def format_kok_neden_blocks(raw, yontem=None):
    """Detay sayfası için (başlık, içerik) listesi."""
    data = parse_stored_kok_neden(raw)
    if data.get("kind") == "empty":
        return []
    if data.get("kind") == "plain":
        return [("Kök Neden", data.get("text") or "—")]

    method = data.get("method") or yontem
    if method == "5 Neden":
        blocks = []
        if data.get("problem"):
            blocks.append(("Problem", data["problem"]))
        for i, why in enumerate(data.get("whys") or [], 1):
            if why:
                blocks.append((f"{i}. Neden (Neden?)", why))
        return blocks or [("Kök Neden", "—")]

    if method == "Ishikawa (Balık Kılçığı)":
        cats = data.get("categories") or {}
        blocks = []
        for key, label in ISHIKAWA_KEYS:
            val = cats.get(key)
            if val:
                blocks.append((label, val))
        return blocks or [("Ishikawa", "—")]

    if method == "A3":
        blocks = []
        for key, label in A3_KEYS:
            val = data.get(key)
            if val:
                blocks.append((label, val))
        return blocks or [("A3", "—")]

    return [("Kök Neden", data.get("text") or "—")]
