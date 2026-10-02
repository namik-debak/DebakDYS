"""
DYS application package scaffold.

Named ``dys_app`` (not ``app``) to avoid circular imports with the legacy
``app.py`` module. Phase 1 keeps the Flask singleton in ``app.py``; a full
application factory can migrate here later.
"""


def create_app():
    """Return the existing Flask app singleton (optional factory entrypoint)."""
    import app as app_module

    return app_module.app
