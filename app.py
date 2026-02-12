"""Flask application for the Python Content Scraper.

This module provides a web interface for downloading content from
Instagram and YouTube with real-time progress tracking via HTMX.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import shutil
import signal
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_executor import Executor

from config import (
    Config,
    ALL_STATUSES,
    FILE_TYPE_AUDIO,
    FILE_TYPE_IMAGE,
    FILE_TYPE_METADATA,
    FILE_TYPE_TRANSCRIPT,
    FILE_TYPE_VIDEO,
    INSTAGRAM_PATTERNS,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
    YOUTUBE_PATTERNS,
)
from scrapers import InstagramScraper, YouTubeScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Executor for background tasks
executor = Executor(app)

# Shutdown flag
_shutdown_event = threading.Event()


def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT,
                progress INTEGER DEFAULT 0,
                current_operation TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                bytes_downloaded INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT (datetime('utc')),
                updated_at TIMESTAMP NOT NULL DEFAULT (datetime('utc')),
                completed_at TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                metadata_json TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT (datetime('utc')),
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT (datetime('utc'))
            )
        """
        )

        conn.commit()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with row factory.

    Yields:
        SQLite connection with row factory enabled
    """
    conn = sqlite3.connect(app.config["SCRAPER_DB_PATH"])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_job(url: str, platform: str) -> str:
    """Create a new job record.

    Args:
        url: The URL to scrape
        platform: Platform identifier ('youtube' or 'instagram')

    Returns:
        Job ID (UUID v4)
    """
    job_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, url, platform, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('utc'), datetime('utc'))
            """,
            (job_id, url, platform, STATUS_PENDING),
        )
        conn.commit()

    return job_id


def update_job(job_id: str, **fields: Any) -> None:
    """Update a job record.

    Args:
        job_id: Job ID to update
        **fields: Fields to update (status, progress, current_operation, etc.)
    """
    if not fields:
        return

    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [job_id]

    with get_db() as conn:
        conn.execute(
            f"UPDATE jobs SET {set_clause}, updated_at = datetime('utc') WHERE id = ?",
            values,
        )
        conn.commit()


def get_job(job_id: str) -> dict[str, Any] | None:
    """Get a job by ID.

    Args:
        job_id: Job ID

    Returns:
        Job dict or None if not found
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            return dict(row)
    return None


def get_active_jobs() -> list[dict[str, Any]]:
    """Get all active (pending or running) jobs.

    Returns:
        List of job dicts ordered by creation time
    """
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM jobs
            WHERE status IN (?, ?)
            ORDER BY created_at ASC
            """,
            (STATUS_PENDING, STATUS_RUNNING),
        ).fetchall()
        return [dict(row) for row in rows]


