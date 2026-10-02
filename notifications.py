"""
DYS — E-posta Bildirim Altyapısı
================================
DYS_SMTP_* ortam değişkenlerinden yapılandırılır. SMTP host tanımlı değilse
gönderim yapılmaz (no-op) ve yalnızca uyarı loglanır — böylece SMTP bilgileri
sonradan eklenene kadar uygulama sorunsuz çalışır.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from config import Config

logger = logging.getLogger("dys.notifications")


def is_configured():
    return bool(Config.SMTP_HOST) and Config.NOTIFICATIONS_ENABLED


def send_mail(to, subject, body, html=None):
    """
    Tek bir e-posta gönderir. Başarılıysa True, aksi halde False döner.
    Host yapılandırılmamışsa no-op (True dönmez, uyarı loglar).
    """
    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r for r in recipients if r]
    if not recipients:
        return False

    if not is_configured():
        logger.warning(
            "SMTP yapılandırılmamış; e-posta gönderilmedi. Konu=%r Alıcı=%r",
            subject, recipients,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("DYS", Config.SMTP_FROM))
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            if Config.SMTP_USER:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.sendmail(Config.SMTP_FROM, recipients, msg.as_string())
        logger.info("E-posta gönderildi: %r → %r", subject, recipients)
        return True
    except Exception:
        logger.exception("E-posta gönderilirken hata oluştu (konu=%r)", subject)
        return False


def _doc_url(doc_id):
    base = Config.APP_BASE_URL.rstrip("/")
    prefix = Config.PREFIX.rstrip("/")
    return f"{base}{prefix}/documents/{doc_id}"


def notify_submitted_for_approval(doc, approvers):
    """Onaya gönderim: onaylayacak kişilere bilgi ver."""
    emails = [u.eposta for u in approvers if u and u.eposta]
    if not emails:
        return
    body = (
        f"'{doc.dokuman_no} - {doc.baslik}' dokümanı onayınıza sunuldu.\n\n"
        f"Doküman: {_doc_url(doc.id)}\n"
    )
    send_mail(emails, f"[DYS] Onay bekliyor: {doc.dokuman_no}", body)


def notify_rejected(doc, hazirlayan, aciklama=""):
    if not (hazirlayan and hazirlayan.eposta):
        return
    body = (
        f"'{doc.dokuman_no} - {doc.baslik}' dokümanı reddedildi ve size geri gönderildi.\n\n"
        f"Ret açıklaması: {aciklama or '-'}\n\n"
        f"Doküman: {_doc_url(doc.id)}\n"
    )
    send_mail(hazirlayan.eposta, f"[DYS] Reddedildi: {doc.dokuman_no}", body)


def notify_approved(doc, hazirlayan):
    if not (hazirlayan and hazirlayan.eposta):
        return
    body = (
        f"'{doc.dokuman_no} - {doc.baslik}' dokümanı tüm onay adımlarından geçti ve yayınlandı.\n\n"
        f"Doküman: {_doc_url(doc.id)}\n"
    )
    send_mail(hazirlayan.eposta, f"[DYS] Onaylandı: {doc.dokuman_no}", body)


def notify_distributed(doc, kullanici):
    if not (kullanici and kullanici.eposta):
        return
    body = (
        f"Size yeni bir doküman dağıtıldı: '{doc.dokuman_no} - {doc.baslik}'.\n"
        f"Lütfen okuyup okundu olarak işaretleyin.\n\n"
        f"Doküman: {_doc_url(doc.id)}\n"
    )
    send_mail(kullanici.eposta, f"[DYS] Yeni doküman dağıtımı: {doc.dokuman_no}", body)


def _capa_url(capa_id):
    base = Config.APP_BASE_URL.rstrip("/")
    prefix = Config.PREFIX.rstrip("/")
    return f"{base}{prefix}/capa/{capa_id}"


def notify_capa_assigned(capa, sorumlu):
    """Yeni DÖF sorumluya atandığında bilgilendir."""
    if not (sorumlu and sorumlu.eposta):
        return
    plan = capa.planlanan_tarih.strftime("%d.%m.%Y") if capa.planlanan_tarih else "—"
    body = (
        f"Size yeni bir DÖF atandı.\n\n"
        f"DÖF No: {capa.dof_no}\n"
        f"Başlık: {capa.baslik}\n"
        f"Planlanan kapanış: {plan}\n\n"
        f"Detay: {_capa_url(capa.id)}\n"
    )
    send_mail(sorumlu.eposta, f"[DYS] DÖF atandı: {capa.dof_no}", body)


def notify_capa_reminder(capa, kind="yaklasan"):
    """
    DÖF hatırlatması.
    kind: 'geciken' | 'yaklasan'
    Alıcı: sorumlu (yoksa açan).
    """
    alici = getattr(capa, "sorumlu", None) or getattr(capa, "acan", None)
    if not (alici and alici.eposta):
        return False
    plan = capa.planlanan_tarih.strftime("%d.%m.%Y") if capa.planlanan_tarih else "—"
    if kind == "geciken":
        konu = f"[DYS] Gecikmiş DÖF: {capa.dof_no}"
        durum_metin = "Planlanan kapanış tarihi geçti. Lütfen durumu güncelleyin."
    else:
        konu = f"[DYS] DÖF hatırlatma: {capa.dof_no}"
        durum_metin = "Planlanan kapanış yaklaşıyor. Lütfen aksiyonları tamamlayın."
    body = (
        f"{durum_metin}\n\n"
        f"DÖF No: {capa.dof_no}\n"
        f"Başlık: {capa.baslik}\n"
        f"Durum: {capa.durum}\n"
        f"Planlanan kapanış: {plan}\n\n"
        f"Detay: {_capa_url(capa.id)}\n"
    )
    return send_mail(alici.eposta, konu, body)
