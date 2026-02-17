"""Jobs blueprint for job lifecycle management."""

from __future__ import annotations

import logging

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from security.csrf import validate_csrf_request
from services import JobService, ScraperService

logger = logging.getLogger(__name__)

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/job/<job_id>")
def job_detail(job_id: str):
    """Job detail page or HTMX partial."""
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
    """Job status as HTMX fragment for polling."""
    job_service = JobService()
    job = job_service.get_job(job_id)
    if not job:
        abort(404)

    files = job_service.get_job_files(job_id)

    return render_template("partials/job_card.html", job=job, files=files)


@jobs_bp.route("/jobs/active")
def active_jobs():
    """Active jobs as HTMX fragment."""
    job_service = JobService()
    jobs = job_service.get_active_jobs()

    return render_template("partials/active_jobs.html", jobs=jobs)


@jobs_bp.route("/download", methods=["POST"])
def download():
    """Accept URL input, create background job."""
    if not validate_csrf_request(request):
        if "HX-Request" in request.headers:
            return '<div class="notification error">CSRF validation failed</div>', 403
        abort(403, "CSRF token validation failed")

    url = request.form.get("url", "").strip()

    # Validate URL using ScraperService
    scraper_service = ScraperService()
    is_valid, error = scraper_service.validate_url(url)

    if not is_valid:
        if "HX-Request" in request.headers:
            return f'<div class="notification error">{error}</div>', 400
        flash(error or "Unknown validation error", "error")
        return redirect(url_for("pages.index"))

    # Detect platform
    platform = scraper_service.detect_platform(url)
    if not platform:
        if "HX-Request" in request.headers:
            return '<div class="notification error">Could not detect platform</div>', 400
        flash("Could not detect platform", "error")
        return redirect(url_for("pages.index"))

    # Create job using JobService
    job_service = JobService()
    job = job_service.create_job(url, platform)

    # Submit background job using ScraperService
    scraper_service.execute_download(job.id)

    if "HX-Request" in request.headers:
        # Return the new job card
        return render_template("partials/job_card.html", job=job, files=[])

    flash(f"Download started for {url}", "success")
    return redirect(url_for("pages.index"))


@jobs_bp.route("/job/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    """Cancel a running job."""
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
    """Retry a failed job."""
    if not validate_csrf_request(request):
        abort(403, "CSRF token validation failed")

    job_service = JobService()
    new_job = job_service.prepare_retry_job(job_id)

    if not new_job:
        flash("Only failed jobs can be retried", "error")
        return redirect(url_for("pages.index"))

    # Submit background job using ScraperService
    scraper_service = ScraperService()
    scraper_service.execute_download(new_job.id)

    if "HX-Request" in request.headers:
        return render_template("partials/job_card.html", job=new_job, files=[])

    flash("Job retry started", "success")
    return redirect(url_for("pages.index"))


@jobs_bp.route("/job/<job_id>", methods=["DELETE"])
def delete_job_route(job_id: str):
    """Delete a job and its files."""
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
