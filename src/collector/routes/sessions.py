"""Sessions blueprint for Instagram session management."""

from __future__ import annotations

import logging

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..security.csrf import validate_csrf_request
from ..services import SessionService

logger = logging.getLogger(__name__)

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/sessions")
def list_sessions():
    """List all saved Instagram sessions."""
    try:
        session_service = SessionService()
        result = session_service.list_sessions()
        if result["success"]:
            sessions = result["sessions"]
        else:
            sessions = []
            flash(f"Error listing sessions: {result.get('error', 'Unknown error')}", "error")
        return render_template("sessions.html", sessions=sessions)
    except Exception as e:
        logger.exception("Error listing sessions: %s", e)
        flash(f"Error listing sessions: {e}", "error")
        return redirect(url_for("pages.index"))


@sessions_bp.route("/sessions/upload", methods=["POST"])
def upload_session():
    """Upload a cookies.txt file to create a session."""
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    if "cookies_file" not in request.files:
        if "HX-Request" in request.headers:
            return '<div class="notification error">No file uploaded</div>', 400
        flash("No file uploaded", "error")
        return redirect(url_for("sessions.list_sessions"))

    file = request.files["cookies_file"]
    filename = file.filename or ""

    if filename == "":
        if "HX-Request" in request.headers:
            return '<div class="notification error">No file selected</div>', 400
        flash("No file selected", "error")
        return redirect(url_for("sessions.list_sessions"))

    if not filename.endswith(".txt"):
        if "HX-Request" in request.headers:
            return (
                '<div class="notification error">File must be .txt format (cookies.txt)</div>',
                400,
            )
        flash("File must be cookies.txt format", "error")
        return redirect(url_for("sessions.list_sessions"))

    try:
        session_service = SessionService()

        # Read file content
        file_content = file.read().decode("utf-8")

        # Process the uploaded file
        result = session_service.upload_session(file_content, filename)

        if result["success"]:
            if "HX-Request" in request.headers:
                return """
                <div class="notification success">
                    Session uploaded successfully! Refresh to see it in the list.
                </div>
                """

            flash("Session uploaded successfully", "success")
        else:
            error_msg = result.get("error", "Unknown error")
            if "HX-Request" in request.headers:
                return f'<div class="notification error">{error_msg}</div>', 400
            flash(error_msg, "error")

        return redirect(url_for("sessions.list_sessions"))

    except Exception as e:
        logger.exception("Error uploading session: %s", e)
        if "HX-Request" in request.headers:
            return f'<div class="notification error">Failed to upload session: {str(e)}</div>', 500
        flash(f"Failed to upload session: {e}", "error")
        return redirect(url_for("sessions.list_sessions"))


@sessions_bp.route("/sessions/<username>/delete", methods=["POST"])
def delete_session(username: str):
    """Delete a saved session."""
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    try:
        session_service = SessionService()
        result = session_service.delete_session(username)
        if result["success"]:
            if "HX-Request" in request.headers:
                return "", 204
            flash("Session deleted", "success")
        else:
            error_msg = result.get("error", "Session not found")
            if "HX-Request" in request.headers:
                return error_msg, 404
            flash(error_msg, "error")
        return redirect(url_for("sessions.list_sessions"))
    except Exception as e:
        logger.exception("Error deleting session: %s", e)
        if "HX-Request" in request.headers:
            return f'<div class="notification error">Failed to delete: {str(e)}</div>', 500
        flash(f"Failed to delete session: {e}", "error")
        return redirect(url_for("sessions.list_sessions"))
