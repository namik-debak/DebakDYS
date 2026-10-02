"""
DYS — Dinamik formlarda kısıtlı erişim (KVKK, 2026)
Kişisel veri içeren formlar (ör. D01 personel izin, fazla mesai, işe giriş / çıkış protokolü) "kısıtlı" işaretlenir.
Kısıtlı formun kayıtlarını yalnız
  · kaydı giren kişi,
  · formda yetkili olarak tanımlanan kullanıcılar (ör. İK) ve
  · Admin (sistem yöneticisi; erişimi işlem kaydına yazılır)
görür, onaylar, yazdırır ve dışa aktarır. Kısıtlı formlar ortak "Form Verileri" klasörüne ve toplu dosyaya yazılmaz.
Boş form (şablon, alan tanımı) herkese açıktır; kısıt yalnız doldurulmuş kayıtlar içindir.
"""
YONETICI_ROLLER = ("Admin", "Doküman Kontrol")


def yetkililer(t):
    try:
        return {int(x) for x in (t.erisim.get("kullanicilar") or [])}
    except (TypeError, ValueError):
        return set()


def kayit_gorebilir(t, k, uid, rol):
    if t is None or not t.kisitli:
        return True
    return rol == "Admin" or (k is not None and k.olusturan_id == uid) or uid in yetkililer(t)


def onaylayabilir(t, uid, rol):
    if t is not None and t.kisitli:
        return rol == "Admin" or uid in yetkililer(t)
    return rol in YONETICI_ROLLER


def gorunur(kayitlar, uid, rol):
    return [k for k in kayitlar if kayit_gorebilir(k.tanim, k, uid, rol)]
