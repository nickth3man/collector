# Implementation Plan: Route Handler Documentation

## 1. Overview

### Current State
As of the initial codebase assessment, approximately **50% of route handlers have docstrings**. While some routes have basic one-line summaries, most lack comprehensive documentation including:
- Detailed descriptions of functionality
- HTMX behavior notes
- CSRF requirements
- Return type specifications
- Error conditions

### Target State
Achieve **100% documentation coverage** for all route handlers with:
- Comprehensive Google-style docstrings
- HTMX behavior documentation
- CSRF requirement notes
- Return type specifications
- Error handling documentation

### Why Route Documentation Matters

1. **API Documentation**: Route handlers serve as the primary interface for the application. Well-documented routes enable automatic API documentation generation and help developers understand available endpoints.

2. **Maintainability**: Clear documentation reduces cognitive load when maintaining or extending routes. Future contributors can quickly understand purpose, behavior, and requirements.

3. **HTMX Integration**: The application heavily uses HTMX for dynamic UI updates. Documenting HTMX-specific behavior (fragments, headers, polling) is crucial for understanding the frontend-backend contract.

4. **Security Awareness**: Explicit documentation of CSRF requirements and security validations reinforces security best practices and prevents accidental security gaps.

5. **Testing**: Well-documented routes provide clear specifications for writing integration tests and verifying expected behavior.

## 2. Documentation Template

Based on existing codebase conventions, use the following Google-style docstring template:

```python
@blueprint.route("/path", methods=["METHOD"])
def route_name(param: type):
    """One-line summary of route purpose.

    Extended description explaining what this route does, the expected
    parameters, and the behavior. Include information about HTMX responses,
    CSRF requirements, and any special handling.

    Args:
        param: Description of path/query/form parameter

    Returns:
        Description of response type and content:
        - HTML: Full page or HTMX fragment (specify which)
        - JSON: Response structure
        - Response: Flask Response object with status code
        - tuple: (response, status_code) for error conditions

    Raises:
        HTTPException: When and why (e.g., 404 if resource not found)
        abort: Specific error conditions

    HTMX Behavior:
        - If HX-Request header present: Returns partial HTML fragment
        - If no HX-Request header: Returns full page or redirect

    CSRF:
        - Requires CSRF token validation for POST/PUT/DELETE methods
    """
```

### Special Cases

**For HTMX Fragment Routes:**
```python
def fragment_route():
    """Return HTMX partial for polling/update.

    Returns:
        HTML: HTMX partial template (e.g., partials/fragment.html)

    Note:
        This route is designed for HTMX polling and returns
        minimal HTML for efficient updates.
    """
```

**For API JSON Endpoints:**
```python
def json_endpoint():
    """Return JSON data for frontend consumption.

    Returns:
        JSON: Response with structure:
            {
                "field1": type_description,
                "field2": type_description
            }

    Error Response:
        JSON with error details when operation fails
    """
```

## 3. Route Inventory

### 3.1 `src/collector/routes/jobs.py`
**Purpose**: Job lifecycle management (create, view, cancel, retry, delete)

| Route Function | HTTP Method | Route Path | Has Docstring | Description |
|----------------|-------------|------------|---------------|-------------|
| `job_detail` | GET | `/job/<job_id>` | Yes (basic) | Job detail page or HTMX partial |
| `job_status` | GET | `/job/<job_id>/status` | Yes (basic) | Job status as HTMX fragment for polling |
| `active_jobs` | GET | `/jobs/active` | Yes (basic) | Active jobs as HTMX fragment |
| `download` | POST | `/download` | Yes (basic) | Accept URL input, create background job |
| `cancel_job` | POST | `/job/<job_id>/cancel` | Yes (basic) | Cancel a running job |
| `retry_job` | POST | `/job/<job_id>/retry` | Yes (basic) | Retry a failed job |
| `delete_job_route` | DELETE | `/job/<job_id>` | Yes (basic) | Delete a job and its files |

**Status**: All routes have one-line docstrings, but lack comprehensive documentation.

**Documentation Needs**:
- Add parameter descriptions
- Document return types (HTML vs HTMX fragments)
- Specify CSRF requirements for POST/DELETE methods
- Document HTMX conditional behavior
- Add error conditions (404, 403, validation errors)

