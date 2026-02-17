"""Repository layer for jobs/files/settings."""

from __future__ import annotations

from typing import Any

ALLOWED_JOB_UPDATE_FIELDS = frozenset(
    {
        "status",
        "title",
        "progress",
        "current_operation",
        "error_message",
        "retry_count",
        "bytes_downloaded",
        "completed_at",
    }
)
