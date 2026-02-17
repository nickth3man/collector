"""
File repository for database operations.

This module provides the FileRepository class for all file-related database operations.
"""

from __future__ import annotations

from typing import Any

from ..models.file import File
from .base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for file-related database operations.

    This class provides all the necessary methods for creating, reading,
    updating, and deleting file records in the database.
    """

    def __init__(self) -> None:
        """Initialize the file repository."""
        super().__init__(File)

    def create(self, model_instance: File) -> File:
        """Create a new file record in the database.

        Args:
            model_instance: The file instance to create.

        Returns:
            The created file instance with updated ID.
        """
        db_config = self._get_db_config()
        sql, params = model_instance.get_insert_sql()

        with db_config.get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()

            # Update the model with the generated ID if it wasn't set
            if not model_instance.id:
                model_instance.id = cursor.lastrowid if cursor.lastrowid else model_instance.id

            # Note: Files don't have updated_at, so we don't call update_timestamp()
            return model_instance

    def get_by_id_int(self, file_id: int) -> File | None:
        """Get a file by its integer ID.

        Args:
            file_id: The integer ID of the file to retrieve.

        Returns:
            The file instance if found, None otherwise.
        """
        db_config = self._get_db_config()
        sql = self.model_class.get_select_by_id_sql()

        results = db_config.execute_query(sql, (file_id,))

        if results:
            return self.model_class.from_dict(results[0])
        return None

    def create_file(
        self,
        job_id: str,
        file_path: str,
        file_type: str,
        file_size: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> File:
        """Create a new file record.

        Args:
            job_id: The ID of the associated job.
            file_path: The path to the file.
            file_type: The type of file (video, audio, image, metadata).
            file_size: Optional size of the file in bytes.
            metadata: Optional metadata dictionary.

        Returns:
            The created file instance.
        """
        metadata_json = None
        if metadata:
            import json

            metadata_json = json.dumps(metadata)

        file = File(
            job_id=job_id,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            metadata_json=metadata_json,
        )
        return self.create(file)

    def get_job_files(self, job_id: str) -> list[File]:
        """Get all files associated with a job.

        Args:
            job_id: The ID of the job.

        Returns:
            List of file instances for the specified job.
        """
        sql = """
        SELECT * FROM files
        WHERE job_id = ?
        ORDER BY created_at ASC
        """

        results = self.execute_custom_query(sql, (job_id,))
        return [File.from_dict(result) for result in results]

    def get_files_by_type(self, file_type: str) -> list[File]:
        """Get files by their type.

        Args:
            file_type: The file type to filter by.

        Returns:
            List of file instances with the specified type.
        """
        return self.find_by(file_type=file_type)

    def get_job_files_by_type(self, job_id: str, file_type: str) -> list[File]:
        """Get files for a specific job filtered by type.

        Args:
            job_id: The ID of the job.
            file_type: The file type to filter by.

        Returns:
            List of file instances for the specified job and type.
        """
        sql = """
        SELECT * FROM files
        WHERE job_id = ? AND file_type = ?
        ORDER BY created_at ASC
        """

        results = self.execute_custom_query(sql, (job_id, file_type))
        return [File.from_dict(result) for result in results]

    def get_video_files(self, job_id: str | None = None) -> list[File]:
        """Get video files, optionally filtered by job.

        Args:
            job_id: Optional job ID to filter by.

        Returns:
            List of video file instances.
        """
        if job_id:
            return self.get_job_files_by_type(job_id, "video")

        return self.get_files_by_type("video")

    def get_audio_files(self, job_id: str | None = None) -> list[File]:
        """Get audio files, optionally filtered by job.

        Args:
            job_id: Optional job ID to filter by.

        Returns:
            List of audio file instances.
        """
        if job_id:
            return self.get_job_files_by_type(job_id, "audio")

        return self.get_files_by_type("audio")

    def get_image_files(self, job_id: str | None = None) -> list[File]:
        """Get image files, optionally filtered by job.

        Args:
            job_id: Optional job ID to filter by.

        Returns:
            List of image file instances.
        """
        if job_id:
            return self.get_job_files_by_type(job_id, "image")

        return self.get_files_by_type("image")

    def get_metadata_files(self, job_id: str | None = None) -> list[File]:
        """Get metadata files, optionally filtered by job.

        Args:
            job_id: Optional job ID to filter by.

        Returns:
            List of metadata file instances.
        """
        if job_id:
            return self.get_job_files_by_type(job_id, "metadata")

        return self.get_files_by_type("metadata")

    def update_file_size(self, file_id: int, file_size: int) -> bool:
        """Update the size of a file.

        Args:
            file_id: The ID of the file to update.
            file_size: The new file size in bytes.

        Returns:
            True if the file was updated, False otherwise.
        """
        file = self.get_by_id_int(file_id)
        if not file:
            return False

        file.file_size = file_size
        self.update(file)
        return True

    def update_file_metadata(self, file_id: int, metadata: dict[str, Any]) -> bool:
        """Update the metadata of a file.

        Args:
            file_id: The ID of the file to update.
            metadata: The new metadata dictionary.

        Returns:
            True if the file was updated, False otherwise.
        """
        file = self.get_by_id_int(file_id)
        if not file:
            return False

        file.set_metadata(metadata)
        self.update(file)
        return True

    def delete_job_files(self, job_id: str) -> int:
        """Delete all files associated with a job.

        Args:
            job_id: The ID of the job whose files should be deleted.

        Returns:
            Number of files deleted.
        """
        sql = """
        DELETE FROM files
        WHERE job_id = ?
        """

        return self.execute_custom_update(sql, (job_id,))

    def get_file_statistics(self) -> dict[str, Any]:
        """Get statistics about files in the system.

        Returns:
            Dictionary with file statistics.
        """
        stats = {}

        # Count by type
        type_sql = """
        SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
        FROM files
        GROUP BY file_type
        """

        type_results = self.execute_custom_query(type_sql)
        stats["by_type"] = {}
        total_size = 0

        for result in type_results:
            file_type = result["file_type"]
            stats["by_type"][file_type] = {
                "count": result["count"],
                "total_size": result["total_size"] or 0,
            }
            total_size += result["total_size"] or 0

        # Total files and size
        stats["total_files"] = self.count()
        stats["total_size"] = total_size

        # Files with metadata
        metadata_sql = """
        SELECT COUNT(*) as count
        FROM files
        WHERE metadata_json IS NOT NULL AND metadata_json != ''
        """

        metadata_result = self.execute_custom_query(metadata_sql)
        stats["files_with_metadata"] = metadata_result[0]["count"] if metadata_result else 0

        return stats

    def get_orphaned_files(self) -> list[File]:
        """Get files that don't have an associated job.

        Returns:
            List of orphaned file instances.
        """
        sql = """
        SELECT f.* FROM files f
        LEFT JOIN jobs j ON f.job_id = j.id
        WHERE j.id IS NULL
        """

        results = self.execute_custom_query(sql)
        return [File.from_dict(result) for result in results]

    def cleanup_orphaned_files(self) -> int:
        """Delete files that don't have an associated job.

        Returns:
            Number of files deleted.
        """
        sql = """
        DELETE FROM files
        WHERE job_id NOT IN (SELECT id FROM jobs)
        """

        return self.execute_custom_update(sql)

    def find_by_path_pattern(self, pattern: str) -> list[File]:
        """Find files whose paths match a pattern.

        Args:
            pattern: SQL LIKE pattern to match against file paths.

        Returns:
            List of matching file instances.
        """
        sql = """
        SELECT * FROM files
        WHERE file_path LIKE ?
        ORDER BY created_at DESC
        """

        results = self.execute_custom_query(sql, (pattern,))
        return [File.from_dict(result) for result in results]

    def get_files_by_size_range(
        self, min_size: int | None = None, max_size: int | None = None
    ) -> list[File]:
        """Get files within a size range.

        Args:
            min_size: Minimum file size in bytes (inclusive).
            max_size: Maximum file size in bytes (inclusive).

        Returns:
            List of file instances within the size range.
        """
        conditions = []
        params = []

        if min_size is not None:
            conditions.append("file_size >= ?")
            params.append(min_size)

        if max_size is not None:
            conditions.append("file_size <= ?")
            params.append(max_size)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
        SELECT * FROM files
        {where_clause}
        ORDER BY file_size DESC
        """

        results = self.execute_custom_query(sql, tuple(params))
        return [File.from_dict(result) for result in results]
