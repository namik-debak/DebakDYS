"""
Optional Redis helpers for rate-limit storage and session revoke list.

When ``DYS_REDIS_URL`` is empty, all helpers no-op (SQLite / memory defaults).
"""

import logging

from config import Config

logger = logging.getLogger("dys.redis")

_client = None
_tried = False


def get_redis():
    """Return a connected ``redis.Redis`` client, or None if unavailable."""
    global _client, _tried
    if not Config.REDIS_URL:
        return None
    if _tried:
        return _client
    _tried = True
    try:
        import redis as redis_lib

        client = redis_lib.Redis.from_url(Config.REDIS_URL, decode_responses=True)
        client.ping()
        _client = client
        return _client
    except Exception:
        logger.warning("Redis unavailable; session revoke list disabled.", exc_info=True)
        _client = None
        return None


def _revoke_key(user_id):
    return f"dys:session_revoke:{int(user_id)}"


def revoke_session(user_id, ttl_seconds=None):
    """Mark a user's sessions as revoked until TTL expires."""
    if not Config.SESSION_REVOKE_ENABLED or user_id is None:
        return False
    client = get_redis()
    if client is None:
        return False
    if ttl_seconds is None:
        ttl_seconds = int(Config.SESSION_LIFETIME_HOURS * 3600)
    try:
        client.setex(_revoke_key(user_id), max(60, ttl_seconds), "1")
        return True
    except Exception:
        logger.exception("revoke_session failed user_id=%s", user_id)
        return False


def clear_session_revoke(user_id):
    """Clear revoke flag (e.g. after a successful fresh login)."""
    if not Config.SESSION_REVOKE_ENABLED or user_id is None:
        return False
    client = get_redis()
    if client is None:
        return False
    try:
        client.delete(_revoke_key(user_id))
        return True
    except Exception:
        logger.exception("clear_session_revoke failed user_id=%s", user_id)
        return False


def is_session_revoked(user_id):
    """Return True if the user id is on the Redis revoke list."""
    if not Config.SESSION_REVOKE_ENABLED or user_id is None:
        return False
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(client.exists(_revoke_key(user_id)))
    except Exception:
        logger.exception("is_session_revoked failed user_id=%s", user_id)
        return False
