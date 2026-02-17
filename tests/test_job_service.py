"""Tests for JobService."""

from pathlib import Path
from unittest.mock import Mock, patch

from collector.models.job import Job
from collector.repositories.file_repository import FileRepository
from collector.repositories.job_repository import JobRepository
from collector.services.job_service import JobService


class TestJobService:
    """Test cases for JobService."""

    def test_init(self):
        """Test JobService initialization."""
        job_repo = Mock(spec=JobRepository)
        file_repo = Mock(spec=FileRepository)
        download_dir = Path("/tmp/downloads")

        service = JobService(job_repo, file_repo, download_dir)

        assert service.job_repository == job_repo
        assert service.file_repository == file_repo
        assert service.download_dir == download_dir

    def test_init_with_defaults(self):
        """Test JobService initialization with default repositories."""
        service = JobService()

        assert service.job_repository is not None
        assert service.file_repository is not None
        assert service.download_dir is None

    @patch("collector.services.job_service.JobRepository")
    def test_create_job(self, mock_repo_class):
        """Test creating a new job."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock(spec=Job)
        mock_repo.create_job.return_value = mock_job

        service = JobService()
        result = service.create_job("https://example.com", "youtube", "Test Video")

        mock_repo.create_job.assert_called_once_with("https://example.com", "youtube", "Test Video")
        assert result == mock_job

    @patch("collector.services.job_service.JobRepository")
    def test_update_job_success(self, mock_repo_class):
        """Test successful job update."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock(spec=Job)
        mock_repo.get_by_id.return_value = mock_job

        service = JobService()
        result = service.update_job("job123", status="completed", progress=100)

        assert result is True
        mock_repo.get_by_id.assert_called_once_with("job123")
        mock_job.update_timestamp.assert_called_once()
        mock_repo.update.assert_called_once_with(mock_job)

    @patch("collector.services.job_service.JobRepository")
    def test_update_job_not_found(self, mock_repo_class):
        """Test updating a job that doesn't exist."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None

        service = JobService()
        result = service.update_job("nonexistent", status="completed")

        assert result is False
        mock_repo.get_by_id.assert_called_once_with("nonexistent")
        mock_repo.update.assert_not_called()

    @patch("collector.services.job_service.JobRepository")
    def test_update_job_invalid_fields(self, mock_repo_class):
        """Test updating job with invalid fields."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock(spec=Job)
        mock_repo.get_by_id.return_value = mock_job

        service = JobService()
        result = service.update_job("job123", invalid_field="value")

        assert result is False
        mock_repo.update.assert_not_called()

    @patch("collector.services.job_service.JobRepository")
    def test_get_job(self, mock_repo_class):
        """Test getting a job by ID."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_job = Mock(spec=Job)
        mock_repo.get_by_id.return_value = mock_job

        service = JobService()
        result = service.get_job("job123")

        assert result == mock_job
        mock_repo.get_by_id.assert_called_once_with("job123")

    @patch("collector.services.job_service.JobRepository")
    def test_get_active_jobs(self, mock_repo_class):
        """Test getting active jobs."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_jobs = [Mock(spec=Job), Mock(spec=Job)]
        mock_repo.get_active_jobs.return_value = mock_jobs

        service = JobService()
        result = service.get_active_jobs()

        assert result == mock_jobs
        mock_repo.get_active_jobs.assert_called_once()

    @patch("collector.services.job_service.JobRepository")
    def test_list_jobs_with_filters(self, mock_repo_class):
        """Test listing jobs with filters."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_jobs = [Mock(spec=Job), Mock(spec=Job), Mock(spec=Job)]
        mock_repo.find_by.return_value = mock_jobs
        mock_repo.get_all.return_value = mock_jobs

        service = JobService()

        # Test with platform filter
        result = service.list_jobs(platform="youtube")
        mock_repo.find_by.assert_called_once_with(platform="youtube")
        assert result == mock_jobs

        # Test with no filters
        mock_repo.reset_mock()
        result = service.list_jobs()
        mock_repo.get_all.assert_called_once()
        assert result == mock_jobs

    @patch("collector.services.job_service.JobRepository")
    @patch("collector.services.job_service.FileRepository")
    def test_get_job_files(self, mock_file_repo_class, mock_job_repo_class):
        """Test getting files for a job."""
        mock_job_repo = Mock()
        mock_job_repo_class.return_value = mock_job_repo
        mock_file_repo = Mock()
        mock_file_repo_class.return_value = mock_file_repo
        mock_files = [Mock(), Mock()]
        mock_file_repo.get_job_files.return_value = mock_files

        service = JobService()
        result = service.get_job_files("job123")

        assert result == mock_files
        mock_file_repo.get_job_files.assert_called_once_with("job123")

    @patch("collector.services.job_service.JobRepository")
    @patch("collector.services.job_service.JobService.create_job")
    def test_prepare_retry_job_success(self, mock_create, mock_repo_class):
        """Test preparing a retry job for a failed job."""
        mock_original_job = Mock(spec=Job)
        mock_original_job.status = "failed"
        mock_original_job.url = "https://example.com"
        mock_original_job.platform = "youtube"
        mock_original_job.title = "Test Video"
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = mock_original_job

        mock_new_job = Mock(spec=Job)
        mock_new_job.id = "new_job_123"
        mock_create.return_value = mock_new_job

        service = JobService()
        result = service.prepare_retry_job("job123")

        assert result == mock_new_job
        mock_repo.get_by_id.assert_called_once_with("job123")
        mock_create.assert_called_once_with(
            url="https://example.com", platform="youtube", title="Test Video"
        )

    @patch("collector.services.job_service.JobRepository")
    def test_prepare_retry_job_not_failed(self, mock_repo_class):
        """Test preparing a retry job for a non-failed job."""
        mock_original_job = Mock(spec=Job)
        mock_original_job.status = "completed"
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = mock_original_job

        service = JobService()
        result = service.prepare_retry_job("job123")

        assert result is None
        mock_repo.get_by_id.assert_called_once_with("job123")

    @patch("collector.services.job_service.FileRepository")
    @patch("collector.services.job_service.JobRepository")
    def test_delete_job_with_files(self, mock_job_repo_class, mock_file_repo_class):
        """Test deleting a job with files."""
        mock_job_repo = Mock()
        mock_job_repo_class.return_value = mock_job_repo
        mock_file_repo = Mock()
        mock_file_repo_class.return_value = mock_file_repo

        mock_job = Mock(spec=Job)
        mock_job_repo.get_by_id.return_value = mock_job

        mock_file1 = Mock()
        mock_file1.file_path = "video1.mp4"
        mock_file2 = Mock()
        mock_file2.file_path = "video2.mp4"
        mock_file_repo.get_job_files.return_value = [mock_file1, mock_file2]

        download_dir = Path("/tmp/downloads")
        service = JobService(download_dir=download_dir)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.iterdir", return_value=[]),
            patch("pathlib.Path.rmdir"),
        ):
            result = service.delete_job("job123", delete_files=True)

            assert result is True
            mock_job_repo.get_by_id.assert_called_once_with("job123")
            mock_file_repo.get_job_files.assert_called_once_with("job123")
            assert mock_unlink.call_count == 2
            mock_file_repo.delete_job_files.assert_called_once_with("job123")
            mock_job_repo.delete_by_id.assert_called_once_with("job123")

    @patch("collector.services.job_service.JobRepository")
    @patch("collector.services.job_service.JobService.update_job")
    def test_cancel_job_success(self, mock_update, mock_repo_class):
        """Test cancelling a job."""
        mock_job = Mock(spec=Job)
        mock_job.status = "pending"
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = mock_job
        mock_update.return_value = True

        service = JobService()
        result = service.cancel_job("job123")

        assert result is True
        mock_repo.get_by_id.assert_called_once_with("job123")
        mock_update.assert_called_once()

    @patch("collector.services.job_service.JobRepository")
    def test_cancel_job_not_cancellable(self, mock_repo_class):
        """Test cancelling a job that can't be cancelled."""
        mock_job = Mock(spec=Job)
        mock_job.status = "completed"
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = mock_job

        service = JobService()
        result = service.cancel_job("job123")

        assert result is False
        mock_repo.get_by_id.assert_called_once_with("job123")

    @patch("collector.services.job_service.JobRepository")
    def test_get_job_statistics(self, mock_repo_class):
        """Test getting job statistics."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_stats = {"total_jobs": 10, "status_completed": 5}
        mock_repo.get_job_statistics.return_value = mock_stats

        service = JobService()
        result = service.get_job_statistics()

        assert result == mock_stats
        mock_repo.get_job_statistics.assert_called_once()

    @patch("collector.services.job_service.JobRepository")
    def test_cleanup_old_jobs(self, mock_repo_class):
        """Test cleaning up old jobs."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.cleanup_old_jobs.return_value = 5

        service = JobService()
        result = service.cleanup_old_jobs(30)

        assert result == 5
        mock_repo.cleanup_old_jobs.assert_called_once_with(30)
