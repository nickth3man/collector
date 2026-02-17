"""
Configuration settings for the Python Content Scraper.

All settings are managed through environment variables with sensible defaults.
"""

import os
from pathlib import Path


class Config:
    """Centralized configuration with environment variable support."""

    # Validation Constants
    MIN_CONCURRENT_JOBS: int = 1
    MAX_CONCURRENT_JOBS: int = 10
    MIN_DISK_WARNING_MB: int = 100
    DEFAULT_DISK_WARNING_MB: int = 1024

    # Paths
    SCRAPER_DOWNLOAD_DIR: Path = Path(os.environ.get("SCRAPER_DOWNLOAD_DIR", "./downloads"))
    SCRAPER_DB_PATH: Path = Path(os.environ.get("SCRAPER_DB_PATH", "./instance/scraper.db"))

    # Concurrency
    SCRAPER_MAX_CONCURRENT: int = int(os.environ.get("SCRAPER_MAX_CONCURRENT", "2"))

    # Instagram rate limiting
    SCRAPER_IG_DELAY_MIN: float = float(os.environ.get("SCRAPER_IG_DELAY_MIN", "5.0"))
    SCRAPER_IG_DELAY_MAX: float = float(os.environ.get("SCRAPER_IG_DELAY_MAX", "10.0"))

    # Disk space warnings (in MB)
    SCRAPER_DISK_WARN_MB: int = int(
        os.environ.get("SCRAPER_DISK_WARN_MB", str(DEFAULT_DISK_WARNING_MB))
    )

    # Security - Flask
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

    # Security - Session encryption
    SCRAPER_SESSION_KEY: str | None = os.environ.get("SCRAPER_SESSION_KEY")

    # Flask settings
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
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
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-secret-key-change-in-production":
            if not cls.DEBUG:
                errors.append("FLASK_SECRET_KEY must be set in production")

        # Validate paths
        if not cls.SCRAPER_DOWNLOAD_DIR.exists():
            try:
                cls.SCRAPER_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create download directory {cls.SCRAPER_DOWNLOAD_DIR}: {e}")

        # Validate numeric ranges
        if (
            cls.SCRAPER_MAX_CONCURRENT < cls.MIN_CONCURRENT_JOBS
            or cls.SCRAPER_MAX_CONCURRENT > cls.MAX_CONCURRENT_JOBS
        ):
            errors.append(
                f"SCRAPER_MAX_CONCURRENT must be between {cls.MIN_CONCURRENT_JOBS} and {cls.MAX_CONCURRENT_JOBS}"
            )

        if cls.SCRAPER_IG_DELAY_MIN < 0:
            errors.append("SCRAPER_IG_DELAY_MIN must be non-negative")

        if cls.SCRAPER_IG_DELAY_MAX <= cls.SCRAPER_IG_DELAY_MIN:
            errors.append("SCRAPER_IG_DELAY_MAX must be greater than SCRAPER_IG_DELAY_MIN")

        if cls.SCRAPER_DISK_WARN_MB < cls.MIN_DISK_WARNING_MB:
            errors.append(f"SCRAPER_DISK_WARN_MB should be at least {cls.MIN_DISK_WARNING_MB} MB")

        return errors

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.SCRAPER_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (cls.SCRAPER_DOWNLOAD_DIR / "youtube").mkdir(exist_ok=True)
        (cls.SCRAPER_DOWNLOAD_DIR / "instagram").mkdir(exist_ok=True)


# Platform-specific URL patterns
INSTAGRAM_PATTERNS: list[str] = [
    r"instagram\.com/p/",
    r"instagram\.com/reel/",
    r"instagram\.com/tv/",
    r"instagram\.com/[\w.-]+/?$",  # Profile
]

YOUTUBE_PATTERNS: list[str] = [
    r"youtube\.com/watch",
    r"youtu\.be/",
    r"youtube\.com/shorts/",
    r"youtube\.com/channel/",
    r"youtube\.com/c/",
    r"youtube\.com/user/",
    r"youtube\.com/playlist\?list=",
]

# Job status constants
STATUS_PENDING: str = "pending"
STATUS_RUNNING: str = "running"
STATUS_COMPLETED: str = "completed"
STATUS_FAILED: str = "failed"
STATUS_CANCELLED: str = "cancelled"

ALL_STATUSES: list[str] = [
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
]

# File type constants
FILE_TYPE_VIDEO: str = "video"
FILE_TYPE_IMAGE: str = "image"
FILE_TYPE_AUDIO: str = "audio"
FILE_TYPE_METADATA: str = "metadata"
FILE_TYPE_TRANSCRIPT: str = "transcript"

FILE_TYPES: list[str] = [
    FILE_TYPE_VIDEO,
    FILE_TYPE_IMAGE,
    FILE_TYPE_AUDIO,
    FILE_TYPE_METADATA,
    FILE_TYPE_TRANSCRIPT,
]


def get_config() -> type[Config]:
    """Get the Config class."""
    return Config
