"""
DYS — Hafif Yerelleştirme (i18n)
================================
Flask-Babel yerine, çalışma zamanında derleme gerektirmeyen sözlük tabanlı
bir çeviri katmanı. Kaynak dil Türkçe'dir; İngilizce çeviriler aşağıdadır.
Veritabanında saklanan enum değerleri Türkçe kalır; yalnızca görüntüleme
katmanında çevrilir (geriye dönük uyumluluk).

Kullanım:
    from translations import _, translate_enum, slug
    _("Kaydet")            → locale 'en' ise "Save"
    translate_enum("Onaylı") → "Approved"
    slug("İncelemede")     → "incelemede"  (CSS sınıfı için güvenli ASCII)
"""

from flask import session, has_request_context

DEFAULT_LOCALE = "tr"


def get_locale():
    if has_request_context():
        return session.get("locale", DEFAULT_LOCALE)
    return DEFAULT_LOCALE


# ── ASCII Slug Haritası (CSS durum sınıfları için güvenli) ──────────────────
# Türkçe karakter dönüşümündeki kırılganlığı ortadan kaldırır.
SLUGS = {
    # Doküman durumları
    "Taslak": "taslak",
    "İncelemede": "incelemede",
    "Onaylı": "onayli",
    "İptal": "iptal",
    "Eskimiş": "eskimis",
    # Onay durumları
    "Bekliyor": "bekliyor",
    "Onaylandı": "onaylandi",
    "Reddedildi": "reddedildi",
    # Güvenlik
    "Gizli": "gizli",
    "Hizmete Özel": "hizmete-ozel",
    "Genel": "genel",
    # PPAP
    "Hazırlanıyor": "hazirlaniyor",
    "Koşullu Onay": "kosulluonay",
    "Hazırlanmadı": "hazirlanmadi",
    "Tamamlandı": "tamamlandi",
    "Uygulanamaz": "uygulanamaz",
    # CAPA / risk / audit
    "Açık": "acik",
    "Devam Ediyor": "devam-ediyor",
    "Etkinlik Kontrolünde": "etkinlik-kontrolunde",
    "Kapatıldı": "kapatildi",
    "Planlandı": "planlandi",
    "Aksiyon Planlandı": "aksiyon-planlandi",
    "Yüksek": "yuksek",
    "Orta": "orta",
    "Düşük": "dusuk",
    # FMEA Action Priority (VDA/AIAG 2019)
    "H": "ap-high",
    "M": "ap-medium",
    "L": "ap-low",
}


def slug(value):
    """Bir enum değerini güvenli ASCII CSS sınıfına çevirir."""
    if value in SLUGS:
        return SLUGS[value]
    # Bilinmeyen değerler için genel dönüşüm
    tr = str.maketrans("İıŞşĞğÜüÖöÇç ", "iisSgGuUoOcC-")
    return value.translate(tr).lower() if value else ""