---

### 3.2 `src/collector/routes/pages.py`
**Purpose**: Main application pages (dashboard, browse, preview, history)

| Route Function | HTTP Method | Route Path | Has Docstring | Description |
|----------------|-------------|------------|---------------|-------------|
| `index` | GET | `/` | Yes (basic) | Dashboard with URL input and active jobs |
| `browse` | GET | `/browse`, `/browse/<path:subpath>` | Yes (basic) | Browse downloaded content by platform/profile/content |
| `preview_file` | GET | `/preview/<path:filepath>` | Yes (detailed) | Preview a file with inline display |
| `history` | GET | `/history` | Yes (basic) | Download history with filters |

**Status**: Most routes have basic one-liners. `preview_file` has the most complete documentation with Args section.

**Documentation Needs**:
- `index`: Add return type specification
- `browse`: Document path resolution, security checks, directory listing behavior
- `preview_file`: Add Returns, Raises sections; document file type detection
- `history`: Document query parameters and filtering

---

### 3.3 `src/collector/routes/sessions.py`
**Purpose**: Instagram session management (list, upload, delete)

| Route Function | HTTP Method | Route Path | Has Docstring | Description |
|----------------|-------------|------------|---------------|-------------|
| `list_sessions` | GET | `/sessions` | Yes (basic) | List all saved Instagram sessions |
| `upload_session` | POST | `/sessions/upload` | Yes (basic) | Upload a cookies.txt file to create a session |
| `delete_session` | POST | `/sessions/<username>/delete` | Yes (basic) | Delete a saved session |

**Status**: All routes have one-line docstrings.

**Documentation Needs**:
- Add Args section for route parameters
- Document file upload requirements for `upload_session`
- Specify CSRF requirements
- Document HTMX conditional responses
- Add error conditions and status codes
- Document session service integration

---

### 3.4 `src/collector/routes/api.py`
**Purpose**: Configuration and status endpoints (JSON API)

| Route Function | HTTP Method | Route Path | Has Docstring | Description |
|----------------|-------------|------------|---------------|-------------|
| `config_status` | GET | `/api/config/status` | Yes (basic) | Get configuration status for UI |

**Status**: Has one-line docstring.

**Documentation Needs**:
- Document JSON response structure
- Add fallback behavior description
- Document SessionService integration
- Add error handling notes
- Specify configuration fields returned

---

## 4. Implementation Steps

### Phase 1: Setup and Analysis (5 minutes)
1. **Review existing documentation patterns** across all route files
2. **Identify common patterns** in HTMX usage, CSRF validation, error handling
3. **Create checklist** of required documentation elements for each route type

### Phase 2: Document jobs.py (20 minutes)
1. **Read file**: `/src/collector/routes/jobs.py`
2. **Enhance each route docstring**:
   - `job_detail`: Add Returns section, HTMX behavior, 404 error
   - `job_status`: Add Returns section, polling usage context
   - `active_jobs`: Add Returns section, fragment description
   - `download`: Add Args, Returns, CSRF section, validation errors
   - `cancel_job`: Add Args, Returns, CSRF, conditional behavior
   - `retry_job`: Add Args, Returns, CSRF, retry logic
   - `delete_job_route`: Add Args, Returns, CSRF, deletion behavior
3. **Verify consistency** with existing docstring style
4. **Test** that no code logic changes (documentation-only update)

### Phase 3: Document pages.py (25 minutes)
1. **Read file**: `/src/collector/routes/pages.py`
2. **Enhance each route docstring**:
   - `index`: Add Returns section, template specification
   - `browse`: Add Args, Returns, PathSecurity handling, directory vs file logic
   - `preview_file`: Add Returns, Raises (403, 404), file type detection logic
   - `history`: Add Args (query params), Returns, filtering behavior
3. **Pay special attention** to security-related routes (browse, preview_file)
4. **Document path resolution** and security validations

### Phase 4: Document sessions.py (20 minutes)
1. **Read file**: `/src/collector/routes/sessions.py`
2. **Enhance each route docstring**:
   - `list_sessions`: Add Returns, error handling
   - `upload_session`: Add Args (file upload), Returns, CSRF, validation errors, file format requirements
   - `delete_session`: Add Args, Returns, CSRF, HTTP status codes
