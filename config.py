"""
Configuration module for the Python Content Scraper.

All settings are managed through environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import cast


class Config:
    """Centralized configuration with environment variable support."""

    # Paths
    SCRAPER_DOWNLOAD_DIR: Path = Path(
        os.environ.get("SCRAPER_DOWNLOAD_DIR", "./downloads")
    )
    SCRAPER_DB_PATH: Path = Path(os.environ.get("SCRAPER_DB_PATH", "./scraper.db"))

    # Concurrency
    SCRAPER_MAX_CONCURRENT: int = int(
        os.environ.get("SCRAPER_MAX_CONCURRENT", "2")
    )

    # Instagram rate limiting
    SCRAPER_IG_DELAY_MIN: float = float(
        os.environ.get("SCRAPER_IG_DELAY_MIN", "5.0")
    )
    SCRAPER_IG_DELAY_MAX: float = float(
        os.environ.get("SCRAPER_IG_DELAY_MAX", "10.0")
    )

    # Disk space warnings (in MB)
    SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", "1024"))

    # Security - Flask
    FLASK_SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

    # Security - Session encryption
    SCRAPER_SESSION_KEY: str | None = os.environ.get("SCRAPER_SESSION_KEY")

    # Flask settings
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")
    TESTING: bool = os.environ.get("FLASK_TESTING", "false").lower() in ("true", "1", "yes")

    # Application settings
    APP_HOST: str = os.environ.get("FLASK_HOST", "127.0.0.1")
    APP_PORT: int = int(os.environ.get("FLASK_PORT", "5000"))

    # Retry settings
    MAX_RETRIES: int = int(os.environ.get("SCRAPER_MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE: float = float(os.environ.get("SCRAPER_RETRY_BACKOFF_BASE", "2.0"))

    # Graceful shutdown timeout (seconds)
    SHUTDOWN_TIMEOUT: int = int(os.environ.get("SCRAPER_SHUTDOWN_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors.

        Returns empty list if configuration is valid.
        """
        errors: list[str] = []

        # Validate required settings
        if not cls.FLASK_SECRET_KEY or cls.FLASK_SECRET_KEY == "dev-secret-key-change-in-production":
            if not cls.DEBUG:
                errors.append("FLASK_SECRET_KEY must be set in production")

        # Validate paths
        if not cls.SCRAPER_DOWNLOAD_DIR.exists():
            try:
                cls.SCRAPER_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create download directory {cls.SCRAPER_DOWNLOAD_DIR}: {e}")

        # Validate numeric ranges
        if cls.SCRAPER_MAX_CONCURRENT < 1 or cls.SCRAPER_MAX_CONCURRENT > 10:
            errors.append("SCRAPER_MAX_CONCURRENT must be between 1 and 10")

        if cls.SCRAPER_IG_DELAY_MIN < 0:
            errors.append("SCRAPER_IG_DELAY_MIN must be non-negative")

        if cls.SCRAPER_IG_DELAY_MAX <= cls.SCRAPER_IG_DELAY_MIN:
            errors.append("SCRAPER_IG_DELAY_MAX must be greater than SCRAPER_IG_DELAY_MIN")

        if cls.SCRAPER_DISK_WARN_MB < 100:
            errors.append("SCRAPER_DISK_WARN_MB should be at least 100 MB")

        return errors

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.SCRAPER_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (cls.SCRAPER_DOWNLOAD_DIR / "youtube").mkdir(exist_ok=True)
        (cls.SCRAPER_DOWNLOAD_DIR / "instagram").mkdir(exist_ok=True)


# Platform-specific URL patterns
INSTAGRAM_PATTERNS = [
    r"instagram\.com/p/",
    r"instagram\.com/reel/",
    r"instagram\.com/tv/",
    r"instagram\.com/[\w.-]+/?$",  # Profile
]

YOUTUBE_PATTERNS = [
    r"youtube\.com/watch",
    r"youtu\.be/",
    r"youtube\.com/shorts/",
    r"youtube\.com/channel/",
    r"youtube\.com/c/",
    r"youtube\.com/user/",
    r"youtube\.com/playlist\?list=",
]

# Job status constants
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

ALL_STATUSES = [
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
]

# File type constants
FILE_TYPE_VIDEO = "video"
FILE_TYPE_IMAGE = "image"
FILE_TYPE_AUDIO = "audio"
FILE_TYPE_METADATA = "metadata"
FILE_TYPE_TRANSCRIPT = "transcript"

FILE_TYPES = [
    FILE_TYPE_VIDEO,
    FILE_TYPE_IMAGE,
    FILE_TYPE_AUDIO,
    FILE_TYPE_METADATA,
    FILE_TYPE_TRANSCRIPT,
]


def get_config() -> Config:
    """Get the singleton Config instance."""
    return Config