def get_jobs(
    platform: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Get jobs with optional filtering.

    Args:
        platform: Filter by platform
        status: Filter by status
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of job dicts
    """
    query = "SELECT * FROM jobs WHERE 1=1"
    params: list[Any] = []

    if platform:
        query += " AND platform = ?"
        params.append(platform)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_job_files(job_id: str) -> list[dict[str, Any]]:
    """Get all files associated with a job.

    Args:
        job_id: Job ID

    Returns:
        List of file dicts
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM files WHERE job_id = ? ORDER BY created_at ASC",
            (job_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_job(job_id: str, delete_files: bool = True) -> bool:
    """Delete a job and optionally its files.

    Args:
        job_id: Job ID to delete
        delete_files: Whether to delete physical files

    Returns:
        True if deleted, False if not found
    """
    job = get_job(job_id)
    if not job:
        return False

    # Delete physical files
    if delete_files:
        files = get_job_files(job_id)
        download_dir = Path(app.config["SCRAPER_DOWNLOAD_DIR"])

        for file_record in files:
            file_path = download_dir / file_record["file_path"]
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning("Could not delete file %s: %s", file_path, e)

        # Try to remove empty directories
        for file_record in files:
            file_path = download_dir / file_record["file_path"]
            try:
                parent = file_path.parent
                while parent != download_dir:
                    if parent.is_dir() and not any(parent.iterdir()):
                        parent.rmdir()
                    parent = parent.parent
            except Exception:
                pass

    # Delete from database
    with get_db() as conn:
        conn.execute("DELETE FROM files WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()

    return True


def detect_platform(url: str) -> str | None:
    """Detect platform from URL.

    Args:
        url: URL to check

    Returns:
        'youtube', 'instagram', or None
    """
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, url):
            return "youtube"

    for pattern in INSTAGRAM_PATTERNS:
        if re.search(pattern, url):
            return "instagram"

    return None


def validate_url(url: str) -> tuple[bool, str | None]:
    """Validate a URL.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    # Platform detection
    platform = detect_platform(url)
    if not platform:
        return False, "Unsupported URL. Please provide a valid Instagram or YouTube URL."

    return True, None


def make_progress_callback(job_id: str) -> callable:
    """Create a progress callback function for a job.

    Args:
        job_id: Job ID

    Returns:
        Callback function
    """
    def callback(progress: int, operation: str) -> None:
        update_job(job_id, progress=progress, current_operation=operation)

    return callback


def execute_download(job_id: str) -> None:
    """Execute a download job in the background.

    Args:
        job_id: Job ID to execute
    """
    if _shutdown_event.is_set():
        logger.info("Shutdown in progress, skipping job %s", job_id)
        return

    job = get_job(job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return

    url = job["url"]
    platform = job["platform"]

    # Update status to running
    update_job(job_id, status=STATUS_RUNNING)

    try:
        db_path = Path(app.config["SCRAPER_DB_PATH"])
        download_dir = Path(app.config["SCRAPER_DOWNLOAD_DIR"])

        progress_callback = make_progress_callback(job_id)

        if platform == "youtube":
            scraper = YouTubeScraper(
                db_path=db_path,
                download_dir=download_dir,
                progress_callback=progress_callback,
            )
        else:  # instagram
            scraper = InstagramScraper(
                db_path=db_path,
                download_dir=download_dir,
                progress_callback=progress_callback,
            )

        # Execute scrape
        result = scraper.scrape(url, job_id)

        if result["success"]:
            update_job(
                job_id,
                status=STATUS_COMPLETED,
                title=result.get("title"),
                progress=100,
                completed_at=datetime.utcnow().isoformat(),
            )
        else:
            error = result.get("error", "Unknown error")
            update_job(
                job_id,
                status=STATUS_FAILED,
                error_message=error,
                completed_at=datetime.utcnow().isoformat(),
            )

    except Exception as e:
        logger.exception("Error executing job %s: %s", job_id, e)
        update_job(
            job_id,
            status=STATUS_FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow().isoformat(),
        )


# ============================================================================
# Routes
# ============================================================================

@app.route("/")
def index():
    """Dashboard with URL input and active jobs."""
    return render_template("dashboard.html")


@app.route("/browse")
@app.route("/browse/<path:subpath>")
def browse(subpath: str = ""):
    """Browse downloaded content by platform/profile/content."""
    download_dir = Path(app.config["SCRAPER_DOWNLOAD_DIR"])

    if subpath:
        browse_path = download_dir / subpath
    else:
        browse_path = download_dir

    if not browse_path.exists():
        flash(f"Path not found: {subpath}", "error")
        return redirect(url_for("browse"))

    if not browse_path.is_dir():
        # It's a file, serve it
        return send_file(browse_path)

    # List directory contents
    items = []
    for item in sorted(browse_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        items.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else None,
            "relative_path": item.relative_to(download_dir) if item != browse_path else Path(),
        })

    return render_template(
        "browse.html",
        current_path=Path(subpath) if subpath else Path(),
        items=items,
    )


@app.route("/history")
def history():
    """Download history with filters."""
    platform = request.args.get("platform")
    status = request.args.get("status")

    jobs = get_jobs(platform=platform, status=status, limit=200)

    return render_template(
        "history.html",
        jobs=jobs,
        filters={"platform": platform, "status": status},
    )


@app.route("/job/<job_id>")
def job_detail(job_id: str):
    """Job detail page or HTMX partial."""
    job = get_job(job_id)
    if not job:
        abort(404)

    files = get_job_files(job_id)
    is_htmx = "HX-Request" in request.headers

    if is_htmx:
        return render_template("partials/job_card.html", job=job, files=files)

    return render_template("job_detail.html", job=job, files=files)


@app.route("/job/<job_id>/status")
def job_status(job_id: str):
    """Job status as HTMX fragment for polling."""
    job = get_job(job_id)
    if not job:
        abort(404)

    files = get_job_files(job_id)

    return render_template("partials/job_card.html", job=job, files=files)


@app.route("/jobs/active")
def active_jobs():
    """Active jobs as HTMX fragment."""
    jobs = get_active_jobs()

    return render_template("partials/active_jobs.html", jobs=jobs)


@app.route("/download", methods=["POST"])
def download():
    """Accept URL input, create background job."""
    url = request.form.get("url", "").strip()

    # Validate URL
    is_valid, error = validate_url(url)
    if not is_valid:
        if "HX-Request" in request.headers:
            return f'<div class="notification error">{error}</div>', 400
        flash(error, "error")
        return redirect(url_for("index"))

    # Detect platform
    platform = detect_platform(url)

    # Create job
    job_id = create_job(url, platform)

    # Submit background job
    executor.submit(execute_download, job_id)

    if "HX-Request" in request.headers:
        # Return the new job card
        job = get_job(job_id)
        return render_template("partials/job_card.html", job=job, files=[])

    flash(f"Download started for {url}", "success")
    return redirect(url_for("index"))


@app.route("/job/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    """Cancel a running job."""
    job = get_job(job_id)
    if not job:
        abort(404)

    if job["status"] not in (STATUS_PENDING, STATUS_RUNNING):
        flash("Job cannot be cancelled", "error")
        return redirect(url_for("index"))

    update_job(job_id, status=STATUS_CANCELLED, completed_at=datetime.utcnow().isoformat())

    if "HX-Request" in request.headers:
        return "", 204

    flash("Job cancelled", "success")
    return redirect(url_for("index"))


@app.route("/job/<job_id>/retry", methods=["POST"])
def retry_job(job_id: str):
    """Retry a failed job."""
    job = get_job(job_id)
    if not job:
        abort(404)

    if job["status"] != STATUS_FAILED:
        flash("Only failed jobs can be retried", "error")
        return redirect(url_for("index"))

    # Create new job with same URL
    url = job["url"]
    platform = job["platform"]
    new_job_id = create_job(url, platform)

    # Submit background job
    executor.submit(execute_download, new_job_id)

    if "HX-Request" in request.headers:
        new_job = get_job(new_job_id)
        return render_template("partials/job_card.html", job=new_job, files=[])

    flash("Job retry started", "success")
    return redirect(url_for("index"))


@app.route("/job/<job_id>", methods=["DELETE"])
def delete_job_route(job_id: str):
    """Delete a job and its files."""
    if delete_job(job_id, delete_files=True):
        if "HX-Request" in request.headers:
            return "", 204
        flash("Job deleted", "success")
    else:
        if "HX-Request" in request.headers:
            return "Job not found", 404
        flash("Job not found", "error")

    return redirect(url_for("history"))


# ============================================================================
# Error handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if "HX-Request" in request.headers:
        return "Not found", 404
    return render_template("error.html", error="Not found"), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    if "HX-Request" in request.headers:
        return "Server error", 500
    return render_template("error.html", error="Server error"), 500


# ============================================================================
# Startup and shutdown
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d, initiating shutdown...", signum)
    _shutdown_event.set()

    # Stop accepting new jobs
    # Give running jobs time to complete
    logger.info("Waiting for running jobs to complete (timeout: %ds)...",
                app.config.get("SHUTDOWN_TIMEOUT", 30))


def before_request():
    """Check for shutdown before each request."""
    if _shutdown_event.is_set():
        abort(503, "Server is shutting down")


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register before_request handler
app.before_request(before_request)


def initialize_app():
    """Initialize the application."""
    # Validate configuration
    config = Config()
    errors = config.validate()
    if errors:
        logger.error("Configuration errors: %s", errors)

    # Ensure directories exist
    config.ensure_directories()

    # Initialize database
    init_db()

    logger.info("Application initialized")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    # Initialize before running
    initialize_app()

    config = Config()
    logger.info("Starting Flask server on %s:%s",
                config.APP_HOST, config.APP_PORT)

    app.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        debug=config.DEBUG,
    )
