"""
File model for database entities.

This module provides the File model class for managing file records in the database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from .base import BaseModel


class File(BaseModel):
    """File model representing a file associated with a job.

    This model represents a file that has been downloaded or created
    as part of a job, including its metadata and relationship to the job.
    """

    # Table name for this model
    table_name = "files"

    # Primary key field name (different from base model)
    primary_key = "id"

    # Index definitions for performance
    indexes: ClassVar[list[dict[str, Any]]] = [
        {"columns": ["job_id"], "unique": False, "name": "idx_files_job_id"},
        {"columns": ["file_type"], "unique": False, "name": "idx_files_file_type"},
        {"columns": [("created_at", "DESC")], "unique": False, "name": "idx_files_created_at"},
        {"columns": ["job_id", "file_type"], "unique": False, "name": "idx_files_job_id_type"},
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the File model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        super().__init__(**kwargs)

        # File-specific fields
        self.id: int = kwargs.get("id")  # Auto-incremented primary key
        self.job_id: str = kwargs.get("job_id", "")
        self.file_path: str = kwargs.get("file_path", "")
        self.file_type: str = kwargs.get("file_type", "")
        self.file_size: int | None = kwargs.get("file_size")
        self.metadata_json: str | None = kwargs.get("metadata_json")
        # Note: files table doesn't have updated_at, only created_at
        # We'll handle this in the to_dict method

    @classmethod
    def get_create_table_sql(cls) -> str:
        """Get SQL statement to create the files table.

        Returns:
            SQL CREATE TABLE statement for files table.
        """
        return """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            metadata_json TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
        """

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert the file instance to a dictionary.

        Args:
            exclude: List of field names to exclude from the dictionary.

        Returns:
            Dictionary representation of the file instance.
        """
        exclude = exclude or []
        # Always exclude updated_at for files since it doesn't exist in the schema
        exclude.append("updated_at")

        result = {}

        # Include only the fields we want for files (matching the database schema)
        for attr_name in [
            "id",
            "job_id",
            "file_path",
            "file_type",
            "file_size",
            "metadata_json",
            "created_at",
        ]:
            if attr_name not in exclude:
                attr_value = getattr(self, attr_name, None)
                if attr_value is not None:
                    if isinstance(attr_value, datetime):
                        result[attr_name] = attr_value.isoformat()
                    elif attr_name == "id":
                        # Keep ID as integer for files
                        result[attr_name] = int(attr_value) if attr_value is not None else None
                    else:
                        result[attr_name] = attr_value

        return result

    def get_insert_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for inserting this file.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict(exclude=["primary_key", "table_name", "indexes"])
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        sql = f"""
        INSERT INTO files ({columns})
        VALUES ({placeholders})
        """

        return sql, values

    def get_update_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for updating this file.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict(exclude=["id", "created_at", "primary_key", "table_name", "indexes"])

        # Note: files table doesn't have updated_at, so we don't add it
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values())

        sql = f"""
        UPDATE files
        SET {set_clause}
        WHERE id = ?
        """

        return sql, values + (self.id,)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> File:
        """Create a file instance from a dictionary.

        Args:
            data: Dictionary containing field values.

        Returns:
            File instance populated with data from the dictionary.
        """
        # Convert ISO string timestamps back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        # Ensure id is properly typed as integer for files
        if "id" in data and isinstance(data["id"], str):
            try:
                data["id"] = int(data["id"])
            except ValueError:
                pass  # Keep original value if conversion fails

        return cls(**data)

    @classmethod
    def get_select_by_id_sql(cls) -> str:
        """Get SQL statement for selecting a file by ID.

        Returns:
            SQL SELECT statement.
        """
        return """
        SELECT * FROM files
        WHERE id = ?
        """

    @classmethod
    def get_delete_by_id_sql(cls) -> str:
        """Get SQL statement for deleting a file by ID.

        Returns:
            SQL DELETE statement.
        """
        return """
        DELETE FROM files
        WHERE id = ?
        """

    def get_metadata(self) -> dict[str, Any]:
        """Parse and return the metadata as a dictionary.

        Returns:
            Parsed metadata dictionary or empty dict if no metadata.
        """
        if not self.metadata_json:
            return {}

        try:
            import json

            return json.loads(self.metadata_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set the metadata from a dictionary.

        Args:
            metadata: Dictionary to serialize as JSON metadata.
        """
        import json

        self.metadata_json = json.dumps(metadata)
        # Note: files table doesn't have updated_at, so we don't call update_timestamp()

    def get_file_extension(self) -> str:
        """Get the file extension from the file path.

        Returns:
            File extension including the dot (e.g., '.mp4') or empty string.
        """
        import os

        return os.path.splitext(self.file_path)[1].lower()

    def get_filename(self) -> str:
        """Get the filename from the file path.

        Returns:
            Filename without directory path.
        """
        import os

        return os.path.basename(self.file_path)

    def is_video(self) -> bool:
        """Check if this file is a video file.

        Returns:
            True if the file type indicates video, False otherwise.
        """
        return self.file_type.lower() in ["video", "mp4", "avi", "mov", "mkv"]

    def is_audio(self) -> bool:
        """Check if this file is an audio file.

        Returns:
            True if the file type indicates audio, False otherwise.
        """
        return self.file_type.lower() in ["audio", "mp3", "wav", "aac", "ogg"]

    def is_image(self) -> bool:
        """Check if this file is an image file.

        Returns:
            True if the file type indicates image, False otherwise.
        """
        return self.file_type.lower() in ["image", "jpg", "jpeg", "png", "gif", "webp"]

    def is_metadata(self) -> bool:
        """Check if this file is a metadata file.

        Returns:
            True if the file type indicates metadata, False otherwise.
        """
        return self.file_type.lower() in ["metadata", "json", "info"]

    def format_file_size(self) -> str:
        """Format the file size in human-readable format.

        Returns:
            Formatted file size string (e.g., "1.5 MB").
        """
        if not self.file_size:
            return "Unknown"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0

        return f"{self.file_size:.1f} PB"

    def __repr__(self) -> str:
        """Return a string representation of the file."""
        return f"<File id={self.id} job_id={self.job_id} type={self.file_type}>"
