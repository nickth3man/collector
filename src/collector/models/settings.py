"""
Settings model for database entities.

This module provides the Settings model class for managing application settings in the database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

from .base import BaseModel


class Settings(BaseModel):
    """Settings model representing application configuration settings.

    This model represents a key-value setting stored in the database,
    allowing for dynamic configuration management.
    """

    # Table name for this model
    table_name = "settings"

    # Primary key field name (different from base model)
    primary_key = "key"

    # No indexes needed for settings table (primary key is sufficient)
    indexes: ClassVar[list[dict[str, Any]]] = []

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Settings model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        # Settings-specific fields
        self.key: str = kwargs.get("key", "")
        self.value: str = kwargs.get("value", "")
        self.updated_at: datetime = kwargs.get("updated_at", datetime.now(timezone.utc))

    @classmethod
    def get_create_table_sql(cls) -> str:
        """Get SQL statement to create the settings table.

        Returns:
            SQL CREATE TABLE statement for settings table.
        """
        return """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT (datetime('now'))
        )
        """

    def get_insert_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for inserting this setting.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        sql = f"""
        INSERT INTO settings ({columns})
        VALUES ({placeholders})
        """

        return sql, values

    def get_update_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for updating this setting.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict(exclude=["key"])

        # Update the timestamp
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values())

        sql = f"""
        UPDATE settings
        SET {set_clause}
        WHERE key = ?
        """

        return sql, values + (self.key,)

    @classmethod
    def get_select_by_id_sql(cls) -> str:
        """Get SQL statement for selecting a setting by key.

        Returns:
            SQL SELECT statement.
        """
        return """
        SELECT * FROM settings
        WHERE key = ?
        """

    @classmethod
    def get_delete_by_id_sql(cls) -> str:
        """Get SQL statement for deleting a setting by key.

        Returns:
            SQL DELETE statement.
        """
        return """
        DELETE FROM settings
        WHERE key = ?
        """

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert the settings instance to a dictionary.

        Args:
            exclude: List of field names to exclude from the dictionary.

        Returns:
            Dictionary representation of the settings instance.
        """
        exclude = exclude or []
        result = {}

        # Include only the fields we want for settings
        for attr_name in ["key", "value", "updated_at"]:
            if attr_name not in exclude:
                attr_value = getattr(self, attr_name, None)
                if attr_value is not None:
                    if isinstance(attr_value, datetime):
                        result[attr_name] = attr_value.isoformat()
                    else:
                        result[attr_name] = attr_value

        return result

    def get_bool_value(self) -> bool:
        """Get the value as a boolean.

        Returns:
            True if the value represents a truthy value, False otherwise.
        """
        return self.value.lower() in ("true", "1", "yes", "on", "enabled")

    def get_int_value(self) -> int:
        """Get the value as an integer.

        Returns:
            Integer value or 0 if conversion fails.
        """
        try:
            return int(self.value)
        except (ValueError, TypeError):
            return 0

    def get_float_value(self) -> float:
        """Get the value as a float.

        Returns:
            Float value or 0.0 if conversion fails.
        """
        try:
            return float(self.value)
        except (ValueError, TypeError):
            return 0.0

    def set_bool_value(self, value: bool) -> None:
        """Set the value from a boolean.

        Args:
            value: Boolean value to set.
        """
        self.value = "true" if value else "false"
        self.update_timestamp()

    def set_int_value(self, value: int) -> None:
        """Set the value from an integer.

        Args:
            value: Integer value to set.
        """
        self.value = str(value)
        self.update_timestamp()

    def set_float_value(self, value: float) -> None:
        """Set the value from a float.

        Args:
            value: Float value to set.
        """
        self.value = str(value)
        self.update_timestamp()

    def __repr__(self) -> str:
        """Return a string representation of the settings."""
        return f"<Settings key={self.key} value={self.value}>"
