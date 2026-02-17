"""
Configuration module for the Python Content Scraper.

This module provides backward compatibility by importing from the new config package.
All existing code that imports from this module will continue to work.
"""

# Import all the configuration classes and constants from the new config package
from collector.config.settings import (
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

# Re-export everything for backward compatibility
__all__ = [
    "Config",
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
    "get_config",
]
