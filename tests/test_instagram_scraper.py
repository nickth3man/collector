"""Tests for Instagram scraper."""

import pytest

from collector.scrapers.instagram_scraper import InstagramScraper


class TestInstagramScraper:
    """Test Instagram scraper functionality."""

    @pytest.fixture
    def scraper(self, tmp_path):
        """Create an Instagram scraper instance for testing."""
        db_path = tmp_path / "test.db"
        download_dir = tmp_path / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)

        return InstagramScraper(
            db_path=db_path,
            download_dir=download_dir,
        )

    def test_detect_url_type_profile(self, scraper):
        """Test profile URL detection."""
        assert scraper._detect_url_type("https://www.instagram.com/natgeo/") == "profile"
        assert scraper._detect_url_type("https://instagram.com/natgeo") == "profile"
        assert scraper._detect_url_type("https://www.instagram.com/test_user/") == "profile"

    def test_detect_url_type_post(self, scraper):
        """Test post URL detection."""
        assert scraper._detect_url_type("https://www.instagram.com/p/ABC123/") == "post"
        assert scraper._detect_url_type("https://www.instagram.com/reel/XYZ789/") == "post"
        assert scraper._detect_url_type("https://www.instagram.com/p/ABC123") == "post"

    def test_extract_username(self, scraper):
        """Test username extraction from profile URL."""
        assert scraper._extract_username("https://www.instagram.com/natgeo/") == "natgeo"
        assert scraper._extract_username("https://instagram.com/test_user") == "test_user"
        assert scraper._extract_username("https://www.instagram.com/test_user/") == "test_user"
        assert scraper._extract_username("invalid-url") is None

    def test_extract_shortcode(self, scraper):
        """Test shortcode extraction from post URL."""
        assert scraper._extract_shortcode("https://www.instagram.com/p/ABC123/") == "ABC123"
        assert scraper._extract_shortcode("https://www.instagram.com/reel/XYZ789/") == "XYZ789"
        assert scraper._extract_shortcode("https://www.instagram.com/p/ABC123") == "ABC123"
        assert scraper._extract_shortcode("invalid-url") is None

    def test_sanitize_filename(self, scraper):
        """Test filename sanitization using base class method."""
        assert scraper.sanitize_filename("test:file/name") == "test_file_name"
        assert scraper.sanitize_filename("file<>|?*name") == "file_____name"
        assert scraper.sanitize_filename("") == "unnamed"
        assert scraper.sanitize_filename("  .test.  ") == "test"

    def test_detect_url_type_stories(self, scraper):
        """Test stories URL detection."""
        assert scraper._detect_url_type("https://www.instagram.com/stories/username/") == "stories"
        assert scraper._detect_url_type("https://instagram.com/stories/username/12345") == "stories"
        assert scraper._detect_url_type("https://www.instagram.com/stories/natgeo/") == "stories"

    def test_detect_url_type_highlights(self, scraper):
        """Test highlights URL detection."""
        assert scraper._detect_url_type("https://www.instagram.com/highlights/username/") == "highlights"
        assert scraper._detect_url_type("https://instagram.com/highlights/username/") == "highlights"

    def test_scrape_stories_requires_session(self, scraper):
        """Test that stories scraping requires an authenticated session."""
        result = scraper._scrape_stories("https://www.instagram.com/stories/test/", "job-123")
        assert not result["success"]
        assert "authenticated session" in result["error"].lower()

    def test_scrape_highlights_requires_session(self, scraper):
        """Test that highlights scraping requires an authenticated session."""
        result = scraper._scrape_highlights("https://www.instagram.com/highlights/test/", "job-123")
        assert not result["success"]
        assert "authenticated session" in result["error"].lower()

