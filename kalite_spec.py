"""
DYS — Kalite: Tedarikçi Uygunsuzluk Raporu (SCAR, D02 F11) ve Müşteri Şikayeti / 8D (Y01.7 F03) alan tanımları (2026)
Aynı tanım form ekranını, listeyi ve A4 PDF raporunu üretir; her başlık Türkçe + İngilizce.
Alan: (anahtar, TR, EN, tip, seçenekler / sütunlar, genişlik)   tip: metin · uzun · tarih · sayi · secim · kullanici · tedarikci · musteri · evet · tablo
Kolon olarak tutulanlar KOLON_* kümelerinde; diğerleri kaydın veri_json alanında.
"""

HATA_TURU = [("Ölçüsel", "Dimensional"), ("Görsel / yüzey", "Visual / surface"), ("Malzeme", "Material"), ("Fonksiyonel", "Functional"),
             ("Montaj", "Assembly"), ("Ambalaj / etiket", "Packaging / labelling"), ("Doküman / sertifika", "Documentation / certificate"),
             ("Karışık parça", "Mixed parts"), ("Miktar", "Quantity"), ("Diğer", "Other")]
ONEM = [("Kritik", "Critical"), ("Major", "Major"), ("Minor", "Minor")]
EVET_HAYIR = [("Evet", "Yes"), ("Hayır", "No")]
ETIKET = [("Hatalı (NOK)", "Defective (NOK)"), ("Referans (OK)", "Reference (OK)"), ("Etiket", "Label"), ("Ambalaj", "Packaging"),
          ("Ölçüm", "Measurement"), ("Diğer", "Other")]

TU = {
 "kod": "D02 F11", "onek": "TU", "baslik": ("TEDARİKÇİ UYGUNSUZLUK RAPORU", "SUPPLIER NONCONFORMANCE REPORT (SCAR)"),
 "durumlar": ["Açık", "Tedarikçi yanıtı bekleniyor", "Değerlendirmede", "Etkinlik doğrulamada", "Kapatıldı", "İptal"],
 "bolumler": [
  ("Genel Bilgiler", "General Information", [
    ("no", "Rapor No", "Report No", "salt", None, 1), ("tarih", "Rapor Tarihi", "Report Date", "tarih", None, 1),
    ("tedarikci_id", "Tedarikçi", "Supplier", "tedarikci", None, 2), ("tedarikci_yetkili", "Tedarikçi Yetkilisi / E-posta", "Supplier Contact / E-mail", "metin", None, 2),
    ("urun_no", "Ürün No", "Part No", "metin", None, 1), ("urun_adi", "Ürün Adı", "Part Name", "metin", None, 2), ("revizyon", "Rev. / Resim No", "Rev. / Drawing No", "metin", None, 1),
    ("siparis_no", "Sipariş No", "Purchase Order No", "metin", None, 1), ("irsaliye_no", "İrsaliye No", "Delivery Note No", "metin", None, 1),
    ("fatura_no", "Fatura No", "Invoice No", "metin", None, 1), ("lot_no", "Lot / Parti No", "Lot / Batch No", "metin", None, 1),
    ("teslim_tarihi", "Teslim Tarihi", "Delivery Date", "tarih", None, 1),
    ("kaynak", "Tespit Yeri", "Detected at", "secim", [("Girdi kontrol", "Incoming inspection"), ("Üretim", "Production"), ("Final kontrol", "Final inspection"),
                                                       ("Müşteri şikayeti", "Customer complaint"), ("Denetim", "Audit")], 1),
    ("sorumlu_id", "Debak Sorumlusu", "Debak Responsible", "kullanici", None, 1)]),
  ("Uygunsuzluk", "Nonconformance", [
    ("hata_turu", "Hata Türü", "Defect Type", "secim", HATA_TURU, 1), ("onem", "Önem", "Severity", "secim", ONEM, 1),
    ("tekrar", "Tekrarlayan hata", "Repeated defect", "secim", EVET_HAYIR, 1),
    ("teslim_miktar", "Teslim Miktarı", "Delivered Qty", "sayi", None, 1), ("kontrol_miktar", "Kontrol Edilen", "Inspected Qty", "sayi", None, 1),
    ("hatali_miktar", "Hatalı Miktar", "Defective Qty", "sayi", None, 1),
    ("gereklilik", "İstenen (şartname / resim)", "Requirement (specification / drawing)", "uzun", None, 3),
    ("problem", "Tespit Edilen Uygunsuzluk", "Nonconformance Found", "uzun", None, 3)]),
  ("Karar ve Acil Önlem (Debak)", "Disposition and Containment (Debak)", [
    ("karar", "Karar", "Disposition", "secim", [("Red — tedarikçiye iade", "Reject — return to supplier"), ("Red — imha", "Reject — scrap"),
                                               ("Şartlı kabul — ayıklama", "Conditional — sorting"), ("Şartlı kabul — yeniden işlem", "Conditional — rework"),
                                               ("Özel kabul (sapma)", "Use as is (deviation)")], 2),
    ("koruma", "Acil Önlem (stok ayıklama, blokaj)", "Containment (stock sorting, blocking)", "uzun", None, 3),
    ("stok", "Stok Kontrolü", "Stock Check", "tablo", ["Yer / Location", "Miktar / Qty", "Kontrol / Checked", "Hatalı / NOK", "Tarih / Date"], 3),
    ("maliyet", "Maliyet", "Cost", "sayi", None, 1), ("para", "Para Birimi", "Currency", "secim", [("TL", "TRY"), ("EUR", "EUR"), ("USD", "USD")], 1),
    ("yansitma", "Maliyet tedarikçiye yansıtılır", "Cost charged to supplier", "secim", EVET_HAYIR, 1)]),
  ("Tedarikçiden İstenen Yanıt", "Required Supplier Response", [
    ("termin_4d", "Acil Önlem / 4D Termini", "Containment / 4D Due", "tarih", None, 1), ("termin_8d", "8D Termini", "8D Due", "tarih", None, 1),
    ("yanit_4d", "4D Alındı", "4D Received", "tarih", None, 1), ("yanit_8d", "8D Alındı", "8D Received", "tarih", None, 1),
    ("kok_neden", "Kök Neden (oluşma ve kaçma)", "Root Cause (occurrence and non-detection)", "uzun", None, 3),
    ("duzeltici", "Düzeltici Faaliyet", "Corrective Action", "uzun", None, 3), ("onleyici", "Önleyici Faaliyet / Yaygınlaştırma", "Preventive Action / Read-across", "uzun", None, 3)]),
  ("Doğrulama ve Kapanış", "Verification and Closure", [
    ("dogrulama", "Etkinlik Doğrulaması (sonraki sevkiyatlar)", "Effectiveness Verification (next deliveries)", "uzun", None, 3),
    ("dogrulama_tarihi", "Doğrulama Tarihi", "Verification Date", "tarih", None, 1), ("durum", "Durum", "Status", "durum", None, 1),
    ("kapanis_tarihi", "Kapanış Tarihi", "Closing Date", "tarih", None, 1), ("notlar", "Notlar", "Remarks", "uzun", None, 3)]),
 ],
}

