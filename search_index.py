"""
DYS — Tam Metin Arama (SQLite FTS5)
===================================
Doküman başlığı/numarası ve dosya içeriği (PDF/DOCX/TXT) üzerinde tam metin
arama. FTS5 sanal tablosu kullanılamıyorsa (ör. SQLite derlemesinde yoksa)
tüm fonksiyonlar güvenli biçimde no-op olur ve çağıran taraf LIKE aramasına
geri düşer.
"""

import os
import logging

from models import engine, SessionLocal, Document

logger = logging.getLogger("dys")

_FTS_STATE = None  # None=bilinmiyor, True=var, False=yok


def _ensure_fts(conn):
    """FTS5 tablosunu oluşturur; kullanılabilirliği önbelleğe alır."""
    global _FTS_STATE
    if _FTS_STATE is False:
        return False
    try:
        conn.exec_driver_sql(
            "CREATE VIRTUAL TABLE IF NOT EXISTS document_fts "
            "USING fts5(doc_id UNINDEXED, dokuman_no, baslik, icerik)"
        )
        _FTS_STATE = True
        return True
    except Exception as exc:  # pragma: no cover - platforma bağlı
        _FTS_STATE = False
        logger.warning("FTS5 kullanılamıyor, LIKE aramasına düşülüyor: %s", exc)
        return False


def extract_text(path):
    """PDF/DOCX/TXT/CSV dosyasından düz metin çıkarır (hata olursa boş döner)."""
    if not path or not os.path.isfile(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            import fitz  # PyMuPDF
            with fitz.open(path) as doc:
                return "\n".join(page.get_text() for page in doc)
        if ext == ".docx":
            import docx
            d = docx.Document(path)
            return "\n".join(p.text for p in d.paragraphs)
        if ext in (".txt", ".csv"):
            with open(path, encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception:
        logger.exception("Metin çıkarılamadı: %s", path)
    return ""


def index_document(doc_id, dokuman_no, baslik, file_path):
    """Bir dokümanın FTS kaydını günceller (varsa siler, yeniden ekler)."""
    try:
        icerik = extract_text(file_path)
        with engine.begin() as conn:
            if not _ensure_fts(conn):
                return
            conn.exec_driver_sql("DELETE FROM document_fts WHERE doc_id = ?", (doc_id,))
            conn.exec_driver_sql(
                "INSERT INTO document_fts (doc_id, dokuman_no, baslik, icerik) "
                "VALUES (?, ?, ?, ?)",
                (doc_id, dokuman_no or "", baslik or "", icerik),
            )
    except Exception:
        logger.exception("FTS indeksleme hatası (doc_id=%s)", doc_id)


def remove_document(doc_id):
    """Bir dokümanı FTS indeksinden çıkarır."""
    try:
        with engine.begin() as conn:
            if not _ensure_fts(conn):
                return
            conn.exec_driver_sql("DELETE FROM document_fts WHERE doc_id = ?", (doc_id,))
    except Exception:
        logger.exception("FTS silme hatası (doc_id=%s)", doc_id)


def _to_match_query(query):
    """Kullanıcı metnini güvenli FTS5 prefix sorgusuna çevirir."""
    tokens = []
    for tok in (query or "").split():
        cleaned = tok.replace('"', "").strip()
        if cleaned:
            tokens.append(f'"{cleaned}"*')
    return " ".join(tokens)


def search_ids(query):
    """Sorguyla eşleşen doküman id listesini döndürür (FTS yoksa boş liste)."""
    match_q = _to_match_query(query)
    if not match_q:
        return []
    try:
        with engine.begin() as conn:
            if not _ensure_fts(conn):
                return []
            rows = conn.exec_driver_sql(
                "SELECT doc_id FROM document_fts WHERE document_fts MATCH ? "
                "ORDER BY rank",
                (match_q,),
            ).fetchall()
            return [r[0] for r in rows]
    except Exception:
        logger.exception("FTS arama hatası: %s", query)
        return []


def available():
    """FTS5 kullanılabilir mi? (arama rotasında karar için)"""
    try:
        with engine.begin() as conn:
            return _ensure_fts(conn)
    except Exception:
        return False


def backfill_if_empty():
    """FTS tablosu boşsa ve doküman varsa, tek seferlik indeksleme yapar."""
    try:
        with engine.begin() as conn:
            if not _ensure_fts(conn):
                return
            count = conn.exec_driver_sql("SELECT COUNT(*) FROM document_fts").scalar()
        if count and count > 0:
            return
    except Exception:
        logger.exception("FTS backfill kontrolü başarısız")
        return

    from helpers import resolve_file_path
    db = SessionLocal()
    try:
        docs = db.query(Document).all()
        indexed = 0
        for d in docs:
            path = resolve_file_path(d.dosya_yolu, d.dosya_adi) if d.dosya_yolu else None
            index_document(d.id, d.dokuman_no, d.baslik, path)
            indexed += 1
        logger.info("FTS backfill tamamlandı: %s doküman indekslendi", indexed)
    except Exception:
        logger.exception("FTS backfill hatası")
    finally:
        db.close()