3. **Document SessionService integration** and response structures
4. **Include file upload specifics** (cookies.txt format, validation)

### Phase 5: Document api.py (10 minutes)
1. **Read file**: `/src/collector/routes/api.py`
2. **Enhance docstring**:
   - `config_status`: Add Returns (JSON structure), error fallback, configuration fields
3. **Document API contract** for frontend consumption

### Phase 6: Review and Consistency Check (10 minutes)
1. **Cross-check all docstrings** for consistency in:
   - Section ordering (summary, Args, Returns, Raises, HTMX Behavior, CSRF)
   - Terminology (HTMX fragment vs partial, template names)
   - Error condition documentation
   - Code examples within docstrings (if any)
2. **Verify no code logic was modified**
3. **Check formatting** (indentation, line length)

### Phase 7: Verification (10 minutes)
1. **Create coverage check script** (see Section 7)
2. **Run verification** to confirm 100% documentation coverage
3. **Generate summary** of added documentation

## 5. Documentation Standards

### 5.1 Style Guide

**Use Google-style docstrings** (matching existing codebase conventions):
- Section headers: `Args:`, `Returns:`, `Raises:`, `Note:`, `HTMX Behavior:`, `CSRF:`
- Parameter descriptions: `param_name: Description`
- Return type on its own line, description below

### 5.2 Content Requirements

**Every route docstring MUST include**:

1. **Summary**: One-line description starting with a verb
   - "Get", "Return", "Create", "Delete", "Update", "List", "Handle"

2. **Detailed Behavior** (paragraph):
   - What the route does
   - Any significant business logic
   - Special handling or conditions

3. **Args Section** (if route accepts parameters):
   ```python
   Args:
       job_id: Unique job identifier from URL path
       url: Target URL for download (form parameter)
   ```

4. **Returns Section** (REQUIRED):
   ```python
   Returns:
       HTML: Rendered template (template_name.html) with context
       OR
       JSON: Response structure with fields:
           - field1: description
           - field2: description
       OR
       tuple: (response, status_code) for error conditions
   ```

5. **Raises Section** (for explicit errors):
   ```python
   Raises:
       HTTPException: 404 if resource not found
       abort: 403 if CSRF validation fails
   ```

6. **HTMX Behavior Section** (if route uses HTMX):
   ```python
   HTMX Behavior:
       If HX-Request header present: Returns partial HTML fragment
       If no HX-Request header: Returns full page or redirect
   ```

7. **CSRF Section** (for POST/PUT/DELETE methods):
   ```python
   CSRF:
       Requires CSRF token validation via validate_csrf_request()
   ```

### 5.3 Special Notes

**File Upload Routes**:
- Document expected file format (.txt for cookies.txt)
- Mention form field name (e.g., "cookies_file")
- Specify validation performed

**Security-Sensitive Routes** (path traversal protection):
- Document path resolution security
- Mention PathSecurityError handling
- Specify abort conditions (403, 404)

**Polling Routes**:
- Document polling purpose
- Mention update frequency expectations (if applicable)
- Specify fragment optimization

## 6. Code Examples

### Example 1: GET Route with HTMX Conditional (Before/After)

**Before** (`jobs.py:job_status`):
```python
@jobs_bp.route("/job/<job_id>/status")
def job_status(job_id: str):
    """Job status as HTMX fragment for polling."""
    job_service = JobService()
    job = job_service.get_job(job_id)
    if not job:
        abort(404)

    files = job_service.get_job_files(job_id)

    return render_template("partials/job_card.html", job=job, files=files)
```

**After**:
```python
@jobs_bp.route("/job/<job_id>/status")
def job_status(job_id: str):
    """Get job status as HTMX fragment for polling.

    This route is designed for HTMX polling to update job status
    on the dashboard without full page refresh.

    Args:
        job_id: Unique job identifier from URL path

    Returns:
        HTML: Partial template (partials/job_card.html) with:
            - job: Job object with current status
            - files: List of associated files

    Raises:
        abort: 404 if job not found

    HTMX Behavior:
        Returns minimal HTML fragment for efficient polling updates.
        Designed for use with hx-trigger="every 2s" or similar.

    Note:
        This route is optimized for frequent polling and returns
        only the job card fragment, not a full page.
    """
    job_service = JobService()
    job = job_service.get_job(job_id)
    if not job:
        abort(404)

    files = job_service.get_job_files(job_id)

    return render_template("partials/job_card.html", job=job, files=files)
```

