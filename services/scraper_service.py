"""Scraper service for orchestrating scraping operations.

This service encapsulates scraping workflow and orchestration logic, including
platform detection, URL validation, and scraper execution.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import (
    INSTAGRAM_PATTERNS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    YOUTUBE_PATTERNS,
)
from repositories.file_repository import FileRepository
from repositories.job_repository import JobRepository
from services.session_manager import SessionManager

# Import scrapers conditionally to avoid import errors in test environment

try:
    from scrapers import InstagramScraper as InstagramScraperClass
    from scrapers import YouTubeScraper as YouTubeScraperClass

    SCRAPERS_AVAILABLE = True
except ImportError:
    InstagramScraperClass = None  # type: ignore
    YouTubeScraperClass = None  # type: ignore
    SCRAPERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for orchestrating scraping operations."""

    def __init__(
        self,
        job_repository: JobRepository | None = None,
        file_repository: FileRepository | None = None,
        session_manager: SessionManager | None = None,
        db_path: Path | None = None,
        download_dir: Path | None = None,
    ) -> None:
        """Initialize the scraper service.

        Args:
            job_repository: Repository for job operations
            file_repository: Repository for file operations
            session_manager: Session manager for Instagram sessions
            db_path: Path to SQLite database
            download_dir: Directory for downloaded files
        """
        self.job_repository = job_repository or JobRepository()
        self.file_repository = file_repository or FileRepository()
        self.session_manager = session_manager
        self.db_path = db_path
        self.download_dir = download_dir

    def detect_platform(self, url: str) -> str | None:
        """Detect platform from URL.

        Args:
            url: URL to check

        Returns:
            'youtube', 'instagram', or None
        """
        for pattern in YOUTUBE_PATTERNS:
            if re.search(pattern, url):
                return "youtube"

        for pattern in INSTAGRAM_PATTERNS:
            if re.search(pattern, url):
                return "instagram"

        return None

    def validate_url(self, url: str) -> tuple[bool, str | None]:
        """Validate a URL.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return False, "URL must start with http:// or https://"

        # Platform detection
        platform = self.detect_platform(url)
        if not platform:
            return False, "Unsupported URL. Please provide a valid Instagram or YouTube URL."

        return True, None

    def make_progress_callback(self, job_id: str) -> Callable[[int, str], None]:
        """Create a progress callback function for a job.

        Args:
            job_id: Job ID

        Returns:
            Callback function
        """

        def callback(progress: int, operation: str) -> None:
            self.job_repository.update_job_progress(job_id, progress, operation)

        return callback

    def execute_download(self, job_id: str) -> dict[str, Any]:
        """Execute a download job in the background.

        Args:
            job_id: Job ID to execute

        Returns:
            Dictionary with execution result
        """
        job = self.job_repository.get_by_id(job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            return {"success": False, "error": "Job not found"}

        url = job.url
        platform = job.platform

        # Update status to running
        self.job_repository.update_job_status(job_id, STATUS_RUNNING)

        try:
            progress_callback = self.make_progress_callback(job_id)

            if not SCRAPERS_AVAILABLE:
                raise ImportError("Scrapers not available - missing dependencies")

            if platform == "youtube":
                scraper = YouTubeScraperClass(
                    db_path=self.db_path,
                    download_dir=self.download_dir,
                    progress_callback=progress_callback,
                )
            else:  # instagram
                # Try to find a saved session for this URL
                session_file = None
                if self.session_manager:
                    try:
                        # Extract username from URL for session lookup
                        match = re.search(r"instagram\.com/([^/?]+)", url)
                        if match:
                            username = match.group(1)
                            session_data = self.session_manager.load_session(username)
                            if session_data and self.session_manager.validate_session(session_data):
                                # Session is valid, get the session file
                                session_file = Path(session_data.get("session_file", ""))
                    except Exception as e:
                        logger.warning("Could not load session: %s", e)

                scraper = InstagramScraperClass(
                    db_path=self.db_path,
                    download_dir=self.download_dir,
                    progress_callback=progress_callback,
                    session_file=session_file,
                )

            # Execute scrape
            result = scraper.scrape(url, job_id)

            if result["success"]:
                self.job_repository.update_job(
                    job_id,
                    status=STATUS_COMPLETED,
                    title=result.get("title"),
                    progress=100,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
            else:
                error = result.get("error", "Unknown error")
                self.job_repository.update_job(
                    job_id,
                    status=STATUS_FAILED,
                    error_message=error,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            return result

        except Exception as e:
            logger.exception("Error executing job %s: %s", job_id, e)
            self.job_repository.update_job(
                job_id,
                status=STATUS_FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            return {"success": False, "error": str(e)}

    def get_scraper_for_platform(
        self,
        platform: str,
        progress_callback: Callable[[int, str], None] | None = None,
        session_file: Path | None = None,
    ) -> Any:
        """Get appropriate scraper instance for a platform.

        Args:
            platform: Platform name ('youtube' or 'instagram')
            progress_callback: Optional progress callback function
            session_file: Optional session file for Instagram

        Returns:
            Scraper instance
        """
        if not SCRAPERS_AVAILABLE:
            raise ImportError("Scrapers not available - missing dependencies")

        if platform == "youtube":
            return YouTubeScraperClass(
                db_path=self.db_path,
                download_dir=self.download_dir,
                progress_callback=progress_callback,
            )
        elif platform == "instagram":
            return InstagramScraperClass(
                db_path=self.db_path,
                download_dir=self.download_dir,
                progress_callback=progress_callback,
                session_file=session_file,
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def extract_username_from_instagram_url(self, url: str) -> str | None:
        """Extract username from Instagram URL.

        Args:
            url: Instagram URL

        Returns:
            Username if found, None otherwise
        """
        match = re.search(r"instagram\.com/([^/?]+)", url)
        return match.group(1) if match else None

    def get_session_for_instagram_url(self, url: str) -> dict[str, Any]:
        """Get session for Instagram URL if available.

        Args:
            url: Instagram URL

        Returns:
            Dictionary with session result
        """
        # Extract username from URL
        match = re.search(r"instagram\.com/([^/?]+)", url)
        if not match:
            return {"success": False, "error": "Could not extract username from URL"}

        username = match.group(1)

        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        try:
            session_data = self.session_manager.load_session(username)
            if not session_data:
                return {"success": False, "error": f"No saved session found for {username}"}

            # Validate session
            is_valid = self.session_manager.validate_session(session_data)
            if not is_valid:
                return {"success": False, "error": "Session has expired"}

            return {
                "success": True,
                "username": username,
                "session_data": session_data,
                "is_valid": True,
            }
        except Exception as e:
            logger.warning("Could not load session for %s: %s", username, e)
            return {"success": False, "error": f"Failed to load session: {str(e)}"}