MS = {
 "kod": "Y01.7 F03", "onek": "MS", "baslik": ("MÜŞTERİ ŞİKAYETİ — 8D RAPORU", "CUSTOMER COMPLAINT — 8D REPORT"),
 "durumlar": ["Açık", "Geçici önlem (D3)", "Kök neden analizi (D4)", "Aksiyonlar (D5–D6)", "Etkinlik doğrulamada (D7)", "Kapatıldı", "İptal"],
 "bolumler": [
  ("Şikayet Bilgileri", "Complaint Information", [
    ("no", "Debak Rapor No", "Debak Report No", "salt", None, 1), ("tarih", "Şikayet Tarihi", "Complaint Date", "tarih", None, 1),
    ("musteri", "Müşteri", "Customer", "musteri", None, 2), ("musteri_ref", "Müşteri Şikayet No", "Customer Claim No", "metin", None, 1),
    ("musteri_yetkili", "Müşteri Yetkilisi / E-posta", "Customer Contact / E-mail", "metin", None, 2),
    ("kanal", "Bildirim Şekli", "Notified via", "secim", [("E-posta", "E-mail"), ("Müşteri portalı", "Customer portal"), ("Telefon", "Phone"), ("Ziyaret", "Visit")], 1),
    ("urun_no", "Debak Ürün No", "Debak Part No", "metin", None, 1), ("musteri_urun_no", "Müşteri Ürün No", "Customer Part No", "metin", None, 1),
    ("urun_adi", "Ürün Adı", "Part Name", "metin", None, 2), ("sevk_no", "İrsaliye / Sevk No", "Delivery Note No", "metin", None, 1),
    ("lot_no", "Lot / Üretim Tarihi", "Lot / Production Date", "metin", None, 1),
    ("tespit_yeri", "Tespit Yeri", "Detected at", "secim", [("Müşteri girdi kontrol", "Customer incoming inspection"), ("Müşteri üretim hattı", "Customer line"),
                                                             ("Saha / son kullanıcı", "Field / end user"), ("Müşteri denetimi", "Customer audit")], 1),
    ("sorumlu_id", "Debak Sorumlusu", "Debak Responsible", "kullanici", None, 1)]),
  ("D1 Ekip", "D1 Team", [("ekip", "Ekip Üyeleri (ad — görev)", "Team Members (name — function)", "uzun", None, 3)]),
  ("D2 Problem Tanımı", "D2 Problem Description", [
    ("sikayet_turu", "Şikayet Türü", "Complaint Type", "secim", [("Kalite", "Quality"), ("Teslimat / lojistik", "Delivery / logistics"),
                                                                 ("Ambalaj / etiket", "Packaging / labelling"), ("Doküman", "Documentation"), ("Diğer", "Other")], 1),
    ("hata_turu", "Hata Türü", "Defect Type", "secim", HATA_TURU, 1), ("onem", "Önem", "Severity", "secim", ONEM, 1),
    ("tekrar", "Tekrarlayan şikayet", "Repeated complaint", "secim", EVET_HAYIR, 1),
    ("sevk_miktar", "Sevk Miktarı", "Delivered Qty", "sayi", None, 1), ("supheli_miktar", "Şüpheli Miktar", "Suspect Qty", "sayi", None, 1),
    ("hatali_miktar", "Hatalı Miktar", "Defective Qty", "sayi", None, 1),
    ("problem", "Problem (ne, nerede, ne zaman, ne kadar)", "Problem (what, where, when, how many)", "uzun", None, 3)]),
  ("D3 Geçici Önlemler", "D3 Containment Actions", [
    ("termin_d3", "D3 Termini", "D3 Due", "tarih", None, 1),
    ("koruma", "Geçici Önlemler (ayıklama, yedek sevk, temiz nokta)", "Containment (sorting, replacement, clean point)", "uzun", None, 3),
    ("ayiklama", "Stok Ayıklama Sonuçları", "Stock Sorting Results", "tablo", ["Yer / Location", "Kontrol / Checked", "Hatalı / NOK", "Tarih / Date", "Sorumlu / Responsible"], 3),
    ("temiz_nokta", "İlk Temiz Sevkiyat (tarih / irsaliye / işaret)", "First Clean Shipment (date / delivery note / marking)", "metin", None, 3)]),
  ("D4 Kök Neden", "D4 Root Cause", [
    ("kok_olusma", "Oluşma Nedeni (neden oluştu?)", "Occurrence Root Cause (why did it occur?)", "uzun", None, 3),
    ("kok_kacma", "Kaçma Nedeni (neden tespit edilmedi?)", "Non-detection Root Cause (why was it not detected?)", "uzun", None, 3),
    ("analiz", "Analiz Yöntemi", "Analysis Method", "secim", [("5 Neden", "5 Why"), ("Balık kılçığı", "Ishikawa"), ("Hata ağacı", "Fault tree"), ("Diğer", "Other")], 1)]),
  ("D5–D6 Düzeltici Faaliyetler", "D5–D6 Corrective Actions", [
    ("aksiyonlar", "Faaliyetler", "Actions", "tablo", ["Faaliyet / Action", "Tür / Type (O / D)", "Sorumlu / Responsible", "Termin / Due", "Gerçekleşme / Done"], 3)]),
  ("D7 Önleme (sistem)", "D7 Prevention (system)", [
    ("guncellenen", "Güncellenen Dokümanlar", "Updated Documents", "coklu", [("PFMEA", "PFMEA"), ("Kontrol planı", "Control plan"), ("Talimat", "Work instruction"),
                                                                           ("Muayene / test planı", "Inspection / test plan"), ("Eğitim", "Training"), ("Poka-yoke", "Poka-yoke")], 3),
    ("yayginlastirma", "Benzer Ürün / Proseslere Yaygınlaştırma", "Read-across to Similar Parts / Processes", "uzun", None, 3),
    ("dogrulama", "Etkinlik Doğrulaması", "Effectiveness Verification", "uzun", None, 3), ("dogrulama_tarihi", "Doğrulama Tarihi", "Verification Date", "tarih", None, 1)]),
  ("D8 Kapanış", "D8 Closure", [
    ("termin_8d", "8D Termini", "8D Due", "tarih", None, 1), ("durum", "Durum", "Status", "durum", None, 1),
    ("kapanis_tarihi", "Kapanış Tarihi", "Closing Date", "tarih", None, 1),
    ("musteri_kabul", "Müşteri Onayı", "Customer Acceptance", "secim", [("Bekliyor", "Pending"), ("Kabul", "Accepted"), ("Red", "Rejected")], 1),
    ("maliyet", "Maliyet", "Cost", "sayi", None, 1), ("para", "Para Birimi", "Currency", "secim", [("TL", "TRY"), ("EUR", "EUR"), ("USD", "USD")], 1),
    ("notlar", "Notlar / Ekip Takdiri", "Remarks / Team Recognition", "uzun", None, 3)]),
 ],
}

KOLON_TU = {"no", "tarih", "tedarikci_id", "urun_no", "urun_adi", "onem", "hatali_miktar", "termin_8d", "durum", "sorumlu_id", "kapanis_tarihi"}
KOLON_MS = {"no", "tarih", "musteri", "musteri_ref", "urun_no", "urun_adi", "onem", "hatali_miktar", "termin_d3", "termin_8d", "durum", "sorumlu_id", "kapanis_tarihi"}
SPEC = {"TU": TU, "MS": MS}
KOLON = {"TU": KOLON_TU, "MS": KOLON_MS}


def alanlar(tur):
    for b in SPEC[tur]["bolumler"]:
        for a in b[2]:
            yield a


def secenek_en(tur, anahtar, deger):
    """Seçim değerinin İngilizcesi (PDF'te 'Red — iade / Reject — return' için)."""
    for a in alanlar(tur):
        if a[0] == anahtar and a[4] and a[3] in ("secim", "coklu"):
            for tr, en in a[4]:
                if tr == deger:
                    return en
    return None
