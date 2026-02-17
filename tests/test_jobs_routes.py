"""Tests for jobs routes."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from collector.models.job import Job


class TestJobsRoutes:
    """Test cases for job management routes."""

    # ========================================================================
    # POST /download tests
    # ========================================================================

    def test_download_with_valid_url_htmx(
        self, client, mock_scraper_service, mock_job_service, mock_executor_adapter, auto_mock_csrf
    ):
        """Test download route with valid URL via HTMX."""
        test_url = "https://www.youtube.com/watch?v=test123"
        test_job = Job(
            id="job-123",
            url=test_url,
            platform="youtube",
            title="Test Video",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_scraper_service.return_value.validate_url.return_value = (True, None)
        mock_scraper_service.return_value.detect_platform.return_value = "youtube"
        mock_job_service.return_value.create_job.return_value = test_job
        mock_executor_adapter.return_value.submit_job.return_value = None

        response = client.post("/download", data={"url": test_url}, headers={"HX-Request": "true"})

        assert response.status_code == 200
        mock_scraper_service.return_value.validate_url.assert_called_once_with(test_url)
        mock_scraper_service.return_value.detect_platform.assert_called_once_with(test_url)
        mock_job_service.return_value.create_job.assert_called_once()
        mock_executor_adapter.return_value.submit_job.assert_called_once()

    def test_download_with_valid_url_regular(
        self, client, mock_scraper_service, mock_job_service, mock_executor_adapter, auto_mock_csrf
    ):
        """Test download route with valid URL via regular request."""
        test_url = "https://www.youtube.com/watch?v=test123"
        test_job = Job(
            id="job-123",
            url=test_url,
            platform="youtube",
            title="Test Video",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_scraper_service.return_value.validate_url.return_value = (True, None)
        mock_scraper_service.return_value.detect_platform.return_value = "youtube"
        mock_job_service.return_value.create_job.return_value = test_job
        mock_executor_adapter.return_value.submit_job.return_value = None

        response = client.post("/download", data={"url": test_url}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_download_with_invalid_url_htmx(self, client, mock_scraper_service, auto_mock_csrf):
        """Test download route with invalid URL via HTMX."""
        test_url = "not-a-valid-url"
        mock_scraper_service.return_value.validate_url.return_value = (False, "Invalid URL format")

        response = client.post("/download", data={"url": test_url}, headers={"HX-Request": "true"})

        assert response.status_code == 400
        assert b"Invalid URL format" in response.data

    def test_download_with_invalid_url_regular(self, client, mock_scraper_service, auto_mock_csrf):
        """Test download route with invalid URL via regular request."""
        test_url = "not-a-valid-url"
        mock_scraper_service.return_value.validate_url.return_value = (False, "Invalid URL format")

        response = client.post("/download", data={"url": test_url}, follow_redirects=False)

        assert response.status_code == 302

    def test_download_platform_detection_fails_htmx(
        self, client, mock_scraper_service, auto_mock_csrf
    ):
        """Test download route when platform detection fails via HTMX."""
        test_url = "https://unknown-platform.com/content"
        mock_scraper_service.return_value.validate_url.return_value = (True, None)
        mock_scraper_service.return_value.detect_platform.return_value = None

        response = client.post("/download", data={"url": test_url}, headers={"HX-Request": "true"})

        assert response.status_code == 400
        assert b"Could not detect platform" in response.data

    def test_download_missing_csrf_token_htmx(self, client):
        """Test download route without CSRF token via HTMX."""
        response = client.post(
            "/download",
            data={"url": "https://youtube.com/watch?v=test"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 403

    def test_download_missing_csrf_token_regular(self, client):
        """Test download route without CSRF token via regular request."""
        response = client.post(
            "/download",
            data={"url": "https://youtube.com/watch?v=test"},
        )

        assert response.status_code == 403

    def test_download_invalid_csrf_token(self, client):
        """Test download route with invalid CSRF token."""
        with client.session_transaction() as sess:
            sess["_csrf_token"] = "valid-token"

        response = client.post(
            "/download",
            data={"url": "https://youtube.com/watch?v=test", "csrf_token": "invalid-token"},
        )

        assert response.status_code == 403

    # ========================================================================
    # GET /job/<job_id> tests
    # ========================================================================

    def test_job_detail_found_htmx(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test job detail page with HTMX returns partial."""
        test_files = [
            Mock(file_type="video", file_path="video.mp4", size_bytes=1024000),
            Mock(file_type="thumbnail", file_path="thumb.jpg", size_bytes=50000),
        ]

        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.get_job_files.return_value = test_files

        response = client.get(f"/job/{sample_job.id}", headers={"HX-Request": "true"})

        assert response.status_code == 200
        mock_job_service.return_value.get_job.assert_called_once_with(sample_job.id)
        mock_job_service.return_value.get_job_files.assert_called_once_with(sample_job.id)

    def test_job_detail_found_regular(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test job detail page with regular request returns full page."""
        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.get_job_files.return_value = []

        response = client.get(f"/job/{sample_job.id}")

        assert response.status_code == 200
        mock_job_service.return_value.get_job.assert_called_once_with(sample_job.id)

    def test_job_detail_not_found_htmx(self, client, mock_job_service, auto_mock_csrf):
        """Test job detail page with non-existent job via HTMX."""
        mock_job_service.return_value.get_job.return_value = None

        response = client.get("/job/nonexistent-job", headers={"HX-Request": "true"})

        assert response.status_code == 404

    def test_job_detail_not_found_regular(self, client, mock_job_service, auto_mock_csrf):
        """Test job detail page with non-existent job via regular request."""
        mock_job_service.return_value.get_job.return_value = None

        response = client.get("/job/nonexistent-job")

        assert response.status_code == 404

    # ========================================================================
    # GET /job/<job_id>/status tests
    # ========================================================================

    def test_job_status_found(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test job status endpoint returns HTMX partial."""
        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.get_job_files.return_value = []

        response = client.get(f"/job/{sample_job.id}/status")

        assert response.status_code == 200
        mock_job_service.return_value.get_job.assert_called_once_with(sample_job.id)

    def test_job_status_not_found(self, client, mock_job_service, auto_mock_csrf):
        """Test job status endpoint with non-existent job."""
        mock_job_service.return_value.get_job.return_value = None

        response = client.get("/job/nonexistent-job/status")

        assert response.status_code == 404

    # ========================================================================
    # GET /jobs/active tests
    # ========================================================================

    def test_active_jobs_with_jobs(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test active jobs endpoint with jobs."""
        mock_job_service.return_value.get_active_jobs.return_value = [sample_job]

        response = client.get("/jobs/active")

        assert response.status_code == 200
        mock_job_service.return_value.get_active_jobs.assert_called_once()

    def test_active_jobs_empty(self, client, mock_job_service, auto_mock_csrf):
        """Test active jobs endpoint with no jobs."""
        mock_job_service.return_value.get_active_jobs.return_value = []

        response = client.get("/jobs/active")

        assert response.status_code == 200
        mock_job_service.return_value.get_active_jobs.assert_called_once()

    # ========================================================================
    # POST /job/<job_id>/cancel tests
    # ========================================================================

    def test_cancel_job_success_htmx(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test successful job cancellation via HTMX."""
        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.cancel_job.return_value = True

        response = client.post(
            f"/job/{sample_job.id}/cancel", data={}, headers={"HX-Request": "true"}
        )

        assert response.status_code == 204
        assert response.data == b""

    def test_cancel_job_success_regular(self, client, mock_job_service, sample_job, auto_mock_csrf):
        """Test successful job cancellation via regular request."""
        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.cancel_job.return_value = True

        response = client.post(f"/job/{sample_job.id}/cancel", data={}, follow_redirects=False)

        assert response.status_code == 302

    def test_cancel_job_not_cancellable_htmx(
        self, client, mock_job_service, sample_job, auto_mock_csrf
    ):
        """Test cancelling a job that cannot be cancelled via HTMX."""
        mock_job_service.return_value.get_job.return_value = sample_job
        mock_job_service.return_value.cancel_job.return_value = False

        response = client.post(
            f"/job/{sample_job.id}/cancel", data={}, headers={"HX-Request": "true"}
        )

        # Note: Current implementation redirects even with HTMX
        assert response.status_code == 302

    def test_cancel_job_not_found(self, client, mock_job_service, auto_mock_csrf):
        """Test cancelling a non-existent job."""
        mock_job_service.return_value.get_job.return_value = None

        response = client.post("/job/nonexistent-job/cancel", data={})

        assert response.status_code == 404

    def test_cancel_job_missing_csrf(self, client):
        """Test cancelling job without CSRF token."""
        response = client.post("/job/job-123/cancel")

        assert response.status_code == 403

    # ========================================================================
    # POST /job/<job_id>/retry tests
    # ========================================================================

    def test_retry_job_success_htmx(
        self, client, mock_job_service, mock_scraper_service, mock_executor_adapter, auto_mock_csrf
    ):
        """Test successful job retry via HTMX."""
        test_job = Job(
            id="new-job-456",
            url="https://youtube.com/watch?v=test",
            platform="youtube",
            title="Test Video",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_job_service.return_value.prepare_retry_job.return_value = test_job
        mock_executor_adapter.return_value.submit_job.return_value = None

        response = client.post("/job/job-123/retry", data={}, headers={"HX-Request": "true"})

        assert response.status_code == 200

    def test_retry_job_success_regular(
        self, client, mock_job_service, mock_scraper_service, mock_executor_adapter, auto_mock_csrf
    ):
        """Test successful job retry via regular request."""
        test_job = Job(
            id="new-job-456",
            url="https://youtube.com/watch?v=test",
            platform="youtube",
            title="Test Video",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_job_service.return_value.prepare_retry_job.return_value = test_job
        mock_executor_adapter.return_value.submit_job.return_value = None

        response = client.post("/job/job-123/retry", data={}, follow_redirects=False)

        assert response.status_code == 302

    def test_retry_job_not_failed_regular(self, client, mock_job_service, auto_mock_csrf):
        """Test retrying a job that is not in failed state."""
        mock_job_service.return_value.prepare_retry_job.return_value = None

        response = client.post("/job/job-123/retry", data={}, follow_redirects=False)

        assert response.status_code == 302

    def test_retry_job_missing_csrf(self, client):
        """Test retrying job without CSRF token."""
        response = client.post("/job/job-123/retry")

        assert response.status_code == 403

    # ========================================================================
    # DELETE /job/<job_id> tests
    # ========================================================================

    def test_delete_job_success_htmx(self, client, mock_job_service, auto_mock_csrf):
        """Test successful job deletion via HTMX."""
        mock_job_service.return_value.delete_job.return_value = True

        response = client.delete("/job/job-123", data={}, headers={"HX-Request": "true"})

        assert response.status_code == 204
        assert response.data == b""

    def test_delete_job_success_regular(self, client, mock_job_service, auto_mock_csrf):
        """Test successful job deletion via regular request."""
        mock_job_service.return_value.delete_job.return_value = True

        response = client.delete("/job/job-123", data={}, follow_redirects=False)

        assert response.status_code == 302

    def test_delete_job_not_found_htmx(self, client, mock_job_service, auto_mock_csrf):
        """Test deleting non-existent job via HTMX."""
        mock_job_service.return_value.delete_job.return_value = False

        response = client.delete("/job/nonexistent-job", data={}, headers={"HX-Request": "true"})

        assert response.status_code == 404

    def test_delete_job_not_found_regular(self, client, mock_job_service, auto_mock_csrf):
        """Test deleting non-existent job via regular request."""
        mock_job_service.return_value.delete_job.return_value = False

        response = client.delete("/job/nonexistent-job", data={}, follow_redirects=False)

        assert response.status_code == 302

    def test_delete_job_missing_csrf(self, client):
        """Test deleting job without CSRF token."""
        response = client.delete("/job/job-123")

        assert response.status_code == 403
