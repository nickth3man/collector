"""
Base model class for database entities.

This module provides a base model class with common functionality for all database entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, TypeVar
from uuid import uuid4

T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """Base model class with common functionality for all database entities.

    This class provides common fields and methods that are shared across all
    database entities, including id, timestamps, and basic serialization.
    """

    # Table name for the model (to be overridden by subclasses)
    table_name: ClassVar[str] = ""

    # Primary key field name
    primary_key: ClassVar[str] = "id"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        self.id: str = kwargs.get("id", str(uuid4()))
        self.created_at: datetime = kwargs.get("created_at", datetime.utcnow())
        self.updated_at: datetime = kwargs.get("updated_at", datetime.utcnow())

        # Set any additional attributes passed in kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and not callable(getattr(self, key)):
                setattr(self, key, value)

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert the model instance to a dictionary.

        Args:
            exclude: List of field names to exclude from the dictionary.

        Returns:
            Dictionary representation of the model instance.
        """
        exclude = exclude or []
        result = {}

        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                attr_value = getattr(self, attr_name)
                if not callable(attr_value) and attr_name not in exclude:
                    if isinstance(attr_value, datetime):
                        result[attr_name] = attr_value.isoformat()
                    else:
                        result[attr_name] = attr_value

        return result

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create a model instance from a dictionary.

        Args:
            data: Dictionary containing field values.

        Returns:
            Model instance populated with data from the dictionary.
        """
        # Convert ISO string timestamps back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        class_name = self.__class__.__name__
        return f"<{class_name} id={self.id}>"

    def __eq__(self, other: object) -> bool:
        """Check equality based on primary key."""
        if not isinstance(other, BaseModel):
            return False
        return getattr(self, self.primary_key) == getattr(other, other.primary_key)

    def __hash__(self) -> int:
        """Return hash based on primary key."""
        return hash(getattr(self, self.primary_key))

    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model.

        Returns:
            Table name for the model.
        """
        return cls.table_name or cls.__name__.lower() + "s"

    @classmethod
    def get_create_table_sql(cls) -> str:
        """Get SQL statement to create the table for this model.

        Returns:
            SQL CREATE TABLE statement.
        """
        table_name = cls.get_table_name()
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {cls.primary_key} TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """

    def get_insert_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for inserting this model.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        table_name = self.get_table_name()
        data = self.to_dict(exclude=[self.primary_key])

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        sql = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        """

        return sql, values

    def get_update_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for updating this model.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        table_name = self.get_table_name()
        data = self.to_dict(exclude=[self.primary_key, "created_at"])

        # Update the timestamp
        data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values())
        primary_key_value = getattr(self, self.primary_key)

        sql = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {self.primary_key} = ?
        """

        return sql, values + (primary_key_value,)

    @classmethod
    def get_select_by_id_sql(cls) -> str:
        """Get SQL statement for selecting a model by ID.

        Returns:
            SQL SELECT statement.
        """
        table_name = cls.get_table_name()
        return f"""
        SELECT * FROM {table_name}
        WHERE {cls.primary_key} = ?
        """

    @classmethod
    def get_delete_by_id_sql(cls) -> str:
        """Get SQL statement for deleting a model by ID.

        Returns:
            SQL DELETE statement.
        """
        table_name = cls.get_table_name()
        return f"""
        DELETE FROM {table_name}
        WHERE {cls.primary_key} = ?
        """
