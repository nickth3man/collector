"""
Database configuration for the Python Content Scraper.

This module provides database configuration and connection management.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from flask import current_app, g

from .settings import Config


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize database configuration.

        Args:
            db_path: Path to the SQLite database file. If None, uses Config.SCRAPER_DB_PATH.
        """
        self.db_path = db_path or Config.SCRAPER_DB_PATH
        self._ensure_db_directory()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        if self.db_path.parent:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection.

        Yields:
            SQLite database connection with row factory set to dict.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Returns:
            List of dictionaries representing the result rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple[Any, ...] = ()) -> int:
        """Execute an update/insert/delete query.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: list[tuple[Any, ...]]) -> int:
        """Execute a query multiple times with different parameters.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def initialize_tables(self) -> None:
        """Initialize database tables if they don't exist."""
        # This will be implemented by specific repositories
        pass


def get_db_config() -> DatabaseConfig:
    """Get the database configuration from Flask application context.

    Returns:
        DatabaseConfig instance from the current application context.

    Raises:
        RuntimeError: If called outside of an application context.
    """
    if "db_config" not in g:
        g.db_config = DatabaseConfig()
    return g.db_config


def get_db() -> sqlite3.Connection:
    """Get a database connection from Flask application context.

    Returns:
        SQLite database connection.

    Raises:
        RuntimeError: If called outside of an application context.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e: BaseException | None = None) -> None:
    """Close database connection from Flask application context.

    Args:
        e: Exception that occurred during request handling (unused).
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()
