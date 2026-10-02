"""Auth blueprint stub.

Login / logout / set_locale remain on the legacy ``app`` module for
backward compatibility. Future work can move those views here.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)
