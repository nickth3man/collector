# Route Integration Testing Implementation Plan

## 1. Overview

### Current Test Coverage Status
- **Services**: Fully covered with unit tests
  - `test_job_service.py` - JobService operations (create, update, cancel, delete, etc.)
  - `test_scraper_service.py` - ScraperService validation and platform detection
  - `test_session_service.py` - SessionService upload, delete, and management
- **Routes**: No integration tests currently
  - HTTP layer is untested
  - CSRF validation logic is untested in route context
  - HTMX vs non-HTMX response paths unverified

### Why Route Testing Matters

1. **HTTP Layer Validation**: Services handle business logic, but routes handle:
   - Request parsing and validation
   - Response formatting (HTML vs JSON vs HTMX fragments)
   - Status code selection
   - Header handling (HX-Request detection, CSRF tokens)

2. **CSRF Protection**: CSRF validation happens at route level:
   - Token generation and injection into templates
   - Token extraction from forms and headers
   - Validation on state-changing operations
   - Different error responses for HTMX vs regular requests

3. **HTMX Integration**: Routes have dual code paths:
   - HTMX requests return partial HTML fragments
   - Regular requests return full pages or redirects
   - Both paths must be tested independently

4. **Error Handling**: Route-level error handling:
   - 404 responses for missing resources
   - 400 responses for validation errors
   - 403 responses for CSRF failures
   - 500 responses for server errors
   - Different formats for HTMX vs regular requests

5. **Integration Between Components**: Routes integrate:
   - Multiple services (JobService, ScraperService, SessionService)
   - Security layer (CSRF, path validation)
   - Template rendering with context
   - Flask session management

## 2. Test Strategy

### Testing Approach

**Flask Test Client**: Use Flask's built-in test client for HTTP simulation
- Provides `client.get()`, `client.post()`, `client.delete()` methods
- Simulates requests without running a server
- Supports session management, headers, and cookies
- Returns response objects with status, data, headers

**Mocking Strategy**: Mock services to isolate HTTP layer
- Mock `JobService`, `ScraperService`, `SessionService`
- Mock repositories if needed (though services already mock them)
- Configure mock return values for different test scenarios
- Verify services are called with correct parameters

**Test Organization**:
- One test file per route blueprint
- Test class per route group
- Test method per specific scenario
- Use pytest fixtures for common setup

**HTMX Testing**:
- Set `HX-Request: true` header to simulate HTMX requests
- Verify HTMX-specific response formats (partial HTML, 204 status)
- Verify non-HTMX paths (full pages, redirects, flash messages)
- Test both code paths for each POST/DELETE route

**CSRF Testing**:
- Generate valid CSRF tokens using test session
- Test with valid token (should succeed)
- Test with missing token (should fail 403)
- Test with invalid token (should fail 403)
- Test HTMX vs non-HTMX CSRF error responses

**Path Security Testing**:
- Test path traversal attempts in browse/preview routes
- Verify path resolution respects download directory boundary
- Test with both valid and malicious paths

**Template Verification**:
- Verify correct templates are rendered
- Check template context contains expected data
- Verify partial templates for HTMX requests
- Verify full templates for regular requests

## 3. Test Inventory

### 3.1 Jobs Routes (`jobs.py`)

#### POST /download
**Purpose**: Accept URL input, create background job

**Test Cases**:
1. `test_download_with_valid_url_htmx` - HTMX request with valid YouTube URL
   - Valid CSRF token
   - HX-Request header
   - Mock ScraperService.validate_url() returns (True, None)
   - Mock ScraperService.detect_platform() returns "youtube"
   - Mock JobService.create_job() returns job object
   - Mock ExecutorAdapter.submit_job()
   - Assert: status 200, response contains job card HTML

2. `test_download_with_valid_url_regular` - Regular request with valid URL
   - Valid CSRF token
   - No HX-Request header
   - Mock services as above
   - Assert: redirect to index
   - Verify flash message "Download started"

3. `test_download_with_invalid_url_htmx` - HTMX request with invalid URL
   - Valid CSRF token
   - Mock ScraperService.validate_url() returns (False, "Invalid URL format")
   - Assert: status 400, error message in response

4. `test_download_with_invalid_url_regular` - Regular request with invalid URL
   - Valid CSRF token
   - Mock ScraperService.validate_url() returns (False, "Invalid URL format")
   - Assert: redirect to index
   - Verify flash error message

5. `test_download_platform_detection_fails_htmx` - Platform detection failure (HTMX)
   - Valid URL but detect_platform() returns None
   - Assert: status 400, error message