# ── Enum Etiket Çevirileri (görüntüleme katmanı) ────────────────────────────
ENUM_EN = {
    # Roller
    "Admin": "Admin",
    "Doküman Kontrol": "Document Control",
    "Kullanıcı": "User",
    "Sadece Görüntüleme": "View Only",
    # Doküman durumları
    "Taslak": "Draft",
    "İncelemede": "In Review",
    "Onaylı": "Approved",
    "İptal": "Cancelled",
    "Eskimiş": "Obsolete",
    # Onay durumları
    "Bekliyor": "Pending",
    "Onaylandı": "Approved",
    "Reddedildi": "Rejected",
    # Onay adımları
    "Hazırlama": "Preparation",
    "Kontrol": "Review",
    "Onay": "Approval",
    # Doküman tipleri
    "Politika": "Policy",
    "El Kitabı": "Manual",
    "Prosedür": "Procedure",
    "Talimat": "Instruction",
    "Plan": "Plan",
    "Spesifikasyon": "Specification",
    "Form": "Form",
    "Liste": "List",
    "Dış Kaynaklı Doküman": "External Document",
    # Güvenlik
    "Gizli": "Confidential",
    "Hizmete Özel": "Internal Use",
    "Genel": "Public",
    # Süreç kategorileri
    "Destek": "Support",
    "Ana": "Core",
    "Yönetim": "Management",
    # PPAP
    "Hazırlanıyor": "In Preparation",
    "Koşullu Onay": "Conditional Approval",
    "Hazırlanmadı": "Not Started",
    "Tamamlandı": "Completed",
    "Uygulanamaz": "Not Applicable",
    # CAPA / audit / risk
    "Açık": "Open",
    "Devam Ediyor": "In Progress",
    "Etkinlik Kontrolünde": "Effectiveness Check",
    "Kapatıldı": "Closed",
    "Planlandı": "Planned",
    "Aksiyon Planlandı": "Action Planned",
    "İç Tetkik": "Internal Audit",
    "Müşteri Şikayeti": "Customer Complaint",
    "Denetim": "Audit",
    "Sistem Denetimi": "System Audit",
    "Proses Denetimi": "Process Audit",
    "Ürün Denetimi": "Product Audit",
    "Uygunsuzluk": "Nonconformity",
    "Öneri": "Suggestion",
    "Diğer": "Other",
    "Uygunsuzluk (Majör)": "Nonconformity (Major)",
    "Uygunsuzluk (Minör)": "Nonconformity (Minor)",
    "Gözlem": "Observation",
    "İyileştirme Fırsatı": "Opportunity for Improvement",
    "Olumlu": "Strength",
    "Oryantasyon": "Orientation",
    "İSG": "OH&S",
    "Kalite": "Quality",
    "Çevre": "Environment",
    "Teknik": "Technical",
    "Bilgi Güvenliği": "Information Security",
    "Yüksek": "High",
    "Orta": "Medium",
    "Düşük": "Low",
    "Editöryal": "Editorial",
    "İçerik": "Content",
    "Kritik": "Critical",
    "Mühendislik": "Engineering",
    "Müşteri Temsilcisi": "Customer Representative",
}


def translate_enum(value):
    """Veritabanı enum değerini görüntüleme için çevirir (locale 'en')."""
    if value is None:
        return ""
    if get_locale() == "en":
        return ENUM_EN.get(value, value)
    return value