---

### Example 2: POST Route with CSRF and HTMX (Before/After)

**Before** (`jobs.py:download`):
```python
@jobs_bp.route("/download", methods=["POST"])
def download():
    """Accept URL input, create background job."""
    if not validate_csrf_request(request):
        if "HX-Request" in request.headers:
            return '<div class="notification error">CSRF validation failed</div>', 403
        abort(403, "CSRF token validation failed")

    url = request.form.get("url", "").strip()

    scraper_service = ScraperService()
    is_valid, error = scraper_service.validate_url(url)

    if not is_valid:
        if "HX-Request" in request.headers:
            return f'<div class="notification error">{error}</div>', 400
        flash(error or "Unknown validation error", "error")
        return redirect(url_for("pages.index"))

    # ... rest of implementation
```

**After**:
```python
@jobs_bp.route("/download", methods=["POST"])
def download():
    """Create and submit a download job for the given URL.

    Validates the URL, detects the platform, creates a job record,
    and submits it for background processing via the executor.

    Form Parameters:
        url: Target URL to download (required)

    Returns:
        HTML/Response:
            - If HTMX request: Partial HTML (partials/job_card.html)
            - If regular request: Redirect to dashboard
            - On validation error: Error notification with status code

    Raises:
        HTTPException: 403 if CSRF token validation fails

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present:
            - Success: Returns job_card.html partial
            - Validation error: Returns error notification div with 400
            - CSRF error: Returns error notification div with 403
        If no HX-Request header:
            - Success: Flash message and redirect to dashboard
            - Errors: Flash message and redirect to dashboard

    Validation Errors:
        - Empty URL: Returns 400 with error message
        - Invalid URL format: Returns 400 with validation error
        - Unrecognized platform: Returns 400 with platform error
    """
    if not validate_csrf_request(request):
        if "HX-Request" in request.headers:
            return '<div class="notification error">CSRF validation failed</div>', 403
        abort(403, "CSRF token validation failed")

    url = request.form.get("url", "").strip()

    scraper_service = ScraperService()
    is_valid, error = scraper_service.validate_url(url)

    if not is_valid:
        if "HX-Request" in request.headers:
            return f'<div class="notification error">{error}</div>', 400
        flash(error or "Unknown validation error", "error")
        return redirect(url_for("pages.index"))

    # ... rest of implementation
```

---

### Example 3: Security-Sensitive Route with Path Resolution (Before/After)

**Before** (`pages.py:preview_file`):
```python
@pages_bp.route("/preview/<path:filepath>")
def preview_file(filepath: str):
    """Preview a file with inline display.

    Args:
        filepath: Relative path from downloads root
    """
    from flask import current_app

    download_dir = Path(current_app.config["SCRAPER_DOWNLOAD_DIR"])

    try:
        file_path = resolve_user_path(download_dir, filepath)
    except PathSecurityError:
        abort(403)

    if not file_path.exists():
        abort(404)

    if file_path.is_dir():
        return redirect(url_for("pages.browse", subpath=filepath))

    # ... file type detection and rendering
```

**After**:
```python
@pages_bp.route("/preview/<path:filepath>")
def preview_file(filepath: str):
    """Preview a downloaded file with inline display based on type.

    Resolves the file path securely, detects the file type, and renders
    an appropriate preview (image, video, audio, text, metadata).

    Args:
        filepath: Relative path from downloads root (e.g., "instagram/user/photo.jpg")

    Returns:
        HTML: Rendered preview page (preview.html) with:
            - file_path: Relative path to file
            - file_name: Base filename
            - file_type: Detected type (image, video, audio, transcript, text, metadata, unknown)
            - content: File content for text-based types (None for binary)
        OR redirect to browse page if path is a directory

    Raises:
        HTTPException: 403 if path traversal detected (PathSecurityError)
        HTTPException: 404 if file does not exist

    Security:
        Uses resolve_user_path() to prevent directory traversal attacks.
        All paths are validated against the configured downloads directory.

    File Type Detection:
        - Image: .jpg, .jpeg, .png, .gif, .webp
        - Video: .mp4, .mov, .webm, .mkv
        - Audio: .mp3, .m4a, .wav
        - Transcript: .txt files with "transcript" in filename
        - Text: Other .txt files
        - Metadata: .json files
        - Unknown: All other file types
    """
    from flask import current_app

    download_dir = Path(current_app.config["SCRAPER_DOWNLOAD_DIR"])

    try:
        file_path = resolve_user_path(download_dir, filepath)
    except PathSecurityError:
        abort(403)

    if not file_path.exists():
        abort(404)

    if file_path.is_dir():
        return redirect(url_for("pages.browse", subpath=filepath))

    # ... file type detection and rendering
```