6. `test_download_missing_csrf_token_htmx` - Missing CSRF token (HTMX)
   - No CSRF token in form or headers
   - Assert: status 403, CSRF error in response

7. `test_download_missing_csrf_token_regular` - Missing CSRF token (regular)
   - No CSRF token
   - Assert: abort(403) raised

8. `test_download_invalid_csrf_token` - Invalid CSRF token
   - CSRF token doesn't match session
   - Assert: 403 response

#### GET /job/<job_id>
**Purpose**: Job detail page or HTMX partial

**Test Cases**:
1. `test_job_detail_found_htmx` - Job found via HTMX
   - Mock JobService.get_job() returns job
   - Mock JobService.get_job_files() returns files
   - HX-Request header
   - Assert: status 200, partial template rendered

2. `test_job_detail_found_regular` - Job found, regular request
   - Mock JobService.get_job() returns job
   - No HX-Request header
   - Assert: status 200, full template rendered

3. `test_job_detail_not_found_htmx` - Job not found via HTMX
   - Mock JobService.get_job() returns None
   - HX-Request header
   - Assert: status 404

4. `test_job_detail_not_found_regular` - Job not found, regular request
   - Mock JobService.get_job() returns None
   - Assert: abort(404) raised

#### GET /job/<job_id>/status
**Purpose**: Job status for HTMX polling

**Test Cases**:
1. `test_job_status_found` - Job found
   - Mock JobService.get_job() returns job
   - Mock JobService.get_job_files() returns files
   - Assert: status 200, partial template rendered

2. `test_job_status_not_found` - Job not found
   - Mock JobService.get_job() returns None
   - Assert: abort(404) raised

#### GET /jobs/active
**Purpose**: Active jobs as HTMX fragment

**Test Cases**:
1. `test_active_jobs_with_jobs` - Has active jobs
   - Mock JobService.get_active_jobs() returns list of jobs
   - Assert: status 200, partial template rendered with jobs

2. `test_active_jobs_empty` - No active jobs
   - Mock JobService.get_active_jobs() returns empty list
   - Assert: status 200, partial template rendered (empty)

#### POST /job/<job_id>/cancel
**Purpose**: Cancel a running job

**Test Cases**:
1. `test_cancel_job_success_htmx` - Successful cancellation via HTMX
   - Valid CSRF token
   - Mock JobService.get_job() returns pending job
   - Mock JobService.cancel_job() returns True
   - HX-Request header
   - Assert: status 204, empty response

2. `test_cancel_job_success_regular` - Successful cancellation, regular request
   - Valid CSRF token
   - Mock JobService.cancel_job() returns True
   - No HX-Request header
   - Assert: redirect to index
   - Verify flash success message

3. `test_cancel_job_not_cancellable_htmx` - Job can't be cancelled
   - Valid CSRF token
   - Mock JobService.cancel_job() returns False
   - HX-Request header
   - Note: Current implementation redirects even with HTMX
   - Assert: redirect to index
   - Verify flash error message

4. `test_cancel_job_not_found` - Job doesn't exist
   - Valid CSRF token
   - Mock JobService.get_job() returns None
   - Assert: abort(404) raised

5. `test_cancel_job_missing_csrf` - Missing CSRF token
   - No CSRF token
   - Assert: abort(403) raised

#### POST /job/<job_id>/retry
**Purpose**: Retry a failed job

**Test Cases**:
1. `test_retry_job_success_htmx` - Successful retry via HTMX
   - Valid CSRF token
   - Mock JobService.prepare_retry_job() returns new job
   - Mock ExecutorAdapter.submit_job()
   - HX-Request header
   - Assert: status 200, job card HTML in response

2. `test_retry_job_success_regular` - Successful retry, regular request
   - Valid CSRF token
   - Mock JobService.prepare_retry_job() returns new job
   - No HX-Request header
   - Assert: redirect to index
   - Verify flash success message

3. `test_retry_job_not_failed_regular` - Job not in failed state
   - Valid CSRF token
   - Mock JobService.prepare_retry_job() returns None
   - Assert: redirect to index
   - Verify flash error message

4. `test_retry_job_missing_csrf` - Missing CSRF token
   - No CSRF token
   - Assert: abort(403) raised

#### DELETE /job/<job_id>
**Purpose**: Delete a job and its files

**Test Cases**:
1. `test_delete_job_success_htmx` - Successful deletion via HTMX
   - Valid CSRF token
   - Mock JobService.delete_job() returns True
   - HX-Request header
   - Assert: status 204, empty response

