"""Application factory for Flask app creation."""

from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    return app
