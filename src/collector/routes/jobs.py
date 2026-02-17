"""Jobs blueprint for job lifecycle management."""

from __future__ import annotations

import logging

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..security.csrf import validate_csrf_request
from ..services import ExecutorAdapter, JobService, ScraperService

logger = logging.getLogger(__name__)

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/job/<job_id>")
def job_detail(job_id: str):
    """Get job detail page or HTMX partial.

    Retrieves job information and associated files, returning either
    a full page or HTMX fragment depending on the request type.

    Args:
        job_id: Unique job identifier from URL path

    Returns:
        HTML:
            - If HX-Request header present: Partial template (partials/job_card.html)
            - If no HX-Request header: Full page (job_detail.html)
            Both templates include:
                - job: Job object with current status
                - files: List of associated files

    Raises:
        HTTPException: 404 if job not found

    HTMX Behavior:
        If HX-Request header present: Returns partial HTML fragment (job_card.html)
        If no HX-Request header: Returns full page (job_detail.html)
    """
    job_service = JobService()
    job = job_service.get_job(job_id)
    if not job:
        abort(404)

    files = job_service.get_job_files(job_id)
    is_htmx = "HX-Request" in request.headers

    if is_htmx:
        return render_template("partials/job_card.html", job=job, files=files)

    return render_template("job_detail.html", job=job, files=files)


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
        HTTPException: 404 if job not found

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


@jobs_bp.route("/jobs/active")
def active_jobs():
    """Get active jobs as HTMX fragment.

    Retrieves all currently active jobs for display in the dashboard.

    Returns:
        HTML: Partial template (partials/active_jobs.html) with:
            - jobs: List of active Job objects

    HTMX Behavior:
        Returns HTML fragment for updating the active jobs section.
        Typically used for polling or conditional updates.
    """
    job_service = JobService()
    jobs = job_service.get_active_jobs()

    return render_template("partials/active_jobs.html", jobs=jobs)


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

    platform = scraper_service.detect_platform(url)
    if not platform:
        if "HX-Request" in request.headers:
            return '<div class="notification error">Could not detect platform</div>', 400
        flash("Could not detect platform", "error")
        return redirect(url_for("pages.index"))

    job_service = JobService()
    job = job_service.create_job(url, platform)

    ExecutorAdapter().submit_job(scraper_service.execute_download, job.id)

    if "HX-Request" in request.headers:
        return render_template("partials/job_card.html", job=job, files=[])

    flash(f"Download started for {url}", "success")
    return redirect(url_for("pages.index"))


@jobs_bp.route("/job/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    """Cancel a running or pending job.

    Attempts to cancel the job if it's in a cancellable state
    (pending, running, or retrying).

    Args:
        job_id: Unique job identifier from URL path

    Returns:
        Response:
            - If HTMX request and successful: Empty response with 204
            - If HTMX request and job not found: 404 error
            - If regular request: Flash message and redirect to dashboard
            - If job cannot be cancelled: Flash error message

    Raises:
        HTTPException: 403 if CSRF token validation fails
        HTTPException: 404 if job not found

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present and successful: Returns 204 No Content
        If no HX-Request header: Flash message and redirect to dashboard
    """
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    job_service = JobService()
    job = job_service.get_job(job_id)
    if not job:
        abort(404)

    if job_service.cancel_job(job_id):
        if "HX-Request" in request.headers:
            return "", 204
        flash("Job cancelled", "success")
    else:
        flash("Job cannot be cancelled", "error")

    return redirect(url_for("pages.index"))


@jobs_bp.route("/job/<job_id>/retry", methods=["POST"])
def retry_job(job_id: str):
    """Retry a failed job by creating a new job with the same parameters.

    Creates a new job based on the original job's URL and platform,
    then submits it for background processing. Only failed jobs can be retried.

    Args:
        job_id: Unique job identifier of the failed job to retry

    Returns:
        HTML/Response:
            - If HTMX request and successful: Partial HTML (partials/job_card.html)
            - If regular request and successful: Flash message and redirect to dashboard
            - If job is not failed: Flash error message and redirect to dashboard

    Raises:
        HTTPException: 403 if CSRF token validation fails

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present and successful: Returns job_card.html partial
        If no HX-Request header: Flash message and redirect to dashboard

    Note:
        Only jobs with status "failed" can be retried.
        A new job is created with a new ID.
    """
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    job_service = JobService()
    new_job = job_service.prepare_retry_job(job_id)

    if not new_job:
        flash("Only failed jobs can be retried", "error")
        return redirect(url_for("pages.index"))

    scraper_service = ScraperService()
    ExecutorAdapter().submit_job(scraper_service.execute_download, new_job.id)

    if "HX-Request" in request.headers:
        return render_template("partials/job_card.html", job=new_job, files=[])

    flash("Job retry started", "success")
    return redirect(url_for("pages.index"))


@jobs_bp.route("/job/<job_id>", methods=["DELETE"])
def delete_job_route(job_id: str):
    """Delete a job record and its associated files.

    Permanently removes the job from the database and deletes all
    associated downloaded files from disk.

    Args:
        job_id: Unique job identifier from URL path

    Returns:
        Response:
            - If HTMX request and successful: Empty response with 204
            - If HTMX request and not found: Error message with 404
            - If regular request: Flash message and redirect to history page
            - If job not found: Flash error message or 404 for HTMX

    Raises:
        HTTPException: 403 if CSRF token validation fails

    CSRF:
        Requires CSRF token validation via validate_csrf_request()

    HTMX Behavior:
        If HX-Request header present and successful: Returns 204 No Content
        If HX-Request header and job not found: Returns error message with 404
        If no HX-Request header: Flash message and redirect to history page

    Warning:
        This operation is irreversible. All files associated with the job
        will be permanently deleted from disk.
    """
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    job_service = JobService()
    if job_service.delete_job(job_id, delete_files=True):
        if "HX-Request" in request.headers:
            return "", 204
        flash("Job deleted", "success")
    else:
        if "HX-Request" in request.headers:
            return "Job not found", 404
        flash("Job not found", "error")

    return redirect(url_for("pages.history"))
