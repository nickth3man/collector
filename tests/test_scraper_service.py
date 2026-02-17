"""Tests for ScraperService."""

from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest

from collector.repositories.file_repository import FileRepository
from collector.repositories.job_repository import JobRepository
from collector.services.scraper_service import ScraperService


class TestScraperService:
    """Test cases for ScraperService."""

    def test_init(self):
        """Test ScraperService initialization."""
        job_repo = Mock(spec=JobRepository)
        file_repo = Mock(spec=FileRepository)
        session_manager = Mock()
        db_path = Path("/tmp/db.sqlite")
        download_dir = Path("/tmp/downloads")

        service = ScraperService(job_repo, file_repo, session_manager, db_path, download_dir)

        assert service.job_repository == job_repo
        assert service.file_repository == file_repo
        assert service.session_manager == session_manager
        assert service.db_path == db_path
        assert service.download_dir == download_dir

    def test_init_with_defaults(self):
        """Test ScraperService initialization with defaults."""
        service = ScraperService()

        assert service.job_repository is not None
        assert service.file_repository is not None
        assert service.session_manager is None
        assert service.db_path is None
        assert service.download_dir is None

    def test_detect_platform_youtube(self):
        """Test detecting YouTube platform."""
        service = ScraperService()

        # Test various YouTube URL patterns
        youtube_urls = [
            "https://www.youtube.com/watch?v=123",
            "https://youtu.be/123",
            "https://www.youtube.com/shorts/123",
            "https://www.youtube.com/channel/UC123",
            "https://www.youtube.com/c/channel123",
            "https://www.youtube.com/user/user123",
            "https://www.youtube.com/playlist?list=123",
        ]

        for url in youtube_urls:
            assert service.detect_platform(url) == "youtube"

    def test_detect_platform_instagram(self):
        """Test detecting Instagram platform."""
        service = ScraperService()

        # Test various Instagram URL patterns
        instagram_urls = [
            "https://www.instagram.com/p/123",
            "https://www.instagram.com/reel/123",
            "https://www.instagram.com/tv/123",
            "https://www.instagram.com/username",
        ]

        for url in instagram_urls:
            assert service.detect_platform(url) == "instagram"

    def test_detect_platform_unknown(self):
        """Test detecting unknown platform."""
        service = ScraperService()

        unknown_urls = [
            "https://www.facebook.com/video/123",
            "https://www.twitter.com/status/123",
            "https://example.com/video/123",
            "",
            "not a url",
        ]

        for url in unknown_urls:
            assert service.detect_platform(url) is None

    def test_validate_url_success(self):
        """Test successful URL validation."""
        service = ScraperService()

        valid_urls = [
            "https://www.youtube.com/watch?v=123",
            "https://www.instagram.com/p/123",
        ]

        for url in valid_urls:
            is_valid, error = service.validate_url(url)
            assert is_valid is True
            assert error is None

    def test_validate_url_failure(self):
        """Test URL validation failures."""
        service = ScraperService()

        # Test empty URL
        is_valid, error = service.validate_url("")
        assert is_valid is False
        assert error == "URL is required"

        # Test invalid protocol
        is_valid, error = service.validate_url("ftp://example.com")
        assert is_valid is False
        assert error == "URL must start with http:// or https://"

        # Test unsupported platform
        is_valid, error = service.validate_url("https://www.facebook.com/video/123")
        assert is_valid is False
        assert error is not None and "Unsupported URL" in error

    @patch("collector.services.scraper_service.JobRepository")
    def test_make_progress_callback(self, mock_repo_class):
        """Test creating progress callback."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        service = ScraperService()
        callback = service.make_progress_callback("job123")

        # Call the callback
        callback(50, "Downloading")

        mock_repo.update_job_progress.assert_called_once_with("job123", 50, "Downloading")

    @patch("collector.services.scraper_service.YouTubeScraperClass")
    @patch("collector.services.scraper_service.InstagramScraperClass")
    @patch("collector.services.scraper_service.JobRepository")
    def test_get_scraper_for_platform_youtube(self, mock_repo_class, mock_insta, mock_youtube):
        """Test getting scraper for YouTube platform."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_scraper = Mock()
        mock_youtube.return_value = mock_scraper

        service = ScraperService()
        result = service.get_scraper_for_platform("youtube")

        assert result == mock_scraper
        mock_youtube.assert_called_once()
        mock_insta.assert_not_called()

    @patch("collector.services.scraper_service.YouTubeScraperClass")
    @patch("collector.services.scraper_service.InstagramScraperClass")
    @patch("collector.services.scraper_service.JobRepository")
    def test_get_scraper_for_platform_instagram(self, mock_repo_class, mock_insta, mock_youtube):
        """Test getting scraper for Instagram platform."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_scraper = Mock()
        mock_insta.return_value = mock_scraper

        service = ScraperService()
        result = service.get_scraper_for_platform("instagram")

        assert result == mock_scraper
        mock_insta.assert_called_once()
        mock_youtube.assert_not_called()

    @patch("collector.services.scraper_service.JobRepository")
    def test_get_scraper_for_platform_unsupported(self, mock_repo_class):
        """Test getting scraper for unsupported platform."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        service = ScraperService()

        with pytest.raises(ValueError, match="Unsupported platform"):
            service.get_scraper_for_platform("unsupported")

    def test_extract_username_from_instagram_url(self):
        """Test extracting username from Instagram URL."""
        service = ScraperService()

        test_cases = [
            ("https://www.instagram.com/username", "username"),
            ("https://instagram.com/username/", "username"),
            ("https://www.instagram.com/username/p/123", "username"),
            ("https://www.instagram.com/username/reel/123", "username"),
            ("https://www.instagram.com/username?param=value", "username"),
            ("https://www.instagram.com/not-instagram", "not-instagram"),
            ("https://www.facebook.com/username", None),
        ]

        for url, expected in test_cases:
            result = service.extract_username_from_instagram_url(url)
            assert result == expected

    @patch("collector.services.scraper_service.SessionManager")
    def test_get_session_for_instagram_url_success(self, mock_session_manager_class):
        """Test getting session for Instagram URL successfully."""
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_session_data = {"username": "testuser", "valid": True}
        mock_session_manager.load_session.return_value = mock_session_data
        mock_session_manager.validate_session.return_value = True
        mock_session_data["session_file"] = "/path/to/session.file"

        service = ScraperService(session_manager=mock_session_manager)
        result = service.get_session_for_instagram_url("https://www.instagram.com/testuser")

        assert result is not None
        assert result["success"] is True
        assert result["username"] == "testuser"
        assert result["session_data"] == mock_session_data
        assert result["is_valid"] is True
        mock_session_manager.load_session.assert_called_once_with("testuser")
        mock_session_manager.validate_session.assert_called_once_with(mock_session_data)

    @patch("collector.services.scraper_service.SessionManager")
    def test_get_session_for_instagram_url_no_session(self, mock_session_manager_class):
        """Test getting session for Instagram URL when no session exists."""
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.load_session.return_value = None

        service = ScraperService(session_manager=mock_session_manager)
        result = service.get_session_for_instagram_url("https://www.instagram.com/testuser")

        assert result is not None
        assert result["success"] is False
        assert result["error"] is not None and "No saved session found" in result["error"]
        mock_session_manager.load_session.assert_called_once_with("testuser")

    @patch("collector.services.scraper_service.SessionManager")
    def test_get_session_for_instagram_url_invalid(self, mock_session_manager_class):
        """Test getting session for Instagram URL when session is invalid."""
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_session_data = {"username": "testuser", "valid": False}
        mock_session_manager.load_session.return_value = mock_session_data
        mock_session_manager.validate_session.return_value = False

        service = ScraperService(session_manager=mock_session_manager)
        result = service.get_session_for_instagram_url("https://www.instagram.com/testuser")

        assert result is not None
        assert result["success"] is False
        assert result["error"] == "Session has expired"
        mock_session_manager.load_session.assert_called_once_with("testuser")
        mock_session_manager.validate_session.assert_called_once_with(mock_session_data)

    @patch("collector.services.scraper_service.SessionManager")
    def test_get_session_for_instagram_url_no_manager(self, mock_session_manager_class):
        """Test getting session when no session manager is available."""
        service = ScraperService(session_manager=None)
        result = service.get_session_for_instagram_url("https://www.instagram.com/testuser")

        assert result is not None
        assert result["success"] is False
        assert result["error"] == "Session manager not available"

    @patch("collector.services.scraper_service.JobRepository")
    @patch("collector.services.scraper_service.YouTubeScraperClass")
    def test_execute_download_youtube_success(self, mock_youtube_class, mock_repo_class):
        """Test executing download for YouTube successfully."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock()
        mock_job.url = "https://www.youtube.com/watch?v=123"
        mock_job.platform = "youtube"
        mock_repo.get_by_id.return_value = mock_job

        mock_scraper = Mock()
        mock_youtube_class.return_value = mock_scraper

        mock_result = {"success": True, "title": "Test Video"}
        mock_scraper.scrape.return_value = mock_result

        service = ScraperService()
        result = service.execute_download("job123")

        assert result["success"] is True
        assert result["title"] == "Test Video"
        mock_repo.update_job_status.assert_called_once_with("job123", "running")
        mock_youtube_class.assert_called_once()
        mock_scraper.scrape.assert_called_once_with("https://www.youtube.com/watch?v=123", "job123")
        mock_repo.update_job.assert_called_once()

    @patch("collector.services.scraper_service.JobRepository")
    @patch("collector.services.scraper_service.InstagramScraperClass")
    @patch("collector.services.scraper_service.SessionManager")
    def test_execute_download_instagram_with_session(
        self, mock_session_manager_class, mock_insta_class, mock_repo_class
    ):
        """Test executing download for Instagram with valid session."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock()
        mock_job.url = "https://www.instagram.com/testuser/p/123"
        mock_job.platform = "instagram"
        mock_repo.get_by_id.return_value = mock_job

        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_data = {"session_file": "/path/to/session.file"}
        mock_session_manager.load_session.return_value = mock_session_data
        mock_session_manager.validate_session.return_value = True

        mock_scraper = Mock()
        mock_insta_class.return_value = mock_scraper

        mock_result = {"success": True, "title": "Test Post"}
        mock_scraper.scrape.return_value = mock_result

        service = ScraperService(session_manager=mock_session_manager)
        result = service.execute_download("job123")

        assert result["success"] is True
        assert result["title"] == "Test Post"
        mock_repo.update_job_status.assert_called_once_with("job123", "running")
        mock_session_manager.load_session.assert_called_once_with("testuser")
        mock_session_manager.validate_session.assert_called_once_with(mock_session_data)
        mock_insta_class.assert_called_once_with(
            db_path=None,
            download_dir=None,
            progress_callback=ANY,
            session_file=Path("/path/to/session.file"),
        )
        mock_scraper.scrape.assert_called_once_with(
            "https://www.instagram.com/testuser/p/123", "job123"
        )
        mock_repo.update_job.assert_called_once()

    @patch("collector.services.scraper_service.JobRepository")
    def test_execute_download_job_not_found(self, mock_repo_class):
        """Test executing download when job is not found."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None

        service = ScraperService()
        result = service.execute_download("nonexistent")

        assert result["success"] is False
        assert result["error"] == "Job not found"
        mock_repo.get_by_id.assert_called_once_with("nonexistent")

    @patch("collector.services.scraper_service.JobRepository")
    @patch("collector.services.scraper_service.YouTubeScraperClass")
    def test_execute_download_scraper_failure(self, mock_youtube_class, mock_repo_class):
        """Test executing download when scraper fails."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock()
        mock_job.url = "https://www.youtube.com/watch?v=123"
        mock_job.platform = "youtube"
        mock_repo.get_by_id.return_value = mock_job

        mock_scraper = Mock()
        mock_youtube_class.return_value = mock_scraper

        mock_result = {"success": False, "error": "Scraping failed"}
        mock_scraper.scrape.return_value = mock_result

        service = ScraperService()
        result = service.execute_download("job123")

        assert result["success"] is False
        assert result["error"] == "Scraping failed"
        mock_repo.update_job_status.assert_called_once_with("job123", "running")
        mock_repo.update_job.assert_called_once()

    @patch("collector.services.scraper_service.JobRepository")
    @patch("collector.services.scraper_service.YouTubeScraperClass")
    def test_execute_download_exception(self, mock_youtube_class, mock_repo_class):
        """Test executing download when an exception occurs."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock()
        mock_job.url = "https://www.youtube.com/watch?v=123"
        mock_job.platform = "youtube"
        mock_repo.get_by_id.return_value = mock_job

        mock_scraper = Mock()
        mock_youtube_class.return_value = mock_scraper
        mock_scraper.scrape.side_effect = Exception("Test exception")

        service = ScraperService()
        result = service.execute_download("job123")

        assert result["success"] is False
        assert "Test exception" in result["error"]
        mock_repo.update_job_status.assert_called_once_with("job123", "running")
        mock_repo.update_job.assert_called_once()
