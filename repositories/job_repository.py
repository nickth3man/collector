"""
Job repository for database operations.

This module provides the JobRepository class for all job-related database operations.
"""

from __future__ import annotations

from typing import Any

from models.job import Job
from repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for job-related database operations.

    This class provides all the necessary methods for creating, reading,
    updating, and deleting job records in the database.
    """

    def __init__(self) -> None:
        """Initialize the job repository."""
        super().__init__(Job)

    def create_job(self, url: str, platform: str, title: str | None = None) -> Job:
        """Create a new job.

        Args:
            url: The URL to scrape.
            platform: The platform (youtube, instagram).
            title: Optional title for the job.

        Returns:
            The created job instance.
        """
        job = Job(url=url, platform=platform, status="pending", title=title)
        return self.create(job)

    def get_active_jobs(self) -> list[Job]:
        """Get all active jobs (pending, running, or cancelling).

        Returns:
            List of active job instances.
        """
        return self.find_by(status__in=["pending", "running", "cancelling"])

    def get_jobs_by_status(self, status: str) -> list[Job]:
        """Get jobs by their status.

        Args:
            status: The status to filter by.

        Returns:
            List of job instances with the specified status.
        """
        return self.find_by(status=status)

    def get_jobs_by_platform(self, platform: str) -> list[Job]:
        """Get jobs by their platform.

        Args:
            platform: The platform to filter by.

        Returns:
            List of job instances for the specified platform.
        """
        return self.find_by(platform=platform)

    def get_recent_jobs(self, limit: int = 10) -> list[Job]:
        """Get the most recent jobs.

        Args:
            limit: Maximum number of jobs to return.

        Returns:
            List of recent job instances ordered by creation date.
        """
        sql = """
        SELECT * FROM jobs
        ORDER BY created_at DESC
        LIMIT ?
        """

        results = self.execute_custom_query(sql, (limit,))
        return [Job.from_dict(result) for result in results]

    def get_job_with_files(self, job_id: str) -> dict[str, Any] | None:
        """Get a job along with its associated files.

        Args:
            job_id: The ID of the job to retrieve.

        Returns:
            Dictionary containing job and files, or None if not found.
        """
        job = self.get_by_id(job_id)
        if not job:
            return None

        # Get associated files
        sql = """
        SELECT * FROM files
        WHERE job_id = ?
        ORDER BY created_at ASC
        """

        file_results = self.execute_custom_query(sql, (job_id,))

        # Import here to avoid circular imports
        from models.file import File

        files = [File.from_dict(file_data) for file_data in file_results]

        return {"job": job, "files": files}

    def update_job_status(self, job_id: str, status: str, error_message: str | None = None) -> bool:
        """Update the status of a job.

        Args:
            job_id: The ID of the job to update.
            status: The new status.
            error_message: Optional error message for failed jobs.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.status = status
        if error_message:
            job.error_message = error_message

        self.update(job)
        return True

    def update_job_progress(
        self, job_id: str, progress: int, current_operation: str | None = None
    ) -> bool:
        """Update the progress of a job.

        Args:
            job_id: The ID of the job to update.
            progress: The progress percentage (0-100).
            current_operation: Optional description of the current operation.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.update_progress(progress, current_operation)
        self.update(job)
        return True

    def increment_job_retry(self, job_id: str) -> bool:
        """Increment the retry count for a job.

        Args:
            job_id: The ID of the job to update.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.increment_retry()
        self.update(job)
        return True

    def add_bytes_downloaded(self, job_id: str, bytes_count: int) -> bool:
        """Add to the total bytes downloaded for a job.

        Args:
            job_id: The ID of the job to update.
            bytes_count: Number of bytes to add to the total.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.add_bytes_downloaded(bytes_count)
        self.update(job)
        return True

    def complete_job(self, job_id: str) -> bool:
        """Mark a job as completed.

        Args:
            job_id: The ID of the job to complete.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.mark_completed()
        self.update(job)
        return True

    def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark a job as failed with an error message.

        Args:
            job_id: The ID of the job to fail.
            error_message: The error message describing the failure.

        Returns:
            True if the job was updated, False otherwise.
        """
        job = self.get_by_id(job_id)
        if not job:
            return False

        job.mark_failed(error_message)
        self.update(job)
        return True

    def get_job_statistics(self) -> dict[str, int]:
        """Get statistics about jobs in the system.

        Returns:
            Dictionary with job statistics.
        """
        stats = {}

        # Count by status
        status_sql = """
        SELECT status, COUNT(*) as count
        FROM jobs
        GROUP BY status
        """

        status_results = self.execute_custom_query(status_sql)
        for result in status_results:
            stats[f"status_{result['status']}"] = result["count"]

        # Total jobs
        stats["total_jobs"] = self.count()

        # Jobs with files
        files_sql = """
        SELECT COUNT(DISTINCT job_id) as count
        FROM files
        """

        files_result = self.execute_custom_query(files_sql)
        stats["jobs_with_files"] = files_result[0]["count"] if files_result else 0

        return stats

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Delete jobs older than the specified number of days.

        Args:
            days: Number of days to keep jobs.

        Returns:
            Number of jobs deleted.
        """
        sql = f"""
        DELETE FROM jobs
        WHERE created_at < datetime('now', '-{days} days')
        AND status IN ('completed', 'failed', 'cancelled')
        """

        return self.execute_custom_update(sql)

    def find_by(self, **kwargs: Any) -> list[Job]:
        """Find jobs matching the given criteria with enhanced filtering.

        Args:
            **kwargs: Field names and values to match. Supports special
                     suffixes like '__in' for IN clauses.

        Returns:
            List of job instances matching the criteria.
        """
        if not kwargs:
            return self.get_all()

        table_name = self.model_class.get_table_name()
        where_clauses = []
        params = []

        for key, value in kwargs.items():
            if key.endswith("__in"):
                # Handle IN clause
                field_name = key[:-4]  # Remove '__in' suffix
                placeholders = ", ".join(["?" for _ in value])
                where_clauses.append(f"{field_name} IN ({placeholders})")
                params.extend(value)
            else:
                # Regular equality clause
                where_clauses.append(f"{key} = ?")
                params.append(value)

        sql = f"SELECT * FROM {table_name} WHERE {' AND '.join(where_clauses)}"

        results = self.execute_custom_query(sql, tuple(params))
        return [Job.from_dict(result) for result in results]
