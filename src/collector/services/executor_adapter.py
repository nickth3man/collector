"""Task execution adapter for background jobs."""

from __future__ import annotations

from collections.abc import Callable
from threading import Thread
from typing import Any


class ExecutorAdapter:
    """Execution adapter for background task submission."""

    def submit_job(self, func: Callable[..., Any], *args: Any) -> Thread:
        """Submit a background job using daemon thread with Flask app context."""
        from flask import current_app

        def run_with_app_context():
            with current_app.app_context():
                func(*args)

        thread = Thread(target=run_with_app_context, daemon=True)
        thread.start()
        return thread
