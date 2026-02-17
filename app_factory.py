"""Application factory for Flask app creation."""

from __future__ import annotations

import logging
import signal
import threading

from flask import Flask

from config import get_config
from config.database import close_db
from routes import api_bp, jobs_bp, pages_bp, sessions_bp
from security.csrf import get_csrf_token_from_session, get_or_create_csrf_token

logger = logging.getLogger(__name__)

# Shutdown flag for graceful shutdown
_shutdown_event = threading.Event()


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Set database path in app config
    app.config["DATABASE_PATH"] = str(config_class.SCRAPER_DB_PATH)

    # Register teardown functions
    app.teardown_appcontext(close_db)

    # Register blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(api_bp)

    # Register before_request handler for CSRF and shutdown checks
    @app.before_request
    def before_request():
        """Check for shutdown and initialize CSRF token."""
        from flask import request

        if _shutdown_event.is_set():
            from flask import abort

            abort(503, "Server is shutting down")

        get_or_create_csrf_token(request)

    # Register context processor for CSRF token injection
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates."""
        from flask import request

        return {"csrf_token": get_csrf_token_from_session(request) or ""}

    # Register error handlers
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

    # Initialize database tables using the repositories
    from repositories.file_repository import FileRepository
    from repositories.job_repository import JobRepository
    from repositories.settings_repository import SettingsRepository

    with app.app_context():
        # Initialize repositories which will create tables if needed
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
        30,  # Default timeout
    )


def register_signal_handlers():
    """Register signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_shutdown_event():
    """Get the shutdown event for external components."""
    return _shutdown_event
