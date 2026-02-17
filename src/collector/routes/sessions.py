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
    """List all saved Instagram sessions.

    Retrieves and displays all stored Instagram sessions with their
    associated metadata (username, creation date, etc.).

    Returns:
        HTML: Rendered sessions page (sessions.html) with:
            - sessions: List of session dictionaries with metadata

    Error Handling:
        If SessionService fails to list sessions, displays an error
        flash message and returns empty sessions list or redirects
        to index on exception.
    """
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
    """Upload a cookies.txt file to create or update an Instagram session.

    Accepts a cookies.txt file upload, validates the format,
    and creates a new session or updates an existing one.

    Form Parameters:
        cookies_file: Uploaded file containing cookies in Netscape cookie format
                      Must be a .txt file (typically named cookies.txt)

    Returns:
        HTML/Response:
            - If HTMX request and successful: Success notification div
            - If regular request and successful: Flash message and redirect to sessions list
            - On validation error: Error notification with 400 status code
            - On exception: Error notification with 500 status code

    Raises:
        HTTPException: 403 if CSRF token validation fails

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present:
            - Success: Returns success notification div
            - Validation error: Returns error notification div with 400
            - Exception: Returns error notification div with 500
        If no HX-Request header:
            - Success: Flash message and redirect to sessions list
            - Errors: Flash message and redirect to sessions list

    Validation Errors:
        - No file uploaded: Returns 400
        - Empty filename: Returns 400
        - Non-.txt file: Returns 400 with format error message
        - Invalid cookies.txt format: Returns 400 with parsing error

    File Requirements:
        - File format: .txt (Netscape cookie format)
        - Encoding: UTF-8
        - Content: Valid cookies.txt file with Instagram session cookies
    """
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
    """Delete a saved Instagram session.

    Permanently removes the session record and associated
    encrypted session file from storage.

    Args:
        username: Username of the session to delete (from URL path)

    Returns:
        Response:
            - If HTMX request and successful: Empty response with 204
            - If HTMX request and not found: Error message with 404
            - If regular request and successful: Flash message and redirect to sessions list
            - If HTMX request and exception: Error notification div with 500
            - If regular request and exception: Flash message and redirect to sessions list

    Raises:
        HTTPException: 403 if CSRF token validation fails

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present and successful: Returns 204 No Content
        If HX-Request header and not found: Returns error message with 404
        If HX-Request header and exception: Returns error notification div with 500
        If no HX-Request header: Flash message and redirect to sessions list

    Error Handling:
        If session not found (404): Returns error message or notification
        If exception occurs (500): Returns error message or notification
    """
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
