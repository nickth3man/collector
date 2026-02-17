"""Job service for managing job lifecycle and operations.

This service encapsulates all job-related business logic and orchestrates
operations with the repository layer.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..config.settings import (
    STATUS_CANCELLED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
)
from ..models.job import Job
from ..repositories.file_repository import FileRepository
from ..repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing job lifecycle and operations."""

    def __init__(
        self,
        job_repository: JobRepository | None = None,
        file_repository: FileRepository | None = None,
        download_dir: Path | None = None,
    ) -> None:
        """Initialize the job service.

        Args:
            job_repository: Repository for job operations
            file_repository: Repository for file operations
            download_dir: Directory where downloaded files are stored
        """
        self.job_repository = job_repository or JobRepository()
        self.file_repository = file_repository or FileRepository()
        self.download_dir = download_dir

    def create_job(self, url: str, platform: str, title: str | None = None) -> Job:
        """Create a new job.

        Args:
            url: The URL to scrape
            platform: Platform identifier ('youtube' or 'instagram')
            title: Optional title for the job

        Returns:
            The created job instance
        """
        logger.info("Creating new job for URL: %s, platform: %s", url, platform)
        return self.job_repository.create_job(url, platform, title)

    def update_job(self, job_id: str, **fields: Any) -> bool:
        """Update job fields with safe/allowed field enforcement.

        Args:
            job_id: Job ID to update
            **fields: Fields to update (must be in allowed list)

        Returns:
            True if updated successfully, False if job not found or no valid fields
        """
        # Define allowed fields for updates (prevents accidental updates of sensitive fields)
        allowed_fields = {
            "status",
            "title",
            "progress",
            "current_operation",
            "error_message",
            "retry_count",
            "bytes_downloaded",
            "completed_at",
        }

        # Filter to only allowed fields
        safe_fields = {k: v for k, v in fields.items() if k in allowed_fields}
        if not safe_fields:
            logger.warning("No valid fields provided for job update: %s", fields.keys())
            return False

        job = self.job_repository.get_by_id(job_id)
        if not job:
            logger.warning("Job not found for update: %s", job_id)
            return False

        # Update job fields
        for field, value in safe_fields.items():
            setattr(job, field, value)

        # Update timestamp
        job.update_timestamp()

        # Save to repository
        self.job_repository.update(job)
        logger.info("Updated job %s with fields: %s", job_id, list(safe_fields.keys()))
        return True

    def get_job(self, job_id: str) -> Job | None:
        """Get a single job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None if not found
        """
        return self.job_repository.get_by_id(job_id)

    def get_active_jobs(self) -> list[Job]:
        """Get all active (pending or running) jobs.

        Returns:
            List of active job instances ordered by creation time
        """
        jobs = self.job_repository.get_active_jobs()

        stale_cutoff = datetime.utcnow() - timedelta(minutes=30)
        active_jobs: list[Job] = []

        for job in jobs:
            updated_at = getattr(job, "updated_at", None)
            if isinstance(updated_at, datetime) and updated_at < stale_cutoff:
                logger.warning("Marking stale active job as failed: %s", job.id)
                self.update_job(
                    job.id,
                    status=STATUS_FAILED,
                    error_message="Job was stale and was automatically failed after restart.",
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
                continue

            active_jobs.append(job)

        return active_jobs

    def list_jobs(
        self,
        platform: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filtering and pagination.

        Args:
            platform: Filter by platform
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of job instances
        """
        # Build filter criteria
        filters = {}
        if platform:
            filters["platform"] = platform
        if status:
            filters["status"] = status

        # Get jobs with filters
        if filters:
            jobs = self.job_repository.find_by(**filters)
        else:
            jobs = self.job_repository.get_all()

        # Apply pagination
        return jobs[offset : offset + limit]

    def get_job_files(self, job_id: str) -> list[Any]:
        """Get all files associated with a job.

        Args:
            job_id: Job ID

        Returns:
            List of file instances
        """
        return self.file_repository.get_job_files(job_id)

    def prepare_retry_job(self, job_id: str) -> Job | None:
        """Prepare a retry job by creating a replacement job.

        Args:
            job_id: Original job ID to retry

        Returns:
            New job instance for retry, or None if original job not found
        """
        original_job = self.job_repository.get_by_id(job_id)
        if not original_job:
            logger.warning("Original job not found for retry: %s", job_id)
            return None

        if original_job.status != STATUS_FAILED:
            logger.warning(
                "Only failed jobs can be retried, job %s has status: %s",
                job_id,
                original_job.status,
            )
            return None

        # Create new job with same URL and platform
        new_job = self.create_job(
            url=original_job.url, platform=original_job.platform, title=original_job.title
        )

        logger.info("Created retry job %s for original failed job %s", new_job.id, job_id)
        return new_job

    def delete_job(self, job_id: str, delete_files: bool = True) -> bool:
        """Delete a job and optionally its files.

        Args:
            job_id: Job ID to delete
            delete_files: Whether to delete physical files

        Returns:
            True if deleted, False if not found
        """
        job = self.job_repository.get_by_id(job_id)
        if not job:
            logger.warning("Job not found for deletion: %s", job_id)
            return False

        # Delete physical files if requested
        if delete_files and self.download_dir:
            files = self.file_repository.get_job_files(job_id)
            for file_record in files:
                file_path = self.download_dir / file_record.file_path
                try:
                    if file_path.exists():
                        file_path.unlink()
                        logger.debug("Deleted file: %s", file_path)
                except Exception as e:
                    logger.warning("Could not delete file %s: %s", file_path, e)

            # Try to remove empty directories
            for file_record in files:
                file_path = self.download_dir / file_record.file_path
                try:
                    parent = file_path.parent
                    while parent != self.download_dir:
                        if parent.is_dir() and not any(parent.iterdir()):
                            parent.rmdir()
                            logger.debug("Removed empty directory: %s", parent)
                        parent = parent.parent
                except Exception:
                    pass

        # Delete from database
        self.file_repository.delete_job_files(job_id)
        self.job_repository.delete_by_id(job_id)

        logger.info("Deleted job %s (delete_files=%s)", job_id, delete_files)
        return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if job not found or not cancellable
        """
        job = self.job_repository.get_by_id(job_id)
        if not job:
            logger.warning("Job not found for cancellation: %s", job_id)
            return False

        if job.status not in (STATUS_PENDING, STATUS_RUNNING):
            logger.warning("Job cannot be cancelled, current status: %s", job.status)
            return False

        return self.update_job(
            job_id, status=STATUS_CANCELLED, completed_at=datetime.now(timezone.utc).isoformat()
        )

    def get_job_statistics(self) -> dict[str, int]:
        """Get statistics about jobs in the system.

        Returns:
            Dictionary with job statistics
        """
        return self.job_repository.get_job_statistics()

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Delete jobs older than the specified number of days.

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of jobs deleted
        """
        return self.job_repository.cleanup_old_jobs(days)
