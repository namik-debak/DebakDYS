"""
DYS — Demo Verileri (Seed Data)
================================
16 süreç, 3 demo kullanıcı ve örnek dokümanlar oluşturur.
"""

from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

from models import (
    SessionLocal, init_db,
    User, Process, Document, DocumentRevision, DocumentApproval, AuditLog,
    PPAPSubmission, PPAPElement, PPAP_ELEMENTLERI, QRQCItem, CorrectiveAction,
)


def seed_all():
    """Tüm demo verileri oluşturur."""
    init_db()
    db = SessionLocal()

    try:
        # ── 1) Kullanıcılar ─────────────────────────────────────────
        users_data = [
            {
                "ad_soyad": "Admin Kullanıcı",
                "eposta": "admin@dys.com",
                "sifre_hash": generate_password_hash("admin123"),
                "departman": "Bilgi Teknolojileri",
                "unvan": "Sistem Yöneticisi",
                "rol": "Admin",
            },
            {
                "ad_soyad": "Kalite Müdürü",
                "eposta": "kalite@dys.com",
                "sifre_hash": generate_password_hash("kalite123"),
                "departman": "Kalite",
                "unvan": "Kalite Müdürü",
                "rol": "Doküman Kontrol",
            },
            {
                "ad_soyad": "Dok. Kontrol Sorumlusu",
                "eposta": "dokuman@dys.com",
                "sifre_hash": generate_password_hash("dokuman123"),
                "departman": "Kalite",
                "unvan": "Doküman Kontrol Sorumlusu",
                "rol": "Doküman Kontrol",
            },
            {
                "ad_soyad": "Üretim Müdürü",
                "eposta": "uretim@dys.com",
                "sifre_hash": generate_password_hash("uretim123"),
                "departman": "Üretim",
                "unvan": "Üretim Müdürü",
                "rol": "Kullanıcı",
            },
            {
                "ad_soyad": "Çevre Mühendisi",
                "eposta": "cevre@dys.com",
                "sifre_hash": generate_password_hash("cevre123"),
                "departman": "Çevre",
                "unvan": "Çevre Mühendisi",
                "rol": "Kullanıcı",
            },
            {
                "ad_soyad": "İSG Uzmanı",
                "eposta": "isg@dys.com",
                "sifre_hash": generate_password_hash("isg123"),
                "departman": "İSG",
                "unvan": "İSG Uzmanı",
                "rol": "Kullanıcı",
            },
            {
                "ad_soyad": "BG Sorumlusu",
                "eposta": "bg@dys.com",
                "sifre_hash": generate_password_hash("bg123"),
                "departman": "Bilgi Güvenliği",
                "unvan": "Bilgi Güvenliği Sorumlusu",
                "rol": "Kullanıcı",
            },
        ]

        users = []
        if not db.query(User).first():
            for u_data in users_data:
                user = User(**u_data, aktif=True, olusturma_tarihi=datetime.now())
                db.add(user)
                users.append(user)
            db.flush()
        else:
            users = db.query(User).all()

        # ── 2) Süreçler ────────────────────────────────────────────
        processes_data = [
            # Destek Süreçleri
            {"kod": "D01", "ad": "İnsan Kaynakları", "kategori": "Destek", "ilgili_standartlar": "IATF 16949, ISO 45001"},
            {"kod": "D02", "ad": "Altyapı ve Çalışma Ortamı", "kategori": "Destek", "ilgili_standartlar": "IATF 16949, ISO 45001"},
            {"kod": "D03", "ad": "Bakım Onarım", "kategori": "Destek", "ilgili_standartlar": "IATF 16949"},
            {"kod": "D04", "ad": "Ölçme ve İzleme Ekipmanları Kontrolü", "kategori": "Destek", "ilgili_standartlar": "IATF 16949"},
            {"kod": "D05", "ad": "Satınalma", "kategori": "Destek", "ilgili_standartlar": "IATF 16949, ISO 14001"},
            {"kod": "D06", "ad": "Kalite Kontrol", "kategori": "Destek", "ilgili_standartlar": "IATF 16949"},
            {"kod": "D07", "ad": "Çevre Yönetimi", "kategori": "Destek", "ilgili_standartlar": "ISO 14001"},
            {"kod": "D08", "ad": "Bilgi Güvenliği Yönetimi", "kategori": "Destek", "ilgili_standartlar": "ISO 27001"},
            # Ana Süreçler
            {"kod": "M01", "ad": "Satış Projeleri Yönetimi", "kategori": "Ana", "ilgili_standartlar": "IATF 16949"},
            {"kod": "M02", "ad": "Yeni Ürün Devreye Alma", "kategori": "Ana", "ilgili_standartlar": "IATF 16949"},
            {"kod": "M03", "ad": "Üretim Planlama", "kategori": "Ana", "ilgili_standartlar": "IATF 16949"},
            {"kod": "M04", "ad": "Üretim Yönetimi", "kategori": "Ana", "ilgili_standartlar": "IATF 16949, ISO 14001, ISO 45001"},
            {"kod": "M05", "ad": "Sevkiyat Yönetimi", "kategori": "Ana", "ilgili_standartlar": "IATF 16949"},
            # Yönetim Süreçleri
            {"kod": "Y01", "ad": "Kalite Yönetim Prosesi", "kategori": "Yönetim", "ilgili_standartlar": "IATF 16949"},
            {"kod": "Y02", "ad": "Yönetim Sorumluluğu Prosesi", "kategori": "Yönetim", "ilgili_standartlar": "IATF 16949, ISO 14001, ISO 45001, ISO 27001"},
            {"kod": "Y03", "ad": "Sürekli İyileştirme Prosesi", "kategori": "Yönetim", "ilgili_standartlar": "IATF 16949, ISO 14001, ISO 45001, ISO 27001"},
        ]

        procs = {}
        if not db.query(Process).first():
            for p_data in processes_data:
                proc = Process(**p_data)
                db.add(proc)
                procs[p_data["kod"]] = proc
            db.flush()
        else:
            for p in db.query(Process).all():
                procs[p.kod] = p

        # ── 3) Örnek Dokümanlar ─────────────────────────────────────
        admin = users[0]
        kalite = users[1]
        dokuman_kontrol = users[2]

        docs_data = [
            # Seviye 1 — Politikalar
            {
                "dokuman_no": "Y01-PO-001", "baslik": "Kalite Politikası",
                "surec": "Y01", "dokuman_tipi": "Politika", "dokuman_seviyesi": 1,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 5.2",
            },
            {
                "dokuman_no": "D07-PO-001", "baslik": "Çevre Politikası",
                "surec": "D07", "dokuman_tipi": "Politika", "dokuman_seviyesi": 1,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "ISO 14001 - 5.2",
            },
            {
                "dokuman_no": "D01-PO-001", "baslik": "İş Sağlığı ve Güvenliği Politikası",
                "surec": "D01", "dokuman_tipi": "Politika", "dokuman_seviyesi": 1,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "ISO 45001 - 5.2",
            },
            {
                "dokuman_no": "D08-PO-001", "baslik": "Bilgi Güvenliği Politikası",
                "surec": "D08", "dokuman_tipi": "Politika", "dokuman_seviyesi": 1,
                "guvenlik_sinifi": "Hizmete Özel", "durum": "Onaylı",
                "ilgili_standartlar": "ISO 27001 - 5.2",
            },
            # Seviye 1 — El Kitapları
            {
                "dokuman_no": "Y01-EK-001", "baslik": "Kalite El Kitabı",
                "surec": "Y01", "dokuman_tipi": "El Kitabı", "dokuman_seviyesi": 1,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 4.4",
            },
            # Seviye 2 — Prosedürler
            {
                "dokuman_no": "Y01-PR-001", "baslik": "Doküman Kontrol Prosedürü",
                "surec": "Y01", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 7.5, ISO 14001 - 7.5, ISO 45001 - 7.5, ISO 27001 - 7.5",
            },
            {
                "dokuman_no": "Y01-PR-002", "baslik": "Kayıtların Kontrolü Prosedürü",
                "surec": "Y01", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 7.5.3",
            },
            {
                "dokuman_no": "Y03-PR-001", "baslik": "Düzeltici Faaliyet Prosedürü",
                "surec": "Y03", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 10.2",
            },
            {
                "dokuman_no": "Y03-PR-002", "baslik": "İç Tetkik Prosedürü",
                "surec": "Y03", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Hizmete Özel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 9.2, ISO 14001 - 9.2, ISO 45001 - 9.2, ISO 27001 - 9.2",
            },
            {
                "dokuman_no": "Y02-PR-001", "baslik": "Yönetimin Gözden Geçirmesi Prosedürü",
                "surec": "Y02", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Hizmete Özel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 9.3, ISO 14001 - 9.3, ISO 45001 - 9.3, ISO 27001 - 9.3",
            },
            {
                "dokuman_no": "D06-PR-001", "baslik": "Uygun Olmayan Ürün Kontrolü Prosedürü",
                "surec": "D06", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.7",
            },
            {
                "dokuman_no": "D05-PR-001", "baslik": "Satınalma Prosedürü",
                "surec": "D05", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.4",
            },
            {
                "dokuman_no": "D04-PR-001", "baslik": "Kalibrasyon Prosedürü",
                "surec": "D04", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 7.1.5",
            },
            {
                "dokuman_no": "D07-PR-001", "baslik": "Çevresel Boyutlar ve Etki Değerlendirme Prosedürü",
                "surec": "D07", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "ISO 14001 - 6.1.2",
            },
            {
                "dokuman_no": "D08-PR-001", "baslik": "Bilgi Güvenliği Risk Değerlendirme Prosedürü",
                "surec": "D08", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Gizli", "durum": "Onaylı",
                "ilgili_standartlar": "ISO 27001 - 6.1.2",
            },
            {
                "dokuman_no": "M02-PR-001", "baslik": "APQP Prosedürü",
                "surec": "M02", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Hizmete Özel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.3",
            },
            {
                "dokuman_no": "M04-PR-001", "baslik": "Üretim Kontrol Prosedürü",
                "surec": "M04", "dokuman_tipi": "Prosedür", "dokuman_seviyesi": 2,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.5",
            },
            # Seviye 3 — Talimatlar
            {
                "dokuman_no": "D06-TL-001", "baslik": "Giriş Kalite Kontrol Talimatı",
                "surec": "D06", "dokuman_tipi": "Talimat", "dokuman_seviyesi": 3,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.6",
            },
            {
                "dokuman_no": "M04-TL-001", "baslik": "Proses Kontrol Talimatı",
                "surec": "M04", "dokuman_tipi": "Talimat", "dokuman_seviyesi": 3,
                "guvenlik_sinifi": "Genel", "durum": "İncelemede",
                "ilgili_standartlar": "IATF 16949 - 8.5.1",
            },
            {
                "dokuman_no": "D03-TL-001", "baslik": "Koruyucu Bakım Talimatı",
                "surec": "D03", "dokuman_tipi": "Talimat", "dokuman_seviyesi": 3,
                "guvenlik_sinifi": "Genel", "durum": "Taslak",
                "ilgili_standartlar": "IATF 16949 - 8.5.1.6",
            },
            # Seviye 4 — Formlar
            {
                "dokuman_no": "Y01-FR-001", "baslik": "Doküman Değişiklik Talep Formu",
                "surec": "Y01", "dokuman_tipi": "Form", "dokuman_seviyesi": 4,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 7.5",
            },
            {
                "dokuman_no": "D06-FR-001", "baslik": "Uygunsuzluk Raporu Formu",
                "surec": "D06", "dokuman_tipi": "Form", "dokuman_seviyesi": 4,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.7, 10.2",
            },
            {
                "dokuman_no": "D04-FR-001", "baslik": "Kalibrasyon Kayıt Formu",
                "surec": "D04", "dokuman_tipi": "Form", "dokuman_seviyesi": 4,
                "guvenlik_sinifi": "Genel", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 7.1.5",
            },
            # Seviye 5 — Dış Kaynaklı
            {
                "dokuman_no": "D06-DK-001", "baslik": "Müşteri Spesifikasyonu - ABC-2024",
                "surec": "D06", "dokuman_tipi": "Dış Kaynaklı Doküman", "dokuman_seviyesi": 5,
                "guvenlik_sinifi": "Gizli", "durum": "Onaylı",
                "ilgili_standartlar": "IATF 16949 - 8.4.2.2",
            },
        ]

        if not db.query(Document).first():
            for d_data in docs_data:
                proc_kod = d_data.pop("surec")
                proc = procs.get(proc_kod)
                doc = Document(
                    **d_data,
                    surec_id=proc.id if proc else None,
                    hazirlayan_id=dokuman_kontrol.id,
                    kontrol_eden_id=kalite.id,
                    onaylayan_id=admin.id,
                    revizyon_no=0,
                    saklama_suresi_ay=36,
                    yururluk_tarihi=date.today() - timedelta(days=90) if d_data.get("durum") == "Onaylı" else None,
                    sonraki_gozden_gecirme=date.today() + timedelta(days=270) if d_data.get("durum") == "Onaylı" else None,
                    olusturma_tarihi=datetime.now() - timedelta(days=120),
                    guncelleme_tarihi=datetime.now() - timedelta(days=30),
                )
                db.add(doc)
                db.flush()

                # Create initial revision
                rev = DocumentRevision(
                    document_id=doc.id,
                    revizyon_no=0,
                    degisiklik_aciklamasi="İlk yayın",
                    hazirlayan_id=dokuman_kontrol.id,
                    tarih=datetime.now() - timedelta(days=120),
                )
                db.add(rev)

                # Create approved approval steps for approved docs
                if doc.durum == "Onaylı":
                    for adim, uid in [("Hazırlama", dokuman_kontrol.id), ("Kontrol", kalite.id), ("Onay", admin.id)]:
                        approval = DocumentApproval(
                            document_id=doc.id,
                            onay_adimi=adim,
                            kullanici_id=uid,
                            durum="Onaylandı",
                            tarih=datetime.now() - timedelta(days=100),
                        )
                        db.add(approval)
                elif doc.durum == "İncelemede":
                    for adim in ["Hazırlama", "Kontrol", "Onay"]:
                        approval = DocumentApproval(
                            document_id=doc.id,
                            onay_adimi=adim,
                            durum="Bekliyor",
                            tarih=datetime.now(),
                        )
                        db.add(approval)

        # Gözden geçirme tarihi yaklaşan dokümanları ayarla (demo amaçlı)
        docs_to_review = db.query(Document).filter_by(durum="Onaylı").limit(3).all()
        for i, doc in enumerate(docs_to_review):
            doc.sonraki_gozden_gecirme = date.today() + timedelta(days=(5 + i * 10))

        db.commit()
        print(f"[OK] {len(users_data)} kullanıcı oluşturuldu")
        # ── 5) PPAP Sunumları ──────────────────────────────────────────
        m02 = db.query(Process).filter_by(kod="M02").first()
        m02_id = m02.id if m02 else None
        kalite_user = db.query(User).filter_by(eposta="kalite@dys.com").first()
        kalite_id = kalite_user.id if kalite_user else 1

        ppap_data = [
            {
                "parca_no": "A95135-001",
                "parca_adi": "Moving Contact Shaft",
                "musteri": "Siemens AG",
                "sunum_seviyesi": 3,
                "durum": "Onaylandı",
                "revizyon_nedeni": "Yeni parça onayı",
                "sunum_tarihi": date.today() - timedelta(days=45),
                "onay_tarihi": date.today() - timedelta(days=10),
                "sorumlu_id": kalite_id,
                "surec_id": m02_id,
                # Element durumları: 1=Tamamlandı hepsi
                "element_durumlari": {
                    1: "Tamamlandı", 2: "Tamamlandı", 3: "Tamamlandı", 4: "Tamamlandı",
                    5: "Tamamlandı", 6: "Tamamlandı", 7: "Tamamlandı", 8: "Tamamlandı",
                    9: "Tamamlandı", 10: "Tamamlandı", 11: "Tamamlandı", 12: "Tamamlandı",
                    13: "Uygulanamaz", 14: "Tamamlandı", 15: "Tamamlandı", 16: "Tamamlandı",
                    17: "Tamamlandı", 18: "Tamamlandı",
                },
            },
            {
                "parca_no": "B20448-003",
                "parca_adi": "Arc Chute Assembly",
                "musteri": "ABB Ltd.",
                "sunum_seviyesi": 3,
                "durum": "Hazırlanıyor",
                "revizyon_nedeni": "Tasarım değişikliği — malzeme revizyonu",
                "sunum_tarihi": None,
                "onay_tarihi": None,
                "sorumlu_id": kalite_id,
                "surec_id": m02_id,
                "element_durumlari": {
                    1: "Tamamlandı", 2: "Tamamlandı", 3: "Hazırlanıyor", 4: "Tamamlandı",
                    5: "Tamamlandı", 6: "Hazırlanıyor", 7: "Hazırlanıyor", 8: "Hazırlanmadı",
                    9: "Hazırlanmadı", 10: "Hazırlanmadı", 11: "Hazırlanmadı", 12: "Hazırlanmadı",
                    13: "Uygulanamaz", 14: "Hazırlanmadı", 15: "Hazırlanmadı", 16: "Uygulanamaz",
                    17: "Tamamlandı", 18: "Hazırlanmadı",
                },
            },
        ]

        if not db.query(PPAPSubmission).first():
            for pdata in ppap_data:
                elem_durumlari = pdata.pop("element_durumlari")
                ppap = PPAPSubmission(**pdata)
                db.add(ppap)
                db.flush()

                for no, en, tr in PPAP_ELEMENTLERI:
                    elem = PPAPElement(
                        ppap_id=ppap.id,
                        element_no=no,
                        element_adi_en=en,
                        element_adi_tr=tr,
                        durum=elem_durumlari.get(no, "Hazırlanmadı"),
                    )
                    db.add(elem)

            db.commit()
            print(f"[OK] {len(ppap_data)} örnek PPAP sunumu oluşturuldu")

        if not db.query(QRQCItem).first():
            uretim_proc = db.query(Process).filter_by(kod="M02").first()
            kalite_user = db.query(User).filter_by(rol="Doküman Kontrol").first()
            admin_user = db.query(User).filter_by(rol="Admin").first()

            # Örnek DÖF
            dof_demo = CorrectiveAction(
                dof_no="DÖF-2026-099",
                baslik="[QRQC-2026-002] Kalıp maça sıkışması ve ölçü dışı çapak",
                kaynak_tipi="QRQC",
                ilgili_surec_id=uretim_proc.id if uretim_proc else None,
                tespit_tarihi=date.today() - timedelta(days=2),
                acan_id=admin_user.id if admin_user else None,
                sorumlu_id=kalite_user.id if kalite_user else None,
                tanim="Enjeksiyon hat 4 maça sıkışması nedeniyle 150 adet hatalı parça üretilmiştir.",
                containment_aksiyonu="Kalıp bakıma çekildi, 150 adet parça karantinaya alındı.",
                durum="Devam Ediyor",
            )
            db.add(dof_demo)
            db.flush()

            qrqc_samples = [
                QRQCItem(
                    qrqc_no="QRQC-2026-001",
                    baslik="Enjeksiyon 02 Hattında Radyal Çatlak",
                    kategori="Kalite",
                    seviye="Hat / Saha",
                    hat_istasyon="Enjeksiyon-02",
                    vardiya="1. Vardiya",
                    tespit_tarihi=datetime.now() - timedelta(hours=5),
                    bildiren_id=admin_user.id if admin_user else None,
                    sorumlu_id=kalite_user.id if kalite_user else None,
                    surec_id=uretim_proc.id if uretim_proc else None,
                    problem_tanimi="Numune kontrolünde 35 adette gözle görülür radyal çatlak tespit edildi.",
                    etkilenen_miktar=35,
                    gecici_onlem="Hammadde kurutma sıcaklığı kontrol edildi, palet karantinaya alındı.",
                    kok_neden="Kurutucu ısıtıcısı arızası nedeniyle nemli hammadde beslemesi.",
                    kalici_aksiyon="Isıtıcı rezistansı yenilendi ve nem ölçüm kontrolü eklendi.",
                    durum="Geçici Aksiyonda",
                    hedef_kapanis_tarihi=date.today() + timedelta(days=1),
                ),
                QRQCItem(
                    qrqc_no="QRQC-2026-002",
                    baslik="Kalıp Maça Sıkışması ve Ölçü Dışı Çapak",
                    kategori="Kalite",
                    seviye="Fabrika / Yönetim",
                    hat_istasyon="Enjeksiyon-04",
                    vardiya="2. Vardiya",
                    tespit_tarihi=datetime.now() - timedelta(days=2),
                    bildiren_id=kalite_user.id if kalite_user else None,
                    sorumlu_id=kalite_user.id if kalite_user else None,
                    surec_id=uretim_proc.id if uretim_proc else None,
                    problem_tanimi="Enjeksiyon 4 kalıbında maça sıkışması nedeniyle ölçü kaçıklığı ve çapak.",
                    etkilenen_miktar=150,
                    gecici_onlem="Kalıp söküldü, karantinadaki 150 parça ayıklandı.",
                    kok_neden="Maça yağlama hidrolik basınç düşüklüğü.",
                    kalici_aksiyon="8D DÖF çalışması başlatıldı.",
                    durum="DÖF Tetiklendi",
                    dof_id=dof_demo.id,
                    hedef_kapanis_tarihi=date.today() + timedelta(days=7),
                ),
                QRQCItem(
                    qrqc_no="QRQC-2026-003",
                    baslik="Montaj İstasyonu Yağ Sızıntısı Riskli Durum",
                    kategori="İSG",
                    seviye="Hat / Saha",
                    hat_istasyon="Montaj-B",
                    vardiya="3. Vardiya",
                    tespit_tarihi=datetime.now() - timedelta(days=5),
                    bildiren_id=admin_user.id if admin_user else None,
                    sorumlu_id=admin_user.id if admin_user else None,
                    surec_id=uretim_proc.id if uretim_proc else None,
                    problem_tanimi="Zeminde hidrolik yağ birikintisi kayma tehlikesi oluşturdu.",
                    etkilenen_miktar=0,
                    gecici_onlem="Talaş ve emici ped serildi, saha temizlendi.",
                    kok_neden="Hortum rekor gevşemesi.",
                    kalici_aksiyon="Rekor sıkıldı ve periyodik sızdırmazlık kontrolüne eklendi.",
                    durum="Kapatıldı",
                    kapanis_tarihi=datetime.now() - timedelta(days=4),
                    hedef_kapanis_tarihi=date.today() - timedelta(days=4),
                ),
            ]
            for q in qrqc_samples:
                db.add(q)
            db.commit()
            print(f"[OK] {len(qrqc_samples)} örnek QRQC kaydı oluşturuldu")

        print(f"[OK] {len(processes_data)} süreç oluşturuldu")
        print(f"[OK] {len(docs_data)} örnek doküman oluşturuldu")
        print("[OK] Demo veriler başarıyla yüklendi!")

    except Exception as e:
        db.rollback()
        print(f"[HATA] Seed data hatası: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