2. `test_delete_job_success_regular` - Successful deletion, regular request
   - Valid CSRF token
   - Mock JobService.delete_job() returns True
   - No HX-Request header
   - Assert: redirect to history
   - Verify flash success message

3. `test_delete_job_not_found_htmx` - Job not found via HTMX
   - Valid CSRF token
   - Mock JobService.delete_job() returns False
   - HX-Request header
   - Assert: status 404, error message in response

4. `test_delete_job_not_found_regular` - Job not found, regular request
   - Valid CSRF token
   - Mock JobService.delete_job() returns False
   - No HX-Request header
   - Assert: redirect to history
   - Verify flash error message

5. `test_delete_job_missing_csrf` - Missing CSRF token
   - No CSRF token
   - Assert: abort(403) raised

### 3.2 Pages Routes (`pages.py`)

#### GET /
**Purpose**: Dashboard with URL input and active jobs

**Test Cases**:
1. `test_index_page` - Render dashboard
   - Assert: status 200
   - Verify template is dashboard.html
   - Verify CSRF token in template context

#### GET /browse and /browse/<path:subpath>
**Purpose**: Browse downloaded content

**Test Cases**:
1. `test_browse_root_directory` - Browse root download directory
   - Mock download directory exists
   - Create test files and subdirectories
   - Assert: status 200
   - Verify template contains directory listing
   - Verify items sorted correctly (directories first)

2. `test_browse_subdirectory` - Browse subdirectory
   - Create test subdirectory with files
   - Assert: status 200
   - Verify correct subpath in context
   - Verify breadcrumb navigation

3. `test_browse_path_not_found` - Path doesn't exist
   - Mock non-existent path
   - Assert: redirect to /browse
   - Verify flash error message

4. `test_browse_path_traversal_attack` - Path traversal attempt
   - Use subpath with "../" sequences
   - Assert: abort(403) raised (PathSecurityError)

5. `test_browse_file_download` - Browse to a file (not directory)
   - Create test file
   - Mock safe_send_file() to return file response
   - Assert: file response returned (not HTML)

6. `test_browse_absolute_path_attack` - Absolute path attempt
   - Use absolute path as subpath
   - Assert: abort(403) raised

#### GET /preview/<path:filepath>
**Purpose**: Preview a file with inline display

**Test Cases**:
1. `test_preview_image_file` - Preview image file
   - Create test .jpg file
   - Assert: status 200
   - Verify file_type="image" in context
   - Verify template includes image tag

2. `test_preview_video_file` - Preview video file
   - Create test .mp4 file
   - Assert: status 200
   - Verify file_type="video" in context

3. `test_preview_transcript_file` - Preview transcript file
   - Create test transcript.txt file
   - Assert: status 200
   - Verify file_type="transcript" in context
   - Verify content read and included

4. `test_preview_metadata_file` - Preview metadata file
   - Create test .json file
   - Assert: status 200
   - Verify file_type="metadata" in context
   - Verify JSON content parsed and displayed

5. `test_preview_audio_file` - Preview audio file
   - Create test .mp3 file
   - Assert: status 200
   - Verify file_type="audio" in context

6. `test_preview_unknown_file_type` - Preview unknown file type
   - Create test .xyz file
   - Assert: status 200
   - Verify file_type="unknown" in context

7. `test_preview_directory_redirects` - Preview path to directory
   - Create test directory
   - Assert: redirect to browse

8. `test_preview_file_not_found` - File doesn't exist
   - Mock non-existent file path
   - Assert: abort(404) raised

9. `test_preview_path_traversal_attack` - Path traversal attempt
   - Use filepath with "../" sequences
   - Assert: abort(403) raised

10. `test_preview_file_read_error` - Error reading file
    - Mock file that raises permission error
    - Assert: status 200
    - Verify error message in content

#### GET /history
**Purpose**: Download history with filters

**Test Cases**:
1. `test_history_no_filters` - History without filters
   - Mock JobService.list_jobs() returns job list
   - Assert: status 200
   - Verify jobs in template context
   - Verify filters empty in context

2. `test_history_with_platform_filter` - Filter by platform
   - GET request with ?platform=youtube
   - Mock JobService.list_jobs(platform="youtube")
   - Assert: status 200
   - Verify platform filter in context

3. `test_history_with_status_filter` - Filter by status
   - GET request with ?status=completed
   - Mock JobService.list_jobs(status="completed")
   - Assert: status 200
   - Verify status filter in context

