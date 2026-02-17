"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path for tests."""
    return tmp_path / "test.db"


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    """Provide a temporary download directory for tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


@pytest.fixture
def app_config_overrides() -> dict[str, str]:
    """Temporary config overrides for tests."""
    return {}


# ============================================================================
# Flask App Fixtures
# ============================================================================

@pytest.fixture
def app(app_config_overrides: dict[str, str], tmp_db_path: Path, tmp_download_dir: Path):
    """Create Flask app for testing with test configuration."""
    from collector import create_app

    # Override config for testing
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SCRAPER_DB_PATH": str(tmp_db_path),
        "SCRAPER_DOWNLOAD_DIR": str(tmp_download_dir),
        "WTF_CSRF_ENABLED": False,  # Disable WTForms CSRF
    }
    test_config.update(app_config_overrides)

    # Create app
    app = create_app()
    app.config.update(test_config)

    # Initialize database schema
    with app.app_context():
        from collector.repositories.job_repository import JobRepository
        from collector.repositories.file_repository import FileRepository
        from collector.repositories.settings_repository import SettingsRepository

        JobRepository()
        FileRepository()
        SettingsRepository()

    yield app

    # Cleanup
    if tmp_db_path.exists():
        tmp_db_path.unlink()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()


# ============================================================================
# Service Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_job_service():
    """Mock JobService."""
    from unittest.mock import patch
    with patch("collector.routes.jobs.JobService") as mock:
        yield mock


@pytest.fixture
def mock_job_service_for_pages():
    """Mock JobService for pages routes."""
    from unittest.mock import patch
    with patch("collector.routes.pages.JobService") as mock:
        yield mock


@pytest.fixture
def mock_scraper_service():
    """Mock ScraperService."""
    from unittest.mock import patch
    with patch("collector.routes.jobs.ScraperService") as mock:
        yield mock


@pytest.fixture
def mock_session_service():
    """Mock SessionService."""
    from unittest.mock import patch
    with patch("collector.routes.sessions.SessionService") as mock:
        yield mock


@pytest.fixture
def mock_executor_adapter():
    """Mock ExecutorAdapter."""
    from unittest.mock import patch
    with patch("collector.routes.jobs.ExecutorAdapter") as mock:
        yield mock


# ============================================================================
# CSRF Token Fixtures
# ============================================================================

@pytest.fixture
def csrf_token(client):
    """Get valid CSRF token from session."""
    with client.session_transaction() as sess:
        from collector.security.csrf import generate_csrf_token
        token = generate_csrf_token()
        sess["_csrf_token"] = token
        # Also make it available as a regular session attribute
        sess["csrf_token"] = token
    return token


@pytest.fixture
def csrf_headers(csrf_token: str):
    """Headers with CSRF token for requests."""
    return {"X-CSRFToken": csrf_token}


@pytest.fixture
def htmx_headers(csrf_token: str):
    """Headers for HTMX requests including CSRF token."""
    return {
        "X-CSRFToken": csrf_token,
        "HX-Request": "true"
    }


@pytest.fixture
def mock_csrf_validation():
    """Mock CSRF validation to always pass for tests."""
    from unittest.mock import patch
    # Patch at the import locations in the route modules
    with patch("collector.routes.jobs.validate_csrf_request", return_value=True), \
         patch("collector.routes.sessions.validate_csrf_request", return_value=True):
        yield


@pytest.fixture
def auto_mock_csrf():
    """Mock CSRF validation for tests (use explicitly for non-CSRF tests)."""
    from unittest.mock import patch
    # Patch at the import locations in the route modules
    with patch("collector.routes.jobs.validate_csrf_request", return_value=True), \
         patch("collector.routes.sessions.validate_csrf_request", return_value=True):
        yield


@pytest.fixture(autouse=True)
def auto_mock_templates():
    """Automatically mock template rendering for tests."""
    from unittest.mock import patch
    # Return HTML string that Flask will wrap in a response
    mock_html = "<div>Mock template response with <input name='csrf_token' value='test-token'/></div>"

    with patch("collector.routes.jobs.render_template", return_value=mock_html), \
         patch("collector.routes.pages.render_template", return_value=mock_html), \
         patch("collector.routes.sessions.render_template", return_value=mock_html), \
         patch("flask.render_template", return_value=mock_html):
        yield


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job():
    """Sample job object for testing."""
    from collector.models.job import Job
    return Job(
        id="test-job-123",
        url="https://www.youtube.com/watch?v=test123",
        platform="youtube",
        title="Test Video",
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_file():
    """Sample file object for testing."""
    from collector.models.file import File
    return File(
        id=1,
        job_id="test-job-123",
        file_type="video",
        file_path="downloads/youtube/test/video.mp4",
        size_bytes=1024000,
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_session():
    """Sample session object for testing."""
    return {
        "username": "testuser",
        "created_at": datetime.now().isoformat(),
        "cookies_count": 5,
    }
