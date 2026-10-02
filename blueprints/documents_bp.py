"""Documents blueprint — Phase 1 platform health ping."""

from flask import Blueprint, jsonify

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/_platform/ping")
def _platform_ping():
    """Unauthenticated health ping proving blueprint registration works."""
    return jsonify({"ok": True, "service": "dys", "platform": "phase1"})