4. `test_history_with_both_filters` - Filter by platform and status
   - GET request with ?platform=youtube&status=completed
   - Mock JobService.list_jobs(platform="youtube", status="completed")
   - Assert: status 200
   - Verify both filters in context

### 3.3 Sessions Routes (`sessions.py`)

#### GET /sessions
**Purpose**: List all saved Instagram sessions

**Test Cases**:
1. `test_list_sessions_success` - Successfully list sessions
   - Mock SessionService.list_sessions() returns sessions
   - Assert: status 200
   - Verify sessions in template context

2. `test_list_sessions_empty` - No sessions exist
   - Mock SessionService.list_sessions() returns empty list
   - Assert: status 200
   - Verify empty list in context

3. `test_list_sessions_service_error` - Service returns error
   - Mock SessionService.list_sessions() returns success=False
   - Assert: status 200
   - Verify flash error message

4. `test_list_sessions_exception` - Service raises exception
   - Mock SessionService.list_sessions() raises exception
   - Assert: redirect to index
   - Verify flash error message

#### POST /sessions/upload
**Purpose**: Upload a cookies.txt file to create a session

**Test Cases**:
1. `test_upload_session_success_htmx` - Successful upload via HTMX
   - Valid CSRF token
   - Upload valid cookies.txt file
   - Mock SessionService.upload_session() returns success=True
   - HX-Request header
   - Assert: status 200, success message in response

2. `test_upload_session_success_regular` - Successful upload, regular request
   - Valid CSRF token
   - Upload valid cookies.txt file
   - Mock SessionService.upload_session() returns success=True
   - No HX-Request header
   - Assert: redirect to sessions
   - Verify flash success message

3. `test_upload_session_no_file_htmx` - No file uploaded (HTMX)
   - Valid CSRF token
   - No file in request.files
   - HX-Request header
   - Assert: status 400, error message in response

4. `test_upload_session_no_file_regular` - No file uploaded (regular)
   - Valid CSRF token
   - No file in request.files
   - No HX-Request header
   - Assert: redirect to sessions
   - Verify flash error message

5. `test_upload_session_empty_filename_htmx` - Empty filename (HTMX)
   - Valid CSRF token
   - File with empty filename
   - HX-Request header
   - Assert: status 400, error message in response

6. `test_upload_session_wrong_extension_htmx` - Wrong file extension (HTMX)
   - Valid CSRF token
   - Upload file.json instead of cookies.txt
   - HX-Request header
   - Assert: status 400, extension error in response

7. `test_upload_session_service_error_htmx` - Service processing error (HTMX)
   - Valid CSRF token
   - Upload valid cookies.txt
   - Mock SessionService.upload_session() returns success=False with error
   - HX-Request header
   - Assert: status 400, error message in response

8. `test_upload_session_exception_htmx` - Service raises exception (HTMX)
   - Valid CSRF token
   - Upload valid cookies.txt
   - Mock SessionService.upload_session() raises exception
   - HX-Request header
   - Assert: status 500, error message in response

9. `test_upload_session_missing_csrf` - Missing CSRF token
   - No CSRF token
   - Assert: abort(403) raised

#### POST /sessions/<username>/delete
**Purpose**: Delete a saved session

**Test Cases**:
1. `test_delete_session_success_htmx` - Successful deletion via HTMX
   - Valid CSRF token
   - Mock SessionService.delete_session() returns success=True
   - HX-Request header
   - Assert: status 204, empty response

2. `test_delete_session_success_regular` - Successful deletion, regular request
   - Valid CSRF token
   - Mock SessionService.delete_session() returns success=True
   - No HX-Request header
   - Assert: redirect to sessions
   - Verify flash success message

3. `test_delete_session_not_found_htmx` - Session not found (HTMX)
   - Valid CSRF token
   - Mock SessionService.delete_session() returns success=False
   - HX-Request header
   - Assert: status 404, error message in response

4. `test_delete_session_not_found_regular` - Session not found (regular)
   - Valid CSRF token
   - Mock SessionService.delete_session() returns success=False
   - No HX-Request header
   - Assert: redirect to sessions
   - Verify flash error message

5. `test_delete_session_exception_htmx` - Service raises exception (HTMX)
   - Valid CSRF token
   - Mock SessionService.delete_session() raises exception
   - HX-Request header
   - Assert: status 500, error message in response

6. `test_delete_session_missing_csrf` - Missing CSRF token
   - No CSRF token
   - Assert: abort(403) raised

### 3.4 API Routes (`api.py`)

#### GET /api/config/status
**Purpose**: Get configuration status for UI

