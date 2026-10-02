"""
DYS — yetkilendirme yardımcıları.
"""


def is_read_only(rol):
    return rol == "Sadece Görüntüleme"


def can_access_document(db, user_id, rol, doc):
    if not doc:
        return False
    if rol in ("Admin", "Doküman Kontrol"):
        return True
    if getattr(doc, "olusturan_id", None) == user_id:
        return True
    try:
        from models import DocumentDistribution
        dist = (
            db.query(DocumentDistribution)
            .filter_by(document_id=doc.id, kullanici_id=user_id)
            .first()
        )
        if dist:
            return True
    except Exception:
        pass
    return rol in ("Kullanıcı", "Admin", "Doküman Kontrol")


def accessible_documents(db, user_id, rol, docs):
    if rol in ("Admin", "Doküman Kontrol"):
        return docs
    return [d for d in docs if can_access_document(db, user_id, rol, d)]


def approval_action_error(db, user_id, rol, approval):
    """None = izin var; aksi halde hata mesajı."""
    if not approval:
        return "Onay kaydı bulunamadı."
    if rol in ("Admin", "Doküman Kontrol"):
        return None
    if getattr(approval, "onayci_id", None) == user_id:
        return None
    return "Bu onay adımı için yetkiniz yok."


def can_act_on_approval(db, user_id, rol, approval):
    return approval_action_error(db, user_id, rol, approval) is None
