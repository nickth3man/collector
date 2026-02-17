"""
Base repository class for data access operations.

This module provides a base repository class with common CRUD operations
and database connection handling.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from ..config.database import DatabaseConfig, get_db_config
from ..models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations.

    This class provides basic CRUD (Create, Read, Update, Delete) operations
    for database entities, along with database connection handling.
    """

    def __init__(self, model_class: type[T], db_config: DatabaseConfig | None = None) -> None:
        """Initialize the repository with a model class and database configuration.

        Args:
            model_class: The model class this repository manages.
            db_config: Database configuration. If None, uses Flask application context.
        """
        self.model_class = model_class
        self.db_config = db_config

    def _get_db_config(self) -> DatabaseConfig:
        """Get database configuration from Flask application context or instance.

        Returns:
            DatabaseConfig instance.
        """
        if self.db_config:
            return self.db_config
        return get_db_config()

    def create(self, model_instance: T) -> T:
        """Create a new record in the database.

        Args:
            model_instance: The model instance to create.

        Returns:
            The created model instance with updated ID.
        """
        db_config = self._get_db_config()
        sql, params = model_instance.get_insert_sql()

        with db_config.get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()

            # Update the model with the generated ID if it wasn't set
            if not model_instance.id:
                model_instance.id = str(cursor.lastrowid) if cursor.lastrowid else model_instance.id

            model_instance.update_timestamp()
            return model_instance

    def get_by_id(self, model_id: str) -> T | None:
        """Get a record by its ID.

        Args:
            model_id: The ID of the record to retrieve.

        Returns:
            The model instance if found, None otherwise.
        """
        db_config = self._get_db_config()
        sql = self.model_class.get_select_by_id_sql()

        results = db_config.execute_query(sql, (model_id,))

        if results:
            return self.model_class.from_dict(results[0])
        return None

    def get_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """Get all records from the table.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of model instances.
        """
        table_name = self.model_class.get_table_name()
        sql = f"SELECT * FROM {table_name}"
        params: tuple = ()

        if limit is not None:
            sql += f" LIMIT {limit}"
            if offset is not None:
                sql += f" OFFSET {offset}"

        db_config = self._get_db_config()
        results = db_config.execute_query(sql, params)

        return [self.model_class.from_dict(result) for result in results]

    def update(self, model_instance: T) -> T:
        """Update an existing record in the database.

        Args:
            model_instance: The model instance to update.

        Returns:
            The updated model instance.
        """
        db_config = self._get_db_config()
        sql, params = model_instance.get_update_sql()

        db_config.execute_update(sql, params)
        model_instance.update_timestamp()

        return model_instance

    def delete(self, model_instance: T) -> bool:
        """Delete a record from the database.

        Args:
            model_instance: The model instance to delete.

        Returns:
            True if the record was deleted, False otherwise.
        """
        return self.delete_by_id(getattr(model_instance, model_instance.primary_key))

    def delete_by_id(self, model_id: str) -> bool:
        """Delete a record by its ID.

        Args:
            model_id: The ID of the record to delete.

        Returns:
            True if the record was deleted, False otherwise.
        """
        db_config = self._get_db_config()
        sql = self.model_class.get_delete_by_id_sql()

        rows_affected = db_config.execute_update(sql, (model_id,))
        return rows_affected > 0

    def count(self) -> int:
        """Count all records in the table.

        Returns:
            Number of records in the table.
        """
        table_name = self.model_class.get_table_name()
        sql = f"SELECT COUNT(*) as count FROM {table_name}"

        db_config = self._get_db_config()
        results = db_config.execute_query(sql)

        return results[0]["count"] if results else 0

    def exists(self, model_id: str) -> bool:
        """Check if a record with the given ID exists.

        Args:
            model_id: The ID to check for existence.

        Returns:
            True if the record exists, False otherwise.
        """
        return self.get_by_id(model_id) is not None

    def find_by(self, **kwargs: Any) -> list[T]:
        """Find records matching the given criteria.

        Args:
            **kwargs: Field names and values to match.

        Returns:
            List of model instances matching the criteria.
        """
        if not kwargs:
            return self.get_all()

        table_name = self.model_class.get_table_name()
        where_clauses = []
        params = []

        for key, value in kwargs.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)

        sql = f"SELECT * FROM {table_name} WHERE {' AND '.join(where_clauses)}"

        db_config = self._get_db_config()
        results = db_config.execute_query(sql, tuple(params))

        return [self.model_class.from_dict(result) for result in results]

    def find_one_by(self, **kwargs: Any) -> T | None:
        """Find the first record matching the given criteria.

        Args:
            **kwargs: Field names and values to match.

        Returns:
            First model instance matching the criteria, or None if not found.
        """
        results = self.find_by(**kwargs)
        return results[0] if results else None

    def create_table(self) -> None:
        """Create the table for this model if it doesn't exist."""
        db_config = self._get_db_config()
        sql = self.model_class.get_create_table_sql()

        with db_config.get_connection() as conn:
            conn.execute(sql)
            conn.commit()

    def execute_custom_query(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute a custom SQL query.

        Args:
            query: The SQL query to execute.
            params: Parameters for the query.

        Returns:
            List of dictionaries representing the result rows.
        """
        db_config = self._get_db_config()
        return db_config.execute_query(query, params)

    def execute_custom_update(self, query: str, params: tuple = ()) -> int:
        """Execute a custom SQL update/insert/delete query.

        Args:
            query: The SQL query to execute.
            params: Parameters for the query.

        Returns:
            Number of rows affected.
        """
        db_config = self._get_db_config()
        return db_config.execute_update(query, params)
