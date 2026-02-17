"""Application factory for Flask app creation."""

from __future__ import annotations

import logging
import signal
import threading

from flask import Flask

from .config import get_config
from .config.database import close_db
from .routes import api_bp, jobs_bp, pages_bp, sessions_bp
from .security.csrf import get_csrf_token_from_session, get_or_create_csrf_token

logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    config_class = get_config()
    app.config.from_object(config_class)

    errors = config_class.validate()
    if errors:
        logger.warning("Configuration warnings: %s", errors)

    config_class.ensure_directories()

    app.config["DATABASE_PATH"] = str(config_class.SCRAPER_DB_PATH)

    app.teardown_appcontext(close_db)

    app.register_blueprint(pages_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def before_request():
        """Check for shutdown and initialize CSRF token."""
        from flask import request

        if _shutdown_event.is_set():
            from flask import abort

            abort(503, "Server is shutting down")

        get_or_create_csrf_token(request)

    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates."""
        from flask import request

        return {"csrf_token": get_csrf_token_from_session(request) or ""}

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        from flask import render_template, request

        if "HX-Request" in request.headers:
            return "Not found", 404
        return render_template("error.html", error="Not found"), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        from flask import render_template, request

        if "HX-Request" in request.headers:
            return "Server error", 500
        return render_template("error.html", error="Server error"), 500

    from .repositories.file_repository import FileRepository
    from .repositories.job_repository import JobRepository
    from .repositories.settings_repository import SettingsRepository

    with app.app_context():
        JobRepository()
        FileRepository()
        SettingsRepository()

    logger.info("Application created and configured")
    return app


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d, initiating shutdown...", signum)
    _shutdown_event.set()
    logger.info(
        "Waiting for running jobs to complete (timeout: %ds)...",
        30,
    )


def register_signal_handlers():
    """Register signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_shutdown_event():
    """Get the shutdown event for external components."""
    return _shutdown_event