**Test Cases**:
1. `test_config_status_success` - Successfully get config
   - Mock SessionService.get_config_status() returns success=True
   - Assert: status 200
   - Verify JSON response with encryption_enabled and downloads_dir

2. `test_config_status_service_error` - Service returns error
   - Mock SessionService.get_config_status() returns success=False
   - Assert: status 200
   - Verify JSON fallback (encryption_enabled=False, downloads_dir from config)

3. `test_config_status_exception` - Service raises exception
   - Mock SessionService.get_config_status() raises exception
   - Assert: status 200
   - Verify JSON fallback

## 4. Fixture Requirements

Add to `tests/conftest.py`:

### 4.1 Flask App Fixtures

```python
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
        "WTF_CSRF_ENABLED": True,
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
def client(app: Flask):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Flask CLI test runner."""
    return app.test_cli_runner()
```

### 4.2 Service Mock Fixtures

```python
@pytest.fixture
def mock_job_service():
    """Mock JobService."""
    with patch("collector.services.JobService") as mock:
        yield mock


@pytest.fixture
def mock_scraper_service():
    """Mock ScraperService."""
    with patch("collector.services.ScraperService") as mock:
        yield mock


@pytest.fixture
def mock_session_service():
    """Mock SessionService."""
    with patch("collector.services.SessionService") as mock:
        yield mock


@pytest.fixture
def mock_executor_adapter():
    """Mock ExecutorAdapter."""
    with patch("collector.services.ExecutorAdapter") as mock:
        yield mock
```

### 4.3 CSRF Token Fixtures

```python
@pytest.fixture
def csrf_token(client):
    """Get valid CSRF token from session."""
    from flask import session

    with client.session_transaction() as sess:
        # Use the CSRF generation from the app
        from collector.security.csrf import generate_csrf_token
        token = generate_csrf_token()
        sess["_csrf_token"] = token

    return token


@pytest.fixture
def csrf_headers(csrf_token: str):
    """Headers with CSRF token for HTMX requests."""
    return {"X-CSRFToken": csrf_token}


@pytest.fixture
def htmx_headers(csrf_headers: dict):
    """Headers for HTMX requests including CSRF token."""
    headers = csrf_headers.copy()
    headers["HX-Request"] = "true"
    return headers
```

### 4.4 Test Data Fixtures

```python
@pytest.fixture
def sample_job():
    """Sample job object for testing."""
    from collector.models.job import Job
    from datetime import datetime

    job = Job(
        id="test-job-123",
        url="https://www.youtube.com/watch?v=test123",
        platform="youtube",
        title="Test Video",
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return job


@pytest.fixture
def sample_file():
    """Sample file object for testing."""
    from collector.models.file import File
    from datetime import datetime

    file = File(
        id=1,
        job_id="test-job-123",
        file_type="video",
        file_path="downloads/youtube/test/video.mp4",
        size_bytes=1024000,
        created_at=datetime.now(),
    )
    return file
```

### 4.5 Helper Fixtures

```python
@pytest.fixture
def with_session(client):
    """Context manager for working with Flask session."""
    from flask import session

    class SessionManager:
        def set(self, key, value):
            with client.session_transaction() as sess:
                sess[key] = value

        def get(self, key):
            with client.session_transaction() as sess:
                return sess.get(key)

        def clear(self):
            with client.session_transaction() as sess:
                sess.clear()

    return SessionManager()
```

## 5. Test Structure Template

### Standard Test Structure

```python
"""Tests for <route_module> routes."""

from __future__ import annotations

from unittest.mock import Mock, patch
from flask import Flask

import pytest


class Test<RouteGroupName>:
    """Test cases for <route_group> routes."""

    def test_route_name_success(self, client, mock_service, csrf_token):
        """Test that route_name does X on success."""
        # Arrange
        mock_service.method.return_value = expected_value
        data = {"param1": "value1", "csrf_token": csrf_token}

        # Act
        response = client.post('/route', data=data)

        # Assert
        assert response.status_code == 200
        assert b"expected content" in response.data
        mock_service.method.assert_called_once_with(expected_args)

    def test_route_name_htmx(self, client, mock_service, htmx_headers):
        """Test that route_name returns HTMX partial."""
        # Arrange
        mock_service.method.return_value = expected_value
        data = {"param1": "value1"}

        # Act
        response = client.post('/route', data=data, headers=htmx_headers)

        # Assert
        assert response.status_code == 200
        assert b"<div" in response.data  # HTML fragment
        # Verify partial template was rendered

    def test_route_name_csrf_failure(self, client):
        """Test that route_name rejects invalid CSRF token."""
        # Arrange
        data = {"param1": "value1", "csrf_token": "invalid-token"}

        # Act
        response = client.post('/route', data=data)

        # Assert
        assert response.status_code == 403

    def test_route_name_not_found(self, client, mock_service, csrf_token):
        """Test that route_name returns 404 for missing resource."""
        # Arrange
        mock_service.method.return_value = None
        data = {"csrf_token": csrf_token}

        # Act
        response = client.post('/route', data=data)

        # Assert
        assert response.status_code == 404
```