---

### Example 4: JSON API Endpoint (Before/After)

**Before** (`api.py:config_status`):
```python
@api_bp.route("/api/config/status")
def config_status():
    """Get configuration status for UI."""
    try:
        session_service = SessionService()
        result = session_service.get_config_status()

        if result["success"]:
            return jsonify({
                "encryption_enabled": result["encryption_enabled"],
                "downloads_dir": result["downloads_dir"],
            })
        else:
            # Fallback to basic config if service fails
            return jsonify({
                "encryption_enabled": False,
                "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
            })
    except Exception as e:
        logger.exception("Error getting config status: %s", e)
        # Fallback to basic config
        return jsonify({
            "encryption_enabled": False,
            "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
        })
```

**After**:
```python
@api_bp.route("/api/config/status")
def config_status():
    """Get application configuration status for the frontend UI.

    Retrieves encryption status and downloads directory location.
    Includes fallback behavior to ensure UI always receives valid config.

    Returns:
        JSON: Response with structure:
            {
                "encryption_enabled": bool - Whether encryption is configured,
                "downloads_dir": string - Absolute path to downloads directory
            }

    Error Handling:
        If SessionService fails or throws exception, returns fallback config:
            - encryption_enabled: false
            - downloads_dir: Value from app config or empty string

    Note:
        This endpoint is called by the frontend to display configuration
        status in the UI. The fallback ensures graceful degradation.
    """
    try:
        session_service = SessionService()
        result = session_service.get_config_status()

        if result["success"]:
            return jsonify({
                "encryption_enabled": result["encryption_enabled"],
                "downloads_dir": result["downloads_dir"],
            })
        else:
            # Fallback to basic config if service fails
            return jsonify({
                "encryption_enabled": False,
                "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
            })
    except Exception as e:
        logger.exception("Error getting config status: %s", e)
        # Fallback to basic config
        return jsonify({
            "encryption_enabled": False,
            "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
        })
```

---

## 7. Verification

### 7.1 Manual Verification Checklist

After completing documentation, verify each route:

- [ ] Every route function has a docstring
- [ ] All docstrings start with a one-line summary
- [ ] GET routes document the Returns section
- [ ] POST/PUT/DELETE routes document CSRF requirements
- [ ] HTMX routes document conditional behavior
- [ ] Routes with parameters document Args section
- [ ] Routes that raise errors document Raises section
- [ ] Security-sensitive routes document security measures
- [ ] API routes document JSON response structure
- [ ] Docstrings follow Google-style formatting

### 7.2 Automated Coverage Check

Create a test script to verify docstring coverage:

```python
# test_route_documentation.py
"""Verify all route handlers have docstrings."""

import ast
import inspect
from pathlib import Path
from flask import Blueprint

def get_all_routes():
    """Extract all route functions from blueprints."""
    routes = []

    # Import all blueprints
    from collector.routes import jobs, pages, sessions, api

    blueprints = [
        ("jobs", jobs.jobs_bp),
        ("pages", pages.pages_bp),
        ("sessions", sessions.sessions_bp),
        ("api", api.api_bp),
    ]

    for module_name, bp in blueprints:
        # Get the module source
        module = inspect.getmodule(bp)
        source = inspect.getsource(module)

        # Parse AST
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function is a route
                has_route_decorator = any(
                    (isinstance(dec, ast.Call) and
                     hasattr(dec.func, 'attr') and
                     dec.func.attr == 'route') or
                    (isinstance(dec, ast.Call) and
                     hasattr(dec.func, 'attr') and
                     dec.func.attr == 'route')
                    for dec in node.decorator_list
                )

                if has_route_decorator:
                    has_docstring = ast.get_docstring(node) is not None
                    routes.append({
                        'module': module_name,
                        'function': node.name,
                        'has_docstring': has_docstring,
                        'docstring': ast.get_docstring(node)
                    })

    return routes

def test_route_documentation_coverage():
    """Test that all route handlers have docstrings."""
    routes = get_all_routes()

    undocumented = [r for r in routes if not r['has_docstring']]
    documented = [r for r in routes if r['has_docstring']]

    print(f"\nRoute Documentation Coverage:")
    print(f"  Total routes: {len(routes)}")
    print(f"  Documented: {len(documented)}")
    print(f"  Undocumented: {len(undocumented)}")
    print(f"  Coverage: {len(documented) / len(routes) * 100:.1f}%")

    if undocumented:
        print(f"\nUndocumented routes:")
        for route in undocumented:
            print(f"  - {route['module']}.{route['function']}")
        raise AssertionError(
            f"{len(undocumented)} route(s) missing documentation"
        )

    print("\nAll routes have documentation!")

if __name__ == '__main__':
    test_route_documentation_coverage()
```

Run the verification:
```bash
pytest tests/test_route_documentation.py -v
# Or directly
python test_route_documentation.py
```

### 7.3 Quality Check Script

Verify docstring quality:

```python
# test_docstring_quality.py
"""Verify docstring quality and completeness."""

import re

def check_docstring_quality(func_name, docstring):
    """Check if docstring meets quality standards."""
    issues = []

    if not docstring:
        return ['Missing docstring']

    # Check for one-line summary
    lines = docstring.strip().split('\n')
    if not lines[0].strip():
        issues.append('Missing one-line summary')

    # Check for Returns section
    if 'Returns:' not in docstring:
        issues.append('Missing Returns section')

    # Check for Args if function has parameters
    # (This would require parsing function signature)

    # Check for CSRF in POST/DELETE routes
    if any(x in func_name for x in ['upload', 'delete', 'cancel', 'retry']):
        if 'CSRF' not in docstring:
            issues.append('Missing CSRF documentation')

    # Check for HTMX behavior if likely HTMX route
    if 'HTMX' not in docstring and any(x in func_name for x in ['status', 'active', 'detail']):
        issues.append('Consider adding HTMX Behavior section')

    return issues
```

### 7.4 Pre-Commit Hook (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Check route documentation before commit

echo "Checking route documentation coverage..."
python test_route_documentation.py

if [ $? -ne 0 ]; then
    echo "Route documentation check failed. Please document all routes."
    exit 1
fi

echo "Route documentation check passed!"
```

## 8. Success Criteria

Implementation is complete when:

1. **Coverage**: 100% of route handlers have docstrings (15/15 routes)
2. **Quality**: All docstrings include:
   - One-line summary
   - Returns section (for all routes)
   - Args section (for routes with parameters)
   - CSRF section (for POST/PUT/DELETE routes)
   - HTMX Behavior section (for HTMX-aware routes)
3. **Consistency**: All docstrings follow the Google-style template
4. **Verification**: Automated test passes without errors
5. **No Side Effects**: No code logic changes, only documentation additions

## 9. Estimated Time

**Total Estimated Time**: 90 minutes (1.5 hours)

- Setup and Analysis: 5 minutes
- Document jobs.py: 20 minutes
- Document pages.py: 25 minutes
- Document sessions.py: 20 minutes
- Document api.py: 10 minutes
- Review and Consistency: 10 minutes

## 10. Next Steps

After completing route documentation:

1. **Consider API documentation generation**: Use tools like Sphinx or Flask-Doc to auto-generate API docs
2. **Add OpenAPI/Swagger spec**: Document REST API endpoints for external consumers
3. **Extend to other modules**: Apply documentation standards to services, repositories, and scrapers
4. **Create developer guide**: Document how to add new routes with proper documentation
5. **Integrate with CI**: Add docstring coverage check to CI/CD pipeline

---

**Document Version**: 1.0
**Created**: 2025-02-17
**Status**: Ready for Implementation
