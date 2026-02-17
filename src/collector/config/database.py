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
import re

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

    def create_indexes(self, model_classes: list[type]) -> None:
        """Create indexes for the given model classes.

        Args:
            model_classes: List of model classes to create indexes for.
        """
        print("Creating database indexes...")

        with self.get_connection() as conn:
            for model_class in model_classes:
                table_name = model_class.get_table_name()
                index_sqls = model_class.get_indexes_sql()

                if not index_sqls:
                    continue

                print(f"\n{table_name}:")
                for index_sql in index_sqls:
                    try:
                        # Extract index name for logging
                        match = re.search(
                            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)',
                            index_sql,
                            re.IGNORECASE
                        )
                        index_name = match.group(1) if match else "unknown"

                        conn.execute(index_sql)
                        print(f"  [OK] Created: {index_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  ✗ Error: {e}")

            conn.commit()
            print("\nIndex creation complete!")

    def ensure_indexes(self, model_classes: list[type]) -> None:
        """Ensure all indexes exist for the given models.

        This method checks for existing indexes and creates any missing ones.

        Args:
            model_classes: List of model classes to check/create indexes for.
        """
        print("Ensuring database indexes exist...")

        with self.get_connection() as conn:
            for model_class in model_classes:
                table_name = model_class.get_table_name()

                # Get existing indexes for this table
                existing_indexes = conn.execute(
                    f"SELECT name FROM sqlite_master "
                    f"WHERE type='index' AND tbl_name='{table_name}' AND name LIKE 'idx_%'"
                ).fetchall()

                existing_index_names = {row[0] for row in existing_indexes}

                # Get required indexes
                index_sqls = model_class.get_indexes_sql()

                if not index_sqls:
                    continue

                print(f"\n{table_name}:")

                for index_sql in index_sqls:
                    # Extract index name
                    match = re.search(
                        r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)',
                        index_sql,
                        re.IGNORECASE
                    )

                    if match:
                        index_name = match.group(1)

                        if index_name not in existing_index_names:
                            try:
                                conn.execute(index_sql)
                                print(f"  [OK] Created: {index_name}")
                            except sqlite3.OperationalError as e:
                                print(f"  ✗ Error creating {index_name}: {e}")
                        else:
                            print(f"  [OK] Exists: {index_name}")

            conn.commit()
            print("\nIndex verification complete!")

    def initialize_schema(self, model_classes: list[type]) -> None:
        """Initialize database schema including tables and indexes.

        Args:
            model_classes: List of model classes to initialize.
        """
        print("Initializing database schema...")

        # Create tables first
        for model_class in model_classes:
            table_name = model_class.get_table_name()
            create_sql = model_class.get_create_table_sql()

            with self.get_connection() as conn:
                conn.execute(create_sql)
                conn.commit()
                print(f"  [OK] Table: {table_name}")

        # Then ensure indexes exist
        self.ensure_indexes(model_classes)

        print("Schema initialization complete!")

    def get_index_info(self, table_name: str) -> list[dict[str, Any]]:
        """Get information about indexes for a table.

        Args:
            table_name: Name of the table to get index info for.

        Returns:
            List of dictionaries containing index information.
        """
        with self.get_connection() as conn:
            indexes = conn.execute(
                f"SELECT name, sql FROM sqlite_master "
                f"WHERE type='index' AND tbl_name='{table_name}' AND name LIKE 'idx_%' "
                f"ORDER BY name"
            ).fetchall()

            return [{"name": row[0], "sql": row[1]} for row in indexes]

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
        configured_db_path = current_app.config.get("SCRAPER_DB_PATH")
        if configured_db_path:
            g.db_config = DatabaseConfig(Path(configured_db_path))
        else:
            configured_database_path = current_app.config.get("DATABASE_PATH")
            g.db_config = (
                DatabaseConfig(Path(configured_database_path))
                if configured_database_path
                else DatabaseConfig()
            )

        initialized_paths = current_app.extensions.setdefault("initialized_db_schema_paths", set())
        db_path_str = str(g.db_config.db_path)
        if db_path_str not in initialized_paths:
            from ..models.file import File
            from ..models.job import Job
            from ..models.settings import Settings

            g.db_config.initialize_schema([Job, File, Settings])
            initialized_paths.add(db_path_str)

    return g.db_config


def get_db() -> sqlite3.Connection:
    """Get a database connection from Flask application context.

    Returns:
        SQLite database connection.

    Raises:
        RuntimeError: If called outside of an application context.
    """
    if "db" not in g:
        db_path = current_app.config.get("SCRAPER_DB_PATH") or current_app.config["DATABASE_PATH"]
        g.db = sqlite3.connect(
            db_path, detect_types=sqlite3.PARSE_DECLTYPES
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
