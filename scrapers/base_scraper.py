"""Base scraper interface with common functionality."""

from __future__ import annotations

import abc
import json
import os
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any, Callable


class BaseScraper(abc.ABC):
    """Abstract base class for platform-specific scrapers."""

    def __init__(
        self,
        db_path: Path,
        download_dir: Path,
        progress_callback: Callable[[int, str], None] | None = None,
    ):
        """Initialize the base scraper.

        Args:
            db_path: Path to SQLite database
            download_dir: Root directory for downloads
            progress_callback: Optional callback for progress updates (progress_percent, operation_text)
        """
        self.db_path = db_path
        self.download_dir = download_dir
        self.progress_callback = progress_callback

    @abc.abstractmethod
    def scrape(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape content from the given URL.

        Args:
            url: The URL to scrape
            job_id: The job ID for tracking

        Returns:
            Dictionary containing:
                - success: bool
                - title: str | None
                - files: list[dict] with file_path, file_type, file_size
                - metadata: dict with platform-specific metadata
                - error: str | None (if failed)
        """
        pass

    def update_progress(self, progress: int, operation: str) -> None:
        """Report progress via callback and update database.

        Args:
            progress: Progress percentage (0-100)
            operation: Human-readable description of current operation
        """
        if self.progress_callback:
            self.progress_callback(progress, operation)

    @staticmethod
    def sanitize_filename(name: str, max_length: int = 200) -> str:
        """Sanitize a filename by removing/replacing problematic characters.

        Args:
            name: The original filename
            max_length: Maximum length for the filename

        Returns:
            A safe filename
        """
        # Normalize unicode characters
        name = unicodedata.normalize("NFKD", name)

        # Remove control characters
        name = "".join(c for c in name if unicodedata.category(c) != "Cc")

        # Replace problematic characters with underscore
        name = re.sub(r'[<>:"/\\|?*]', "_", name)

        # Remove leading/trailing spaces and dots
        name = name.strip(". ")

        # Avoid Windows reserved names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        base_name = os.path.splitext(name)[0].upper()
        if base_name in reserved_names:
            name = f"_{name}"

        # Limit length
        if len(name) > max_length:
            # Try to preserve extension
            base, ext = os.path.splitext(name)
            name = base[: max_length - len(ext)] + ext

        # Fallback if empty
        if not name:
            name = "unnamed"

        return name

    def save_metadata(
        self,
        job_id: str,
        metadata: dict[str, Any],
        file_path: Path,
    ) -> None:
        """Save metadata to a JSON file.

        Args:
            job_id: The job ID
            metadata: Metadata dictionary to save
            file_path: Path where metadata JSON should be saved
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

    def get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection.

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_file_record(
        self,
        job_id: str,
        file_path: str,
        file_type: str,
        file_size: int,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Save a file record to the database.

        Args:
            job_id: The job ID
            file_path: Relative path from downloads root
            file_type: Type of file (video, image, audio, metadata, transcript)
            file_size: File size in bytes
            metadata: Optional metadata JSON

        Returns:
            The file record ID
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO files (job_id, file_path, file_type, file_size, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    job_id,
                    file_path,
                    file_type,
                    file_size,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_file_size(self, path: Path) -> int:
        """Get file size safely.

        Args:
            path: Path to the file

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        try:
            return path.stat().st_size
        except (OSError, FileNotFoundError):
            return 0
