"""Integration tests for database indexes.

This module tests that indexes are properly created and used for queries.
"""

import pytest

from src.collector.models.file import File
from src.collector.models.job import Job
from src.collector.models.settings import Settings


def test_jobs_indexes_exist(app):
    """Test that all job indexes are created."""
    from src.collector.config.database import DatabaseConfig

    with app.app_context():
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            # Get indexes for jobs table
            indexes = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='jobs' AND name LIKE 'idx_%'"
            ).fetchall()

            index_names = {row[0] for row in indexes}

            # Verify expected indexes exist
            expected_indexes = {
                "idx_jobs_status",
                "idx_jobs_platform",
                "idx_jobs_created_at",
                "idx_jobs_status_created",
            }

            assert expected_indexes.issubset(index_names), (
                f"Missing indexes: {expected_indexes - index_names}"
            )


def test_files_indexes_exist(app):
    """Test that all file indexes are created."""
    from src.collector.config.database import DatabaseConfig

    with app.app_context():
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            # Get indexes for files table
            indexes = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='files' AND name LIKE 'idx_%'"
            ).fetchall()

            index_names = {row[0] for row in indexes}

            # Verify expected indexes exist
            expected_indexes = {
                "idx_files_job_id",
                "idx_files_file_type",
                "idx_files_created_at",
                "idx_files_job_id_type",
            }

            assert expected_indexes.issubset(index_names), (
                f"Missing indexes: {expected_indexes - index_names}"
            )


def test_settings_has_no_custom_indexes(app):
    """Test that settings table has no custom indexes (only primary key)."""
    from src.collector.config.database import DatabaseConfig

    with app.app_context():
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            # Get indexes for settings table
            indexes = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='settings' AND name LIKE 'idx_%'"
            ).fetchall()

            # Should be empty (only auto-created primary key index exists)
            assert len(indexes) == 0, "Settings table should not have custom indexes"


def test_index_usage_on_active_jobs(app):
    """Test that get_active_jobs uses the status index."""
    from src.collector.config.database import DatabaseConfig
    from src.collector.repositories.job_repository import JobRepository

    with app.app_context():
        # Create some test jobs
        job_repo = JobRepository()

        job_repo.create_job("https://example.com/1", "youtube")
        job_repo.create_job("https://example.com/2", "instagram")
        job_repo.create_job("https://example.com/3", "youtube")

        # Check query plan
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            plan = conn.execute(
                "EXPLAIN QUERY PLAN "
                "SELECT * FROM jobs WHERE status IN ('pending', 'running', 'cancelling')"
            ).fetchall()

            # Verify index is used - convert rows to list of dicts for checking
            plan_list = [dict(row) for row in plan]
            plan_str = str(plan_list)

            # The query plan should use an index (either idx_jobs_status or idx_jobs_status_created)
            assert "INDEX" in plan_str.upper() or "idx_jobs" in plan_str, (
                f"Query should use an index. Plan: {plan_list}"
            )


def test_index_usage_on_job_files(app):
    """Test that get_job_files uses the job_id index."""
    from src.collector.config.database import DatabaseConfig
    from src.collector.repositories.file_repository import FileRepository
    from src.collector.repositories.job_repository import JobRepository

    with app.app_context():
        # Create test job and files
        job_repo = JobRepository()
        file_repo = FileRepository()

        job = job_repo.create_job("https://example.com", "youtube")
        file_repo.create_file(job.id, "/path/to/video.mp4", "video", 1024000)

        # Check query plan
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            plan = conn.execute(
                f"EXPLAIN QUERY PLAN SELECT * FROM files WHERE job_id = '{job.id}'"
            ).fetchall()

            # Verify index is used
            plan_list = [dict(row) for row in plan]
            plan_str = str(plan_list)

            assert "INDEX" in plan_str.upper() or "idx_files" in plan_str, (
                f"Query should use idx_files_job_id index. Plan: {plan_list}"
            )


def test_index_usage_on_recent_jobs(app):
    """Test that get_recent_jobs uses the created_at index."""
    from src.collector.config.database import DatabaseConfig
    from src.collector.repositories.job_repository import JobRepository

    with app.app_context():
        # Create some test jobs
        job_repo = JobRepository()

        job_repo.create_job("https://example.com/1", "youtube")
        job_repo.create_job("https://example.com/2", "instagram")

        # Check query plan
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10"
            ).fetchall()

            # Verify index is used
            plan_list = [dict(row) for row in plan]
            plan_str = str(plan_list)

            # The query should use an index on created_at
            assert (
                "INDEX" in plan_str.upper()
                or "B-tree" in plan_str.upper()
                or "idx_jobs" in plan_str
            ), f"Query should use an index. Plan: {plan_list}"


def test_index_usage_on_job_statistics(app):
    """Test that get_job_statistics uses the status index."""
    from src.collector.config.database import DatabaseConfig
    from src.collector.repositories.job_repository import JobRepository

    with app.app_context():
        # Create some test jobs
        job_repo = JobRepository()

        job_repo.create_job("https://example.com/1", "youtube")
        job_repo.create_job("https://example.com/2", "instagram")

        # Check query plan
        db_config = DatabaseConfig()

        with db_config.get_connection() as conn:
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
            ).fetchall()

            # Verify index is used
            plan_list = [dict(row) for row in plan]
            plan_str = str(plan_list)

            assert "INDEX" in plan_str.upper() or "idx_jobs" in plan_str, (
                f"Query should use idx_jobs_status index. Plan: {plan_list}"
            )


def test_get_index_info_method(app):
    """Test that get_index_info returns correct index information."""
    from src.collector.config.database import DatabaseConfig

    with app.app_context():
        db_config = DatabaseConfig()

        # Get indexes for jobs table
        job_indexes = db_config.get_index_info("jobs")

        # Verify we get the expected indexes
        assert len(job_indexes) > 0, "Should have indexes for jobs table"

        index_names = {idx["name"] for idx in job_indexes}
        assert "idx_jobs_status" in index_names
        assert "idx_jobs_platform" in index_names
        assert "idx_jobs_created_at" in index_names
        assert "idx_jobs_status_created" in index_names

        # Get indexes for files table
        file_indexes = db_config.get_index_info("files")

        # Verify we get the expected indexes
        assert len(file_indexes) > 0, "Should have indexes for files table"

        index_names = {idx["name"] for idx in file_indexes}
        assert "idx_files_job_id" in index_names
        assert "idx_files_file_type" in index_names
        assert "idx_files_created_at" in index_names
        assert "idx_files_job_id_type" in index_names


def test_ensure_indexes_is_idempotent(app):
    """Test that ensure_indexes can be called multiple times safely."""
    from src.collector.config.database import DatabaseConfig

    with app.app_context():
        db_config = DatabaseConfig()

        # Call ensure_indexes twice - should not fail
        from src.collector.models.job import Job
        from src.collector.models.file import File
        from src.collector.models.settings import Settings

        model_classes = [Job, File, Settings]

        # First call
        db_config.ensure_indexes(model_classes)

        # Second call - should not create duplicates or fail
        db_config.ensure_indexes(model_classes)

        # Verify indexes exist
        job_indexes = db_config.get_index_info("jobs")
        assert len(job_indexes) == 4, "Should have exactly 4 job indexes"
