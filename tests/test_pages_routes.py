"""Tests for pages routes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestPagesRoutes:
    """Test cases for page routes."""

    # ========================================================================
    # GET / tests
    # ========================================================================

    def test_index_page(self, client):
        """Test dashboard page renders correctly."""
        response = client.get("/")

        assert response.status_code == 200
        # Just verify the page loads, template mocking is handled by conftest

    # ========================================================================
    # GET /browse tests
    # ========================================================================

    def test_browse_root_directory(self, client, tmp_download_dir):
        """Test browsing root download directory."""
        # Create test files and directories
        (tmp_download_dir / "file1.txt").write_text("content1")
        (tmp_download_dir / "file2.mp4").write_text("video content")
        subdir = tmp_download_dir / "subdirectory"
        subdir.mkdir()
        (subdir / "file3.jpg").write_text("image content")

        response = client.get("/browse")

        assert response.status_code == 200
        # Verify the route loads successfully (template content is mocked)

    def test_browse_subdirectory(self, client, tmp_download_dir):
        """Test browsing subdirectory."""
        subdir = tmp_download_dir / "youtube"
        subdir.mkdir()
        (subdir / "video1.mp4").write_text("video")

        response = client.get("/browse/youtube")

        assert response.status_code == 200

    def test_browse_path_not_found(self, client, tmp_download_dir):
        """Test browsing non-existent path redirects to root."""
        response = client.get("/browse/nonexistent/path", follow_redirects=False)

        assert response.status_code == 302

    def test_browse_path_traversal_attack(self, client):
        """Test browse route blocks path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
        ]

        for malicious_path in malicious_paths:
            response = client.get(f"/browse/{malicious_path}")
            assert response.status_code == 403, f"Should reject path: {malicious_path}"

    def test_browse_file_download(self, client, tmp_download_dir):
        """Test browsing to a file returns file download."""
        test_file = tmp_download_dir / "test.txt"
        test_file.write_text("test content")

        # Use Flask's Response class for the mock
        from flask import Response

        mock_response = Response(b"test content", status=200)

        with patch(
            "collector.routes.pages.safe_send_file", return_value=mock_response
        ) as mock_send:
            response = client.get("/browse/test.txt")

            # For files, safe_send_file is called
            mock_send.assert_called_once()

    def test_browse_absolute_path_attack(self, client):
        """Test browse route blocks absolute path attempts."""
        response = client.get("/browse/C:/Windows/System32/config")
        assert response.status_code == 403

    # ========================================================================
    # GET /preview tests
    # ========================================================================

    def test_preview_image_file(self, client, tmp_download_dir):
        """Test previewing image file."""
        test_file = tmp_download_dir / "image.jpg"
        test_file.write_bytes(b"fake image data")

        response = client.get("/preview/image.jpg")

        assert response.status_code == 200

    def test_preview_video_file(self, client, tmp_download_dir):
        """Test previewing video file."""
        test_file = tmp_download_dir / "video.mp4"
        test_file.write_bytes(b"fake video data")

        response = client.get("/preview/video.mp4")

        assert response.status_code == 200

    def test_preview_transcript_file(self, client, tmp_download_dir):
        """Test previewing transcript file."""
        test_file = tmp_download_dir / "transcript.txt"
        test_file.write_text("This is a transcript content.")

        response = client.get("/preview/transcript.txt")

        assert response.status_code == 200

    def test_preview_metadata_file(self, client, tmp_download_dir):
        """Test previewing metadata JSON file."""
        test_file = tmp_download_dir / "metadata.json"
        test_file.write_text('{"title": "Test", "duration": 120}')

        response = client.get("/preview/metadata.json")

        assert response.status_code == 200

    def test_preview_audio_file(self, client, tmp_download_dir):
        """Test previewing audio file."""
        test_file = tmp_download_dir / "audio.mp3"
        test_file.write_bytes(b"fake audio data")

        response = client.get("/preview/audio.mp3")

        assert response.status_code == 200

    def test_preview_unknown_file_type(self, client, tmp_download_dir):
        """Test previewing unknown file type."""
        test_file = tmp_download_dir / "file.xyz"
        test_file.write_bytes(b"some data")

        response = client.get("/preview/file.xyz")

        assert response.status_code == 200

    def test_preview_directory_redirects(self, client, tmp_download_dir):
        """Test previewing a directory redirects to browse."""
        test_dir = tmp_download_dir / "testdir"
        test_dir.mkdir()

        response = client.get(f"/preview/testdir", follow_redirects=False)

        assert response.status_code == 302

    def test_preview_file_not_found(self, client, tmp_download_dir):
        """Test previewing non-existent file."""
        response = client.get("/preview/nonexistent.txt")

        assert response.status_code == 404

    def test_preview_path_traversal_attack(self, client):
        """Test preview route blocks path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
        ]

        for malicious_path in malicious_paths:
            response = client.get(f"/preview/{malicious_path}")
            assert response.status_code == 403, f"Should reject path: {malicious_path}"

    def test_preview_file_read_error(self, client, tmp_download_dir):
        """Test previewing file with read error."""
        test_file = tmp_download_dir / "unreadable.txt"
        test_file.write_text("content")

        # Mock open to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            response = client.get("/preview/unreadable.txt")

            assert response.status_code == 200
            # Error is handled and returns 200 with error message in content

    # ========================================================================
    # GET /history tests
    # ========================================================================

    def test_history_no_filters(self, client, mock_job_service_for_pages):
        """Test history page without filters."""
        mock_job_service_for_pages.return_value.list_jobs.return_value = []

        response = client.get("/history")

        assert response.status_code == 200
        mock_job_service_for_pages.return_value.list_jobs.assert_called_once_with(
            platform=None, status=None, limit=200
        )

    def test_history_with_platform_filter(self, client, mock_job_service_for_pages):
        """Test history page with platform filter."""
        mock_job_service_for_pages.return_value.list_jobs.return_value = []

        response = client.get("/history?platform=youtube")

        assert response.status_code == 200
        mock_job_service_for_pages.return_value.list_jobs.assert_called_once_with(
            platform="youtube", status=None, limit=200
        )

    def test_history_with_status_filter(self, client, mock_job_service_for_pages):
        """Test history page with status filter."""
        mock_job_service_for_pages.return_value.list_jobs.return_value = []

        response = client.get("/history?status=completed")

        assert response.status_code == 200
        mock_job_service_for_pages.return_value.list_jobs.assert_called_once_with(
            platform=None, status="completed", limit=200
        )

    def test_history_with_both_filters(self, client, mock_job_service_for_pages):
        """Test history page with both platform and status filters."""
        mock_job_service_for_pages.return_value.list_jobs.return_value = []

        response = client.get("/history?platform=youtube&status=completed")

        assert response.status_code == 200
        mock_job_service_for_pages.return_value.list_jobs.assert_called_once_with(
            platform="youtube", status="completed", limit=200
        )
