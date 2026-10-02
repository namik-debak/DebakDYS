"""Document service helpers — thin wrappers over models + authz."""

from models import Document
import authz


def get_document(db, doc_id):
    """Load a document by primary key (SQLAlchemy 2.0 Session.get)."""
    return db.get(Document, doc_id)


def list_accessible_documents(db, user_id, rol, docs=None):
    """Return documents the user may access.

    If *docs* is omitted, loads all documents ordered by document number.
    """
    if docs is None:
        docs = db.query(Document).order_by(Document.dokuman_no).all()
    return authz.accessible_documents(db, user_id, rol, docs)
