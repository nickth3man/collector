"""Tests for YouTube scraper."""

import pytest
from scrapers.youtube_scraper import YouTubeScraper


class TestYouTubeScraper:
    """Test YouTube scraper functionality."""

    @pytest.fixture
    def scraper(self, tmp_path):
        """Create a YouTube scraper instance for testing."""
        db_path = tmp_path / "test.db"
        download_dir = tmp_path / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)

        return YouTubeScraper(
            db_path=db_path,
            download_dir=download_dir,
        )

    def test_detect_video_url(self, scraper):
        """Test YouTube video URL detection."""
        assert (
            scraper._is_playlist_or_channel("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is False
        )
        assert scraper._is_playlist_or_channel("https://youtu.be/dQw4w9WgXcQ") is False

    def test_detect_playlist_url(self, scraper):
        """Test YouTube playlist URL detection."""
        assert (
            scraper._is_playlist_or_channel(
                "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            )
            is True
        )
        assert scraper._is_playlist_or_channel("https://www.youtube.com/c/somechannel") is True
        assert scraper._is_playlist_or_channel("https://www.youtube.com/channel/UC_some_id") is True

    def test_sanitize_filename(self, scraper):
        """Test filename sanitization."""
        assert scraper.sanitize_filename("test:file/name") == "test_file_name"
        assert scraper.sanitize_filename("file<>|?*name") == "file_____name"
        assert scraper.sanitize_filename("") == "unnamed"
        assert scraper.sanitize_filename("  .test.  ") == "test"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/playlist?list=PLtest", "youtube"),
        ("https://www.instagram.com/p/ABC123/", "instagram"),
        ("https://www.instagram.com/natgeo/", "instagram"),
        ("https://example.com", None),
    ],
)
def test_detect_platform(url, expected):
    """Test platform detection from URLs."""
    from app import detect_platform

    assert detect_platform(url) == expected
