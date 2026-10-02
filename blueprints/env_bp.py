"""Environment blueprint stub."""

from flask import Blueprint

env_bp = Blueprint("env", __name__, url_prefix="/env")
