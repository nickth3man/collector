"""CSRF protection helpers for Flask application."""

from __future__ import annotations

import hmac
import secrets
import typing
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Request

CSRF_TOKEN_LENGTH = 32
CSRF_HEADER_NAME = "X-CSRFToken"
CSRF_FORM_FIELD = "csrf_token"
CSRF_SESSION_KEY = "_csrf_token"


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token.

    Returns:
        URL-safe base64 encoded token string
    """
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def get_csrf_token_from_session(request: Request) -> str | None:
    """Get CSRF token from session.

    Args:
        request: Flask request object with session

    Returns:
        CSRF token or None if not set
    """
    if not hasattr(request, "session"):
        return None
    session: Any = typing.cast(Any, request.session)
    return session.get(CSRF_SESSION_KEY)


def set_csrf_token_in_session(request: Request) -> str:
    """Generate and store a new CSRF token in session.

    Args:
        request: Flask request object with session

    Returns:
        The newly generated token
    """
    token = generate_csrf_token()
    if hasattr(request, "session"):
        session: Any = typing.cast(Any, request.session)
        session[CSRF_SESSION_KEY] = token
    return token


def get_or_create_csrf_token(request: Request) -> str:
    """Get existing CSRF token from session or create a new one.

    Args:
        request: Flask request object with session

    Returns:
        CSRF token string
    """
    return get_csrf_token_from_session(request) or set_csrf_token_in_session(request)


def extract_csrf_token(request: Request) -> str | None:
    """Extract CSRF token from request (form field or header).

    Checks both form data and headers for the token.

    Args:
        request: Flask request object

    Returns:
        CSRF token or None if not found
    """
    token = request.form.get(CSRF_FORM_FIELD)
    if token:
        return token

    token = request.headers.get(CSRF_HEADER_NAME)
    if token:
        return token

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return get_csrf_token_from_session(request)

    return None


def validate_csrf_token(request: Request, token: str | None = None) -> bool:
    """Validate CSRF token against session token.

    Args:
        request: Flask request object with session
        token: Token to validate (if None, extracts from request)

    Returns:
        True if valid, False otherwise
    """
    if token is None:
        token = extract_csrf_token(request)

    if not token:
        return False

    session_token = get_csrf_token_from_session(request)
    if not session_token:
        return False

    return hmac.compare_digest(token, session_token)


def validate_csrf_request(request: Request) -> bool:
    """Validate CSRF token for a state-changing request.

    Automatically extracts token from form field or header.

    Args:
        request: Flask request object

    Returns:
        True if valid, False otherwise
    """
    return validate_csrf_token(request)


def csrf_protected(func):
    """Decorator to protect a route with CSRF validation.

    Usage:
        @app.route('/submit', methods=['POST'])
        @csrf_protected
        def submit():
            ...

    Returns:
        Decorated function that validates CSRF before calling original
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import abort, request

        if not validate_csrf_request(request):
            abort(400, "CSRF token validation failed")
        return func(*args, **kwargs)

    return wrapper
