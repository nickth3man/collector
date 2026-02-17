"""
Job model for database entities.

This module provides the Job model class for managing job records in the database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from .base import BaseModel


class Job(BaseModel):
    """Job model representing a download job.

    This model represents a job in the system, including its status, progress,
    and metadata about the download operation.
    """

    # Table name for this model
    table_name = "jobs"

    # Index definitions for performance
    indexes: ClassVar[list[dict[str, Any]]] = [
        {
            "columns": ["status"],
            "unique": False,
            "name": "idx_jobs_status"
        },
        {
            "columns": ["platform"],
            "unique": False,
            "name": "idx_jobs_platform"
        },
        {
            "columns": [("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_created_at"
        },
        {
            "columns": ["status", ("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_status_created"
        }
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Job model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        super().__init__(**kwargs)

        # Job-specific fields
        self.url: str = kwargs.get("url", "")
        self.platform: str = kwargs.get("platform", "")
        self.status: str = kwargs.get("status", "pending")
        self.title: str | None = kwargs.get("title")
        self.progress: int = kwargs.get("progress", 0)
        self.current_operation: str | None = kwargs.get("current_operation")
        self.error_message: str | None = kwargs.get("error_message")
        self.retry_count: int = kwargs.get("retry_count", 0)
        self.bytes_downloaded: int = kwargs.get("bytes_downloaded", 0)
        self.completed_at: datetime | None = kwargs.get("completed_at")

    @classmethod
    def get_create_table_sql(cls) -> str:
        """Get SQL statement to create the jobs table.

        Returns:
            SQL CREATE TABLE statement for jobs table.
        """
        return """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT NOT NULL,
            title TEXT,
            progress INTEGER DEFAULT 0,
            current_operation TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            bytes_downloaded INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
            updated_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
            completed_at TIMESTAMP
        )
        """

    def get_insert_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for inserting this job.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict(exclude=["primary_key", "table_name", "indexes"])
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        sql = f"""
        INSERT INTO jobs ({columns})
        VALUES ({placeholders})
        """

        return sql, values

    def get_update_sql(self) -> tuple[str, tuple[Any, ...]]:
        """Get SQL statement and parameters for updating this job.

        Returns:
            Tuple of (SQL statement, parameters).
        """
        data = self.to_dict(exclude=["id", "created_at", "primary_key", "table_name", "indexes"])

        # Update the timestamp
        data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values())

        sql = f"""
        UPDATE jobs
        SET {set_clause}
        WHERE id = ?
        """

        return sql, values + (self.id,)

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """Convert the job instance to a dictionary.

        Args:
            exclude: List of field names to exclude from the dictionary.

        Returns:
            Dictionary representation of the job instance.
        """
        exclude = exclude or []
        result = super().to_dict(exclude=exclude)

        # Handle datetime serialization for completed_at
        if "completed_at" in result and result["completed_at"]:
            if isinstance(result["completed_at"], datetime):
                result["completed_at"] = result["completed_at"].isoformat()

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Create a job instance from a dictionary.

        Args:
            data: Dictionary containing field values.

        Returns:
            Job instance populated with data from the dictionary.
        """
        # Convert ISO string timestamps back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        if (
            "completed_at" in data
            and data["completed_at"]
            and isinstance(data["completed_at"], str)
        ):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])

        return cls(**data)

    def mark_completed(self) -> None:
        """Mark the job as completed with current timestamp."""
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.utcnow()
        self.update_timestamp()

    def mark_failed(self, error_message: str) -> None:
        """Mark the job as failed with an error message.

        Args:
            error_message: The error message describing the failure.
        """
        self.status = "failed"
        self.error_message = error_message
        self.update_timestamp()

    def increment_retry(self) -> None:
        """Increment the retry count for the job."""
        self.retry_count += 1
        self.update_timestamp()

    def update_progress(self, progress: int, operation: str | None = None) -> None:
        """Update the progress of the job.

        Args:
            progress: The progress percentage (0-100).
            operation: Optional description of the current operation.
        """
        self.progress = max(0, min(100, progress))  # Ensure progress is within bounds
        if operation:
            self.current_operation = operation
        self.update_timestamp()

    def add_bytes_downloaded(self, bytes_count: int) -> None:
        """Add to the total bytes downloaded.

        Args:
            bytes_count: Number of bytes to add to the total.
        """
        self.bytes_downloaded += bytes_count
        self.update_timestamp()

    def __repr__(self) -> str:
        """Return a string representation of the job."""
        return f"<Job id={self.id} status={self.status} platform={self.platform}>"
