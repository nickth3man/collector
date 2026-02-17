"""
Configuration module for the Python Content Scraper.

This package provides centralized configuration management with environment variable support.
"""

from .database import DatabaseConfig
from .settings import (
    ALL_STATUSES,
    FILE_TYPE_AUDIO,
    FILE_TYPE_IMAGE,
    FILE_TYPE_METADATA,
    FILE_TYPE_TRANSCRIPT,
    FILE_TYPE_VIDEO,
    FILE_TYPES,
    INSTAGRAM_PATTERNS,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
    YOUTUBE_PATTERNS,
    Config,
    get_config,
)

__all__ = [
    "Config",
    "get_config",
    "DatabaseConfig",
    "INSTAGRAM_PATTERNS",
    "YOUTUBE_PATTERNS",
    "STATUS_PENDING",
    "STATUS_RUNNING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_CANCELLED",
    "ALL_STATUSES",
    "FILE_TYPE_VIDEO",
    "FILE_TYPE_IMAGE",
    "FILE_TYPE_AUDIO",
    "FILE_TYPE_METADATA",
    "FILE_TYPE_TRANSCRIPT",
    "FILE_TYPES",
]