### Parameterized Test Structure

```python
@pytest.mark.parametrize(
    "url,expected_valid,expected_platform",
    [
        ("https://www.youtube.com/watch?v=test", True, "youtube"),
        ("https://instagram.com/p/test", True, "instagram"),
        ("invalid-url", False, None),
        ("", False, None),
    ],
)
def test_download_with_various_urls(
    client, mock_scraper_service, mock_job_service, csrf_token, url, expected_valid, expected_platform
):
    """Test download route with various URL formats."""
    # Arrange
    mock_scraper_service.validate_url.return_value = (expected_valid, None if expected_valid else "Invalid URL")
    mock_scraper_service.detect_platform.return_value = expected_platform

    # Act
    response = client.post("/download", data={"url": url, "csrf_token": csrf_token})

    # Assert
    if expected_valid:
        assert response.status_code in [200, 302]  # HTMX or redirect
    else:
        assert response.status_code in [400, 302]  # Error HTMX or redirect
```

## 6. Implementation Steps

### Step 1: Update conftest.py
- Add Flask app fixture with test configuration
- Add Flask test client fixture
- Add service mock fixtures (JobService, ScraperService, SessionService)
- Add CSRF token fixtures
- Add test data fixtures (sample_job, sample_file)
- Add helper fixtures (with_session)
- Run pytest to verify fixtures work

### Step 2: Create test_jobs_routes.py
- Create test file structure with TestJobsRoutes class
- Implement all POST /download tests (8 test cases)
- Implement all GET /job/<id> tests (4 test cases)
- Implement all GET /job/<id>/status tests (2 test cases)
- Implement all GET /jobs/active tests (2 test cases)
- Implement all POST /job/<id>/cancel tests (5 test cases)
- Implement all POST /job/<id>/retry tests (4 test cases)
- Implement all DELETE /job/<id> tests (5 test cases)
- Run pytest on test_jobs_routes.py and fix any failures
- Verify all 30 job route tests pass

### Step 3: Create test_pages_routes.py
- Create test file structure with TestPagesRoutes class
- Implement GET / tests (1 test case)
- Implement GET /browse tests (6 test cases)
- Implement GET /preview tests (10 test cases)
- Implement GET /history tests (4 test cases)
- Create temporary files and directories for testing
- Run pytest on test_pages_routes.py and fix any failures
- Verify all 21 page route tests pass

### Step 4: Create test_sessions_routes.py
- Create test file structure with TestSessionsRoutes class
- Implement GET /sessions tests (4 test cases)
- Implement POST /sessions/upload tests (9 test cases)
- Implement POST /sessions/<username>/delete tests (6 test cases)
- Create test cookies.txt file for upload tests
- Run pytest on test_sessions_routes.py and fix any failures
- Verify all 19 session route tests pass

### Step 5: Create test_api_routes.py
- Create test file structure with TestApiRoutes class
- Implement GET /api/config/status tests (3 test cases)
- Run pytest on test_api_routes.py and fix any failures
- Verify all 3 API route tests pass

### Step 6: Integration and Verification
- Run full test suite: `pytest tests/`
- Verify all existing unit tests still pass
- Verify all new route tests pass
- Check test coverage: `pytest --cov=collector routes/`
- Ensure route coverage is >90%
- Fix any failing tests
- Update documentation if needed

## 7. Specific Test Cases

### 7.1 CSRF Validation Tests

**Pattern for all POST/DELETE routes:**

```python
def test_<route>_missing_csrf_token(self, client):
    """Test <route> rejects request without CSRF token."""
    # Arrange
    data = {"param": "value"}  # No csrf_token

    # Act
    response = client.post('/route', data=data)

    # Assert
    assert response.status_code == 403

def test_<route>_invalid_csrf_token(self, client):
    """Test <route> rejects request with invalid CSRF token."""
    # Arrange
    data = {"param": "value", "csrf_token": "wrong-token"}

    # Act
    response = client.post('/route', data=data)

    # Assert
    assert response.status_code == 403
```

