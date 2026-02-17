"""Pages blueprint for main application pages."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from security.paths import PathSecurityError, resolve_user_path, safe_send_file
from services import JobService

logger = logging.getLogger(__name__)

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    """Dashboard with URL input and active jobs."""
    return render_template("dashboard.html")


@pages_bp.route("/browse")
@pages_bp.route("/browse/<path:subpath>")
def browse(subpath: str = ""):
    """Browse downloaded content by platform/profile/content."""
    from flask import current_app

    download_dir = Path(current_app.config["SCRAPER_DOWNLOAD_DIR"])

    try:
        browse_path = resolve_user_path(download_dir, subpath) if subpath else download_dir
    except PathSecurityError:
        abort(403)

    if not browse_path.exists():
        flash(f"Path not found: {subpath}", "error")
        return redirect(url_for("pages.browse"))

    if not browse_path.is_dir():
        return safe_send_file(download_dir, browse_path)

    # List directory contents
    items = []
    for item in sorted(browse_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        items.append(
            {
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None,
                "relative_path": str(item.relative_to(download_dir)) if item != browse_path else "",
            }
        )

    return render_template(
        "browse.html",
        current_path=subpath,
        current_path_parts=subpath.split("/") if subpath else [],
        is_root=not subpath,
        items=items,
    )


@pages_bp.route("/preview/<path:filepath>")
def preview_file(filepath: str):
    """Preview a file with inline display.

    Args:
        filepath: Relative path from downloads root
    """
    from flask import current_app

    download_dir = Path(current_app.config["SCRAPER_DOWNLOAD_DIR"])

    try:
        file_path = resolve_user_path(download_dir, filepath)
    except PathSecurityError:
        abort(403)

    if not file_path.exists():
        abort(404)

    if file_path.is_dir():
        return redirect(url_for("pages.browse", subpath=filepath))

    # Determine file type
    file_ext = file_path.suffix.lower()
    file_name = file_path.name

    # Check for different file types
    if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        file_type = "image"
    elif file_ext in [".mp4", ".mov", ".webm", ".mkv"]:
        file_type = "video"
    elif file_ext == ".txt":
        # Check if it's a transcript
        if "transcript" in file_name.lower():
            file_type = "transcript"
        else:
            file_type = "text"
    elif file_ext == ".json":
        file_type = "metadata"
    elif file_ext in [".mp3", ".m4a", ".wav"]:
        file_type = "audio"
    else:
        file_type = "unknown"

    # Read file content for text-based previews
    content = None
    if file_type in ["transcript", "text", "metadata"]:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            content = f"Error reading file: {e}"

    return render_template(
        "preview.html",
        file_path=str(file_path.relative_to(download_dir)),
        file_name=file_name,
        file_type=file_type,
        content=content,
    )


@pages_bp.route("/history")
def history():
    """Download history with filters."""
    platform = request.args.get("platform")
    status = request.args.get("status")

    job_service = JobService()
    jobs = job_service.list_jobs(platform=platform, status=status, limit=200)

    return render_template(
        "history.html",
        jobs=jobs,
        filters={"platform": platform, "status": status},
    )
