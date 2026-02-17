"""Path-safety helpers for secure file access."""

from __future__ import annotations

from pathlib import Path

from flask import abort, send_file


class PathSecurityError(Exception):
    """Raised when a path violates security constraints."""

    pass


def resolve_user_path(base_dir: Path, user_path: str) -> Path:
    """Resolve a user-provided relative path beneath base directory.

    Args:
        base_dir: The allowed base directory
        user_path: User-provided relative path

    Returns:
        Resolved absolute path

    Raises:
        PathSecurityError: If path attempts traversal outside base_dir
    """
    base_dir = base_dir.resolve()
    resolved = (base_dir / user_path).resolve()

    if not is_within_base(base_dir, resolved):
        raise PathSecurityError(f"Path '{user_path}' resolves outside allowed directory")

    return resolved


def is_within_base(base_dir: Path, candidate: Path) -> bool:
    """Check if candidate path is inside base_dir.

    Uses robust path containment checks across platforms.

    Args:
        base_dir: The base directory to check against
        candidate: The path to verify

    Returns:
        True if candidate is within base_dir, False otherwise
    """
    try:
        base_resolved = base_dir.resolve()
        candidate_resolved = candidate.resolve()
        candidate_resolved.relative_to(base_resolved)
        return True
    except (ValueError, OSError):
        return False


def safe_send_file(base_dir: Path, file_path: Path, as_attachment: bool = False):
    """Safe wrapper around Flask send_file with root containment.

    Args:
        base_dir: The allowed base directory
        file_path: Path to the file to send
        as_attachment: Whether to send as attachment vs inline

    Returns:
        Flask response with file

    Raises:
        404: If file not found
        403: If path is outside base_dir
    """
    base_dir = base_dir.resolve()
    resolved_path = file_path.resolve()

    if not is_within_base(base_dir, resolved_path):
        abort(403)

    if not resolved_path.exists():
        abort(404)

    if not resolved_path.is_file():
        abort(404)

    return send_file(resolved_path, as_attachment=as_attachment)