### 7.2 HTMX vs Non-HTMX Response Tests

**Pattern for routes with dual responses:**

```python
def test_<route>_htmx_response(self, client, htmx_headers):
    """Test <route> returns HTMX partial."""
    # Act
    response = client.post('/route', headers=htmx_headers)

    # Assert
    assert response.status_code == 200
    assert b"<div" in response.data  # HTML fragment
    assert b"DOCTYPE" not in response.data  # Not full HTML

def test_<route>_regular_response(self, client):
    """Test <route> returns full page or redirect."""
    # Act
    response = client.post('/route')

    # Assert
    assert response.status_code in [200, 302]
    if response.status_code == 200:
        assert b"DOCTYPE" in response.data or b"<html" in response.data
```

### 7.3 Error Condition Tests

**Pattern for service-level errors:**

```python
def test_<route>_service_error(self, client, mock_service, csrf_token):
    """Test <route> handles service errors gracefully."""
    # Arrange
    mock_service.method.side_effect = Exception("Service error")

    # Act
    response = client.post('/route', data={"csrf_token": csrf_token})

    # Assert
    assert response.status_code in [400, 500, 302]  # Depends on route

def test_<route>_resource_not_found(self, client, mock_service, csrf_token):
    """Test <route> returns 404 for missing resource."""
    # Arrange
    mock_service.get_by_id.return_value = None

    # Act
    response = client.post('/route/123', data={"csrf_token": csrf_token})

    # Assert
    assert response.status_code == 404
```

### 7.4 Path Security Tests

**Pattern for browse/preview routes:**

```python
def test_browse_path_traversal_attack(self, client):
    """Test browse route rejects path traversal attempts."""
    # Arrange
    malicious_subpath = "../../../etc/passwd"

    # Act
    response = client.get(f'/browse/{malicious_subpath}')

    # Assert
    assert response.status_code == 403

def test_preview_absolute_path_attack(self, client):
    """Test preview route rejects absolute paths."""
    # Arrange
    malicious_path = "/etc/passwd"

    # Act
    response = client.get(f'/preview/{malicious_path}')

    # Assert
    assert response.status_code == 403
```

## 8. Code Examples

### Example 1: POST Request with CSRF and HTMX

```python
def test_download_with_valid_url_htmx(
    self, client, mock_scraper_service, mock_job_service, mock_executor_adapter, htmx_headers
):
    """Test download route with valid URL via HTMX."""
    # Arrange
    from datetime import datetime
    from collector.models.job import Job

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

    # Act
    response = client.post(
        "/download",
        data={"url": test_url},
        headers=htmx_headers,
    )

    # Assert
    assert response.status_code == 200
    assert b"job-123" in response.data or b"Test Video" in response.data
    mock_scraper_service.return_value.validate_url.assert_called_once_with(test_url)
    mock_scraper_service.return_value.detect_platform.assert_called_once_with(test_url)
    mock_job_service.return_value.create_job.assert_called_once()
    mock_executor_adapter.return_value.submit_job.assert_called_once()
```

### Example 2: GET Request with Template Verification

```python
def test_job_detail_found_htmx(self, client, mock_job_service):
    """Test job detail page renders HTMX partial."""
    # Arrange
    from datetime import datetime
    from collector.models.job import Job

    test_job = Job(
        id="job-123",
        url="https://youtube.com/watch?v=test",
        platform="youtube",
        title="Test Video",
        status="completed",
        progress=100,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    test_files = [
        Mock(file_type="video", file_path="video.mp4", size_bytes=1024000),
        Mock(file_type="thumbnail", file_path="thumb.jpg", size_bytes=50000),
    ]

    mock_job_service.return_value.get_job.return_value = test_job
    mock_job_service.return_value.get_job_files.return_value = test_files

    # Act
    response = client.get(
        "/job/job-123",
        headers={"HX-Request": "true"}
    )

    # Assert
    assert response.status_code == 200
    assert b"Test Video" in response.data
    assert b"video.mp4" in response.data
    # Verify it's a partial (not a full HTML page)
    assert b"DOCTYPE" not in response.data
    mock_job_service.return_value.get_job.assert_called_once_with("job-123")
    mock_job_service.return_value.get_job_files.assert_called_once_with("job-123")
```

### Example 3: DELETE Request with Error Handling