# ── Arayüz Metinleri ────────────────────────────────────────────────────────
UI_EN = {
    # Navigasyon
    "Panel": "Dashboard",
    "Dokümanlar": "Documents",
    "Süreçler": "Processes",
    "Onaylar": "Approvals",
    "Dağıtım": "Distribution",
    "Raporlar": "Reports",
    "Erişim Kayıtları": "Audit Logs",
    "Kullanıcı Yönetimi": "User Management",
    "DÖF": "CAPA",
    "İç Tetkik": "Internal Audits",
    "Eğitimler": "Training",
    "Risk Kaydı": "Risk Register",
    "Dağıtım Grupları": "Distribution Groups",
    "Çıkış": "Logout",
    "Çıkış Yap": "Log Out",
    "Giriş Yap": "Log In",
    "Ana Menü": "Main Menu",
    "İş Akışı": "Workflow",
    "Kalite Sistemi": "Quality System",
    "Yönetim": "Administration",
    # Yeni modül gezinme etiketleri (Faz 4-9)
    "IATF 16949 Otomotiv": "IATF 16949 Automotive",
    "APQP": "APQP",
    "FMEA": "FMEA",
    "Kontrol Planı": "Control Plan",
    "Kalibrasyon": "Calibration",
    "Uygun Olmayan Ürün": "Nonconforming Product",
    "Tedarikçiler": "Suppliers",
    "Entegre Yönetim (IMS)": "Integrated Management (IMS)",
    "IMS Genel Bakış": "IMS Overview",
    "Uyum Matrisi": "Compliance Matrix",
    "Bağlam & Taraflar": "Context & Parties",
    "Hedefler": "Objectives",
    "Mevzuat & Uygunluk": "Legal & Compliance",
    "Yönetim Gözden Geçirme": "Management Review",
    "ISO 14001 Çevre": "ISO 14001 Environment",
    "Çevre Boyutları": "Environmental Aspects",
    "Çevresel Ölçüm": "Environmental Monitoring",
    "Çevre Olayları": "Environmental Incidents",
    "ISO 45001 İSG": "ISO 45001 OH&S",
    "Tehlike & Risk": "Hazard & Risk",
    "İSG Olayları": "OH&S Incidents",
    "Çalışan Katılımı": "Worker Participation",
    "ISO 27001 ISMS": "ISO 27001 ISMS",
    "ISMS Genel Bakış": "ISMS Overview",
    "Bilgi Varlıkları": "Information Assets",
    "SoA": "SoA",
    "ISMS Riskleri": "ISMS Risks",
    "Güvenlik Olayları": "Security Incidents",
    "Erişim İncelemesi": "Access Review",
    "Yetkinlik Matrisi": "Competency Matrix",
    "İmha Talepleri": "Disposal Requests",
    "Audit Bütünlük": "Audit Integrity",
    "Tetkik Programı": "Audit Program",
    "SPC": "SPC",
    "CSR": "CSR",
    "KKD": "PPE",
    "Acil Durum Tatbikatı": "Emergency Drill",
    "Yedekleme Kanıtı": "Backup Evidence",
    "Denetim Paketi": "Audit Package",
    "Giriş": "Login",
    "Doküman Yönetim Sistemi": "Document Management System",
    "ISO uyumlu doküman kontrol sistemi": "ISO-compliant document control system",
    "Temel Bilgiler": "Basic Information",
    "Doküman Tipi": "Document Type",
    "Doküman Seviyesi": "Document Level",
    "Doküman Başlığı": "Document Title",
    "Müşteri Özel Şartları": "Customer Specific Requirements",
    "Adımlar": "Steps",
    "Menü": "Menu",
    "Ara...": "Search...",
    "Bana Atanan Görevler": "My Assigned Tasks",
    "Bekleyen Onaylarım": "My Pending Approvals",
    "Açık DÖF": "Open CAPA",
    "Okunmamış Dağıtım": "Unread Distributions",
    "Süreç Haritası": "Process Map",
    "PPAP Yönetimi": "PPAP Management",
    "Doküman Yönetimi": "Document Management",
    "Ana Sayfa": "Home",
    "İçeriğe geç": "Skip to content",
    "Dil": "Language",
    "Tema Değiştir": "Toggle Theme",
    # Ortak eylemler
    "Kaydet": "Save",
    "İptal": "Cancel",
    "Sil": "Delete",
    "Düzenle": "Edit",
    "Yeni": "New",
    "Ara": "Search",
    "Filtrele": "Filter",
    "Temizle": "Clear",
    "Detay": "Details",
    "Görüntüle": "View",
    "İndir": "Download",
    "Önizle": "Preview",
    "Onayla": "Approve",
    "Reddet": "Reject",
    "Kapat": "Close",
    "Ekle": "Add",
    "Gönder": "Submit",
    "Dışa Aktar": "Export",
    "Doküman ara...": "Search documents...",
    # Alan etiketleri
    "Doküman No": "Document No",
    "Başlık": "Title",
    "Dizin": "Directory",
    "Durum": "Status",
    "Tip": "Type",
    "Süreç": "Process",
    "Güvenlik": "Security",
    "Revizyon": "Revision",
    "Hazırlayan": "Prepared By",
    "Kontrol Eden": "Reviewed By",
    "Onaylayan": "Approved By",
    "Tarih": "Date",
    "Açıklama": "Description",
    "Sorumlu": "Responsible",
    "Kategori": "Category",
    "Ad Soyad": "Full Name",
    "E-posta": "Email",
    "Şifre": "Password",
    "Departman": "Department",
    "Ünvan": "Title",
    "Rol": "Role",
    # Sayfa başlıkları / listeler
    "Doküman Listesi": "Document List",
    "Toplam": "Total",
    "doküman": "documents",
    "Yeni Doküman": "New Document",
    "Yeni Doküman Ekle": "Add New Document",
    "Doküman bulunamadı": "No documents found",
    "Arama kriterlerine uygun doküman yok veya henüz doküman eklenmemiş.":
        "No documents match your search criteria, or none have been added yet.",
    "Tümü": "All",
    "Seviye": "Level",
    "Rev.": "Rev.",
    "Yürürlük": "Effective",
    "Değişiklik Açıklaması": "Change Description",
    # Dashboard
    "Genel Bakış": "Overview",
    "Toplam Doküman": "Total Documents",
    "Onay Bekleyen": "Pending Approval",
    "Gecikmiş": "Overdue",
    "Yaklaşan Gözden Geçirmeler": "Upcoming Reviews",
    "60 gün içinde": "Within 60 days",
    "Açık DÖF": "Open CAPA",
    "Açık Riskler": "Open Risks",
    "Planlı Tetkikler": "Planned Audits",
    "Son Eklenen Dokümanlar": "Recently Added Documents",
    "Bekleyen Onaylarım": "My Pending Approvals",
    "Hızlı Erişim": "Quick Access",
    "Kayıt bulunamadı": "No records found",
    "Bu sistem IATF 16949, ISO 14001, ISO 45001 ve ISO 27001 doküman kontrolü (Madde 7.5) gerekliliklerini karşılamaktadır.":
        "This system meets the document control requirements (Clause 7.5) of IATF 16949, ISO 14001, ISO 45001 and ISO 27001.",
    "Onaylı Doküman": "Approved Documents",
    "Gözden Geçirme Yaklaşan": "Reviews Due Soon",
    "Gecikmiş Gözden Geçirme": "Overdue Reviews",
    "Aktif Süreç": "Active Processes",
    "Doküman Durumu Dağılımı": "Document Status Distribution",
    "Standart Bazında Dağılım": "Distribution by Standard",
    "Süreç Bazında Doküman Sayıları": "Document Counts by Process",
    "Tümünü Gör": "View All",
    "Henüz doküman eklenmemiş.": "No documents added yet.",
    "İlk Dokümanı Ekle": "Add First Document",
    "Onay Bekleyen Dokümanlar": "Documents Awaiting Approval",
    "Onay Adımı": "Approval Step",
    "İncele": "Review",
    "Gözden Geçirme Tarihi Yaklaşan Dokümanlar": "Documents With Upcoming Review Date",
    "Gözden Geçirme Tarihi": "Review Date",
    "Kalan Gün": "Days Remaining",
    "gün": "days",
    # Onaylar
    "Onay Bekleyenler": "Awaiting Approval",
    "Tümünü Seç": "Select All",
    "Seçilenleri Onayla": "Approve Selected",
    "Onay bekleyen doküman yok": "No documents awaiting approval",
    "Adım": "Step",
    "İşlem": "Action",
    "Onay bekleyen dokümanlar ve onay geçmişi": "Documents awaiting approval and approval history",
    "Bekleyenler": "Pending",
    "Geçmiş": "History",
    "Dokümanı Reddet": "Reject Document",
    "Red Sebebi": "Rejection Reason",
    "Red sebebini açıklayınız...": "Please explain the reason for rejection...",
    "Tüm dokümanlar işleme alınmıştır.": "All documents have been processed.",
    "Kişi": "Person",
    "Sonuç": "Result",
    "Henüz onay geçmişi bulunmamaktadır.": "No approval history yet.",
    "Lütfen en az bir onay seçin.": "Please select at least one approval.",
    # Raporlar
    "Standart Uyumluluk Matrisi": "Standard Compliance Matrix",
    "Doküman Envanteri": "Document Inventory",
    "Gözden Geçirme Takvimi": "Review Calendar",
    "Eskimiş Dokümanlar": "Obsolete Documents",
    "Geri": "Back",
    "Standart uyumluluk, doküman envanteri ve analiz raporları":
        "Standard compliance, document inventory and analysis reports",
    "Tüm standartların doküman gerekliliklerini ve mevcut durumlarını gösterir.":
        "Shows document requirements and current status for all standards.",
    "Süreç bazında tüm dokümanların detaylı listesi ve istatistikleri.":
        "Detailed list and statistics of all documents by process.",
    "Yaklaşan ve geçmiş gözden geçirme tarihleri ve planlama.":
        "Upcoming and past review dates and planning.",
    "İptal edilen ve eskimiş dokümanların kontrolü.":
        "Control of cancelled and obsolete documents.",
    "Onaylı": "Approved",
    "Taslak": "Draft",
    "Eskimiş/İptal": "Obsolete/Cancelled",
    "Standart × Süreç Uyumluluk Matrisi": "Standard × Process Compliance Matrix",
    "Doküman Sayısı": "Document Count",
    "Süreç Bazında Doküman Tipi Dağılımı": "Document Type Distribution by Process",
    "Diğer": "Other",
}


def _(text):
    """Arayüz metnini çevirir; çeviri yoksa kaynağı (Türkçe) döndürür."""
    if get_locale() == "en":
        return UI_EN.get(text, text)
    return text
