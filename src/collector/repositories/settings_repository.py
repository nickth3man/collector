"""
Settings repository for database operations.

This module provides the SettingsRepository class for all settings-related database operations.
"""

from __future__ import annotations

from typing import Any

from ..models.settings import Settings
from .base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    """Repository for settings-related database operations.

    This class provides all the necessary methods for creating, reading,
    updating, and deleting settings records in the database.
    """

    def __init__(self) -> None:
        """Initialize the settings repository."""
        super().__init__(Settings)

    def get_setting(self, key: str) -> Settings | None:
        """Get a setting by its key.

        Args:
            key: The key of the setting to retrieve.

        Returns:
            The settings instance if found, None otherwise.
        """
        return self.find_one_by(key=key)

    def get_setting_value(self, key: str, default_value: str = "") -> str:
        """Get the value of a setting by its key.

        Args:
            key: The key of the setting.
            default_value: Default value if the setting is not found.

        Returns:
            The setting value or default value.
        """
        setting = self.get_setting(key)
        return setting.value if setting else default_value

    def get_setting_bool(self, key: str, default_value: bool = False) -> bool:
        """Get a setting value as a boolean.

        Args:
            key: The key of the setting.
            default_value: Default boolean value if the setting is not found.

        Returns:
            The setting value as a boolean or default value.
        """
        setting = self.get_setting(key)
        if not setting:
            return default_value

        return setting.get_bool_value()

    def get_setting_int(self, key: str, default_value: int = 0) -> int:
        """Get a setting value as an integer.

        Args:
            key: The key of the setting.
            default_value: Default integer value if the setting is not found.

        Returns:
            The setting value as an integer or default value.
        """
        setting = self.get_setting(key)
        if not setting:
            return default_value

        return setting.get_int_value()

    def get_setting_float(self, key: str, default_value: float = 0.0) -> float:
        """Get a setting value as a float.

        Args:
            key: The key of the setting.
            default_value: Default float value if the setting is not found.

        Returns:
            The setting value as a float or default value.
        """
        setting = self.get_setting(key)
        if not setting:
            return default_value

        return setting.get_float_value()

    def set_setting(self, key: str, value: str) -> Settings:
        """Set a setting value.

        Args:
            key: The key of the setting.
            value: The value to set.

        Returns:
            The created or updated settings instance.
        """
        setting = self.get_setting(key)

        if setting:
            setting.value = value
            setting.update_timestamp()
            return self.update(setting)
        else:
            setting = Settings(key=key, value=value)
            return self.create(setting)

    def set_setting_bool(self, key: str, value: bool) -> Settings:
        """Set a setting value from a boolean.

        Args:
            key: The key of the setting.
            value: The boolean value to set.

        Returns:
            The created or updated settings instance.
        """
        setting = self.get_setting(key)

        if setting:
            setting.set_bool_value(value)
            return self.update(setting)
        else:
            setting = Settings(key=key)
            setting.set_bool_value(value)
            return self.create(setting)

    def set_setting_int(self, key: str, value: int) -> Settings:
        """Set a setting value from an integer.

        Args:
            key: The key of the setting.
            value: The integer value to set.

        Returns:
            The created or updated settings instance.
        """
        setting = self.get_setting(key)

        if setting:
            setting.set_int_value(value)
            return self.update(setting)
        else:
            setting = Settings(key=key)
            setting.set_int_value(value)
            return self.create(setting)

    def set_setting_float(self, key: str, value: float) -> Settings:
        """Set a setting value from a float.

        Args:
            key: The key of the setting.
            value: The float value to set.

        Returns:
            The created or updated settings instance.
        """
        setting = self.get_setting(key)

        if setting:
            setting.set_float_value(value)
            return self.update(setting)
        else:
            setting = Settings(key=key)
            setting.set_float_value(value)
            return self.create(setting)

    def delete_setting(self, key: str) -> bool:
        """Delete a setting by its key.

        Args:
            key: The key of the setting to delete.

        Returns:
            True if the setting was deleted, False otherwise.
        """
        return self.delete_by_id(key)

    def get_all_settings(self) -> dict[str, str]:
        """Get all settings as a dictionary.

        Returns:
            Dictionary of all settings (key -> value).
        """
        settings_list = self.get_all()
        return {setting.key: setting.value for setting in settings_list}

    def get_settings_by_prefix(self, prefix: str) -> dict[str, str]:
        """Get settings whose keys start with a prefix.

        Args:
            prefix: The prefix to match against setting keys.

        Returns:
            Dictionary of matching settings (key -> value).
        """
        sql = """
        SELECT * FROM settings
        WHERE key LIKE ?
        ORDER BY key
        """

        results = self.execute_custom_query(sql, (f"{prefix}%",))
        settings = [Settings.from_dict(result) for result in results]

        return {setting.key: setting.value for setting in settings}

    def batch_set_settings(self, settings_dict: dict[str, str]) -> list[Settings]:
        """Set multiple settings at once.

        Args:
            settings_dict: Dictionary of settings to set (key -> value).

        Returns:
            List of created or updated settings instances.
        """
        result = []

        for key, value in settings_dict.items():
            setting = self.set_setting(key, value)
            result.append(setting)

        return result

    def batch_delete_settings(self, keys: list[str]) -> int:
        """Delete multiple settings at once.

        Args:
            keys: List of setting keys to delete.

        Returns:
            Number of settings deleted.
        """
        if not keys:
            return 0

        placeholders = ", ".join(["?" for _ in keys])
        sql = f"""
        DELETE FROM settings
        WHERE key IN ({placeholders})
        """

        return self.execute_custom_update(sql, tuple(keys))

    def export_settings(self, include_updated_at: bool = False) -> dict[str, Any]:
        """Export all settings as a dictionary.

        Args:
            include_updated_at: Whether to include the updated_at timestamp.

        Returns:
            Dictionary containing all settings.
        """
        settings_list = self.get_all()

        if include_updated_at:
            return {
                setting.key: {
                    "value": setting.value,
                    "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
                }
                for setting in settings_list
            }
        else:
            return {setting.key: setting.value for setting in settings_list}

    def import_settings(
        self, settings_data: dict[str, Any], overwrite: bool = True
    ) -> list[Settings]:
        """Import settings from a dictionary.

        Args:
            settings_data: Dictionary containing settings data.
            overwrite: Whether to overwrite existing settings.

        Returns:
            List of created or updated settings instances.
        """
        result = []

        for key, value in settings_data.items():
            # Handle different data formats
            if isinstance(value, dict) and "value" in value:
                # Format with value and metadata
                setting_value = value["value"]
            else:
                # Simple key-value format
                setting_value = str(value)

            # Check if setting exists and whether to overwrite
            existing = self.get_setting(key)
            if existing and not overwrite:
                continue

            setting = self.set_setting(key, setting_value)
            result.append(setting)

        return result

    def get_setting_keys(self) -> list[str]:
        """Get all setting keys.

        Returns:
            List of all setting keys.
        """
        sql = "SELECT key FROM settings ORDER BY key"

        results = self.execute_custom_query(sql)
        return [result["key"] for result in results]

    def count_settings(self) -> int:
        """Count the total number of settings.

        Returns:
            Number of settings in the database.
        """
        return self.count()