```python
def test_delete_job_not_found_htmx(self, client, mock_job_service, csrf_token):
    """Test delete job returns 404 when job doesn't exist via HTMX."""
    # Arrange
    mock_job_service.return_value.delete_job.return_value = False

    # Act
    response = client.delete(
        "/job/nonexistent-job",
        headers={
            "X-CSRFToken": csrf_token,
            "HX-Request": "true"
        }
    )

    # Assert
    assert response.status_code == 404
    assert b"not found" in response.data.lower()
    mock_job_service.return_value.delete_job.assert_called_once_with(
        "nonexistent-job", delete_files=True
    )
```

### Example 4: File Upload Test

```python
def test_upload_session_success_htmx(self, client, mock_session_service, csrf_token):
    """Test successful session upload via HTMX."""
    # Arrange
    from io import BytesIO

    cookies_content = "cookie1=value1\ncookie2=value2"
    cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

    mock_session_service.return_value.upload_session.return_value = {
        "success": True,
        "username": "testuser"
    }

    # Act
    response = client.post(
        "/sessions/upload",
        data={"cookies_file": cookies_file},
        headers={
            "X-CSRFToken": csrf_token,
            "HX-Request": "true"
        },
        content_type="multipart/form-data"
    )

    # Assert
    assert response.status_code == 200
    assert b"success" in response.data.lower() or b"uploaded" in response.data.lower()
    mock_session_service.return_value.upload_session.assert_called_once()
```

### Example 5: Path Security Test

```python
def test_browse_path_traversal_attack(self, client):
    """Test browse route blocks path traversal attacks."""
    # Arrange
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/passwd",
        "C:\\Windows\\System32\\config",
    ]

    for malicious_path in malicious_paths:
        # Act
        response = client.get(f"/browse/{malicious_path}")

        # Assert
        assert response.status_code == 403, f"Should reject path: {malicious_path}"
```

### Example 6: Filter and Parameter Tests

```python
def test_history_with_filters(self, client, mock_job_service):
    """Test history route with platform and status filters."""
    # Arrange
    from datetime import datetime
    from collector.models.job import Job

    test_jobs = [
        Job(
            id=f"job-{i}",
            url=f"https://youtube.com/watch?v={i}",
            platform="youtube",
            title=f"Video {i}",
            status="completed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        for i in range(5)
    ]

    mock_job_service.return_value.list_jobs.return_value = test_jobs

    # Act
    response = client.get("/history?platform=youtube&status=completed")

    # Assert
    assert response.status_code == 200
    mock_job_service.return_value.list_jobs.assert_called_once_with(
        platform="youtube",
        status="completed",
        limit=200
    )
```

## 9. Success Criteria

### Implementation Complete When:
1. All 4 test files created (jobs, pages, sessions, api)
2. conftest.py updated with all required fixtures
3. All 73+ tests pass (30 jobs + 21 pages + 19 sessions + 3 api)
4. Test coverage for routes > 90%
5. All existing unit tests still pass
6. No regression in application functionality
7. Tests run quickly (< 5 seconds total)
8. Tests are maintainable and well-documented

### Test Coverage Goals:
- CSRF validation: 100% (all state-changing routes)
- HTMX vs non-HTMX paths: 100% (all applicable routes)
- Error handling: 100% (all error conditions)
- Path security: 100% (browse/preview routes)
- Service integration: 100% (all routes that use services)

## 10. Notes and Considerations

### Mocking Strategy
- Mock services at the import level using `patch()` decorator
- Use `return_value` for methods that return data
- Use `side_effect` for methods that raise exceptions
- Verify calls with `assert_called_once_with()` or `assert_called_with()`

### Session Management
- Flask test client supports session persistence
- Use `client.session_transaction()` to modify session
- CSRF tokens are stored in session by `before_request` handler

### File Upload Testing
- Use `io.BytesIO` to simulate file uploads
- Set proper `content_type="multipart/form-data"` header
- Include filename in file tuple: `(BytesIO(content), "filename.txt")`

### Path Security Testing
- Test various path traversal patterns
- Test both Unix and Windows path separators
- Verify absolute paths are rejected
- Verify symbolic link attacks are blocked (if applicable)

### Template Testing
- Check for specific HTML content in response.data
- Verify partial templates for HTMX (no DOCTYPE)
- Verify full templates for regular requests
- Check template context indirectly via rendered content

### Cleanup
- Use tmp_path fixture for temporary files
- Clean up test database between tests
- Ensure mock patches are properly scoped
- Close client connections if needed

### Performance
- Keep tests fast by avoiding I/O where possible
- Use in-memory database for testing
- Mock external service calls
- Avoid unnecessary sleep() calls
