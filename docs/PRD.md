# Product Requirements Document: Python Content Scraper

**Instagram + YouTube Downloader · Flask + HTMX Web Interface**

Version 2.0 — February 2026

---

## Table of Contents

1. Executive Summary
2. Problem Statement
3. Scope Definition
4. Target Users
5. Technical Requirements
6. Architecture & Design
7. User Interface Requirements
8. Data Model
9. API Design
10. Security Considerations
11. Risk Assessment
12. Implementation Plan
13. Success Metrics
14. Dependencies & Deployment
15. Appendix

---

## 1. Executive Summary

This document specifies a Python-based content scraper for downloading and
archiving media from Instagram and YouTube. The application provides a web
interface built with Flask, HTMX, and Pico CSS, allowing users to input URLs and
retrieve media alongside metadata and transcripts. The scraping layer uses
Instaloader for Instagram and yt-dlp combined with youtube-transcript-api for
YouTube.

The architecture prioritizes simplicity over scalability. This is a single-user,
self-hosted utility — not a production service. It requires zero external
services (no Redis, no message brokers, no Docker), no API keys for basic
operation, and runs entirely on a single machine with SQLite for state and the
filesystem for media storage. Flask-Executor handles background task processing
to keep the interface responsive during downloads.

All core scraping libraries are actively maintained as of early 2026 and provide
comprehensive Python APIs. The system is designed for minimal operational
overhead while navigating the increasingly complex anti-scraping measures
implemented by major platforms.

---

## 2. Problem Statement

### 2.1 Tool Fragmentation

Archiving content from multiple platforms requires separate command-line tools
with different interfaces, dependencies, and failure modes. Instagram typically
requires Instaloader or gallery-dl; YouTube demands yt-dlp. Users who simply
want to save content from both platforms must learn and manage multiple tools.

### 2.2 Technical Barriers

Existing graphical solutions often require complex setup, API keys, or
subscription fees. Many impose rate limits or require authentication through
proprietary systems. The once-reliable pytube library has been effectively
abandoned since mid-2024, and instagram-scraper (7,100 stars) has been
non-functional since 2021. Even actively maintained tools require careful
configuration — as of November 2025, yt-dlp requires a Deno JavaScript runtime
for YouTube support.

### 2.3 Metadata Loss

Most downloaders focus solely on media files, discarding captions, descriptions,
timestamps, engagement metrics, and transcripts. Preserving this context
requires manual effort or custom scripting that most users cannot perform.

### 2.4 No Unified Management

Users lack a centralized interface for initiating downloads across platforms,
monitoring progress, browsing archived content, and managing download history.
Command-line tools offer no built-in mechanism for tracking queued operations or
reviewing past downloads.

### 2.5 Anti-Scraping Escalation

Instagram has implemented increasingly sophisticated detection — TLS
fingerprinting, behavioral analysis, rotating GraphQL doc_id values, and IP
reputation scoring. Instaloader users report persistent 401 Unauthorized errors
throughout 2024–2025. Users without technical expertise cannot navigate these
challenges effectively.

---

## 3. Scope Definition

### 3.1 In Scope

- Instagram profile scraping: photos, videos, reels, stories (authenticated),
  and highlights (authenticated) from public profiles
- YouTube video downloads in selectable quality formats with metadata
  preservation
- YouTube transcript extraction (manual and auto-generated subtitles)
- Metadata preservation: captions, descriptions, timestamps, engagement metrics
  in JSON format
- Web interface: Flask dashboard with HTMX for dynamic updates, Pico CSS for
  styling
- Background processing: concurrent downloads with real-time progress tracking
- Content browsing: file browser organized by platform, profile, and content
- Download history with filtering, retry, and deletion

### 3.2 Out of Scope

- Multi-user authentication and authorization
- Cloud deployment or distributed processing
- Scheduled/recurring downloads or real-time monitoring
- Platforms beyond Instagram and YouTube
- Commercial redistribution or API-as-a-service
- Mobile-native interfaces

---

## 4. Target Users

### 4.1 Primary Persona: Individual Content Archiver

A person who wants to save social media content for personal use, offline
viewing, or research. Technical expertise ranges from command-line proficient to
GUI-only users. The system must serve both through its web interface while
exposing advanced options for power users.

### 4.2 Secondary Personas

**Content Creators** need to back up their own posts across platforms. They
value metadata preservation and organized storage. They require authenticated
Instagram sessions to access their own content and may download entire profile
archives.

**Researchers and Analysts** collect content systematically for study. They need
structured metadata output (JSON) importable into analysis pipelines and the
ability to process content from specific creators in bulk.

**Digital Archivists** maintain comprehensive collections. They require complete
metadata preservation including platform-specific attributes, organized folder
structures that maintain provenance, and may customize the application for
specialized workflows.

---

## 5. Technical Requirements

### 5.1 Core Technology Stack

| Component              | Technology                     | Rationale                                                                 |
| ---------------------- | ------------------------------ | ------------------------------------------------------------------------- |
| Instagram Scraper      | Instaloader v4.15+             | 11,500+ stars, active maintenance, clean Python API                       |
| Instagram Fallback     | gallery-dl                     | Alternative when Instaloader encounters persistent 401s                   |
| YouTube Downloader     | yt-dlp                         | 146,000+ stars, 1000+ sites, daily builds, mature embedding API           |
| Transcript API         | youtube-transcript-api v1.2.4+ | 6,400+ stars, instance-based API, no video download required              |
| Web Framework          | Flask 3.x                      | Template-first, Jinja2 native, massive ecosystem                          |
| Background Tasks       | Flask-Executor                 | Zero external dependencies, ThreadPoolExecutor wrapper with Flask context |
| Frontend Interactivity | HTMX                           | Dynamic behavior via HTML attributes, no JS framework complexity          |
| CSS Framework          | Pico CSS                       | ~8KB, semantic HTML styling, zero custom classes, built-in dark mode      |
| Database               | SQLite                         | ACID-compliant, zero operational overhead, single-file                    |

### 5.2 System Dependencies

| Dependency   | Purpose                    | Notes                                                                         |
| ------------ | -------------------------- | ----------------------------------------------------------------------------- |
| Python 3.10+ | Runtime                    | Required for structural pattern matching and improved type hints              |
| Deno         | JS runtime for yt-dlp      | Required since Nov 2025 for YouTube's JS challenges; recommended over Node.js |
| FFmpeg       | Video/audio stream merging | YouTube stores video and audio as separate streams                            |

### 5.3 Functional Requirements — Instagram

| ID     | Requirement                                                                                 |
| ------ | ------------------------------------------------------------------------------------------- |
| FR-1.1 | Accept Instagram profile URLs and extract all public posts (photos, videos, reels)          |
| FR-1.2 | Download stories and highlights when an authenticated session is provided                   |
| FR-1.3 | Preserve metadata (captions, hashtags, timestamps, location, engagement metrics) in JSON    |
| FR-1.4 | Implement configurable rate limiting with randomized delays (default: 5–10 seconds)         |
| FR-1.5 | Support authenticated sessions via browser cookie import (preferred) or username/password   |
| FR-1.6 | Detect and report 401/429 errors with actionable guidance (e.g., "refresh session cookies") |
| FR-1.7 | Fall back to gallery-dl when Instaloader encounters persistent authentication failures      |

### 5.4 Functional Requirements — YouTube

| ID     | Requirement                                                                                                   |
| ------ | ------------------------------------------------------------------------------------------------------------- |
| FR-2.1 | Accept YouTube video URLs and download in user-selected quality (up to 4K)                                    |
| FR-2.2 | Support audio-only downloads                                                                                  |
| FR-2.3 | Support channel and playlist URLs, enumerating all videos as individual jobs                                  |
| FR-2.4 | Retrieve transcripts in multiple languages (manual and auto-generated) via youtube-transcript-api             |
| FR-2.5 | Handle videos without transcripts gracefully (log absence, do not fail the job)                               |
| FR-2.6 | Preserve metadata (title, description, uploader, upload date, view count, like count, duration, tags) in JSON |

### 5.5 Functional Requirements — Web Interface

| ID      | Requirement                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------- |
| FR-3.1  | Dashboard with URL input form, active downloads section, and recent activity                      |
| FR-3.2  | Auto-detect platform from URL and route to the appropriate scraper module                         |
| FR-3.3  | Validate URLs and return descriptive errors for unsupported or malformed inputs                   |
| FR-3.4  | Support batch URL input (multiple URLs submitted in a single request, processed as separate jobs) |
| FR-3.5  | Display real-time download progress via HTMX polling (every 2–3 seconds) without page refreshes   |
| FR-3.6  | File browser for navigating downloaded content by platform → profile → content item               |
| FR-3.7  | Inline media preview (image display, video player) with metadata and transcript display           |
| FR-3.8  | Download history table with filtering by platform, status, and date range                         |
| FR-3.9  | Job actions: cancel (running/queued), retry (failed), delete (any completed/failed)               |
| FR-3.10 | Dark/light mode matching system preference with manual toggle override                            |

### 5.6 Functional Requirements — Background Processing

| ID     | Requirement                                                                               |
| ------ | ----------------------------------------------------------------------------------------- |
| FR-4.1 | Execute all scraping operations as background tasks via Flask-Executor                    |
| FR-4.2 | Track job states: pending → running → completed/failed/cancelled                          |
| FR-4.3 | Report progress: percentage, current operation description, bytes downloaded              |
| FR-4.4 | Support configurable concurrent downloads (default: 2, max recommended: 4)                |
| FR-4.5 | Implement automatic retry with exponential backoff for transient failures (max 3 retries) |
| FR-4.6 | Clean up partial downloads on cancellation or unrecoverable failure                       |
| FR-4.7 | Persist job state to SQLite for recovery after application restart                        |

### 5.7 Functional Requirements — Storage

| ID     | Requirement                                                                                    |
| ------ | ---------------------------------------------------------------------------------------------- |
| FR-5.1 | Organize downloads as: `downloads/{platform}/{profile_or_channel}/{content_title}/`            |
| FR-5.2 | Each content directory contains: media file, metadata.json, transcript.txt (when available)    |
| FR-5.3 | Sanitize filenames: strip special characters, truncate excessive length, handle reserved names |
| FR-5.4 | Track all files in the database with job-to-file relationships                                 |
| FR-5.5 | Support deletion through the interface (removes both database record and physical files)       |
| FR-5.6 | Monitor available disk space and warn when below a configurable threshold (default: 1 GB)      |

### 5.8 Non-Functional Requirements

| ID      | Category        | Requirement                                                                         |
| ------- | --------------- | ----------------------------------------------------------------------------------- |
| NFR-1.1 | Performance     | Page loads complete within 2 seconds under normal conditions                        |
| NFR-1.2 | Performance     | API polling endpoints respond within 500 milliseconds                               |
| NFR-1.3 | Performance     | Database operations complete within 50 milliseconds for typical queries             |
| NFR-2.1 | Reliability     | Individual download failures do not crash the application                           |
| NFR-2.2 | Reliability     | Background tasks are isolated — exceptions are caught, logged, and reported         |
| NFR-2.3 | Reliability     | Atomic file writes where possible; temporary files cleaned up on failure            |
| NFR-2.4 | Reliability     | No memory leaks or resource exhaustion during sustained operation                   |
| NFR-3.1 | Usability       | Core workflows (submit URL, view progress, browse content) require no documentation |
| NFR-3.2 | Usability       | Error messages written in plain language with actionable guidance                   |
| NFR-3.3 | Usability       | Keyboard-navigable interface for accessibility                                      |
| NFR-4.1 | Maintainability | Scraping modules are isolated — each can be updated or replaced independently       |
| NFR-4.2 | Maintainability | Configuration centralized in settings module with environment variable overrides    |
| NFR-4.3 | Maintainability | Logging at configurable levels (DEBUG, INFO, WARNING, ERROR)                        |

---

## 6. Architecture & Design

### 6.1 System Architecture

The application follows a request-response architecture with background task
processing. The design deliberately avoids complexity: no Redis, no message
queues, no container orchestration, no microservices. Flask's synchronous model
is sufficient for single-user load, and Flask-Executor provides concurrency
without Celery's infrastructure dependencies.

**Four primary components:**

**Web Layer** — Flask routes serving full HTML pages and HTMX partials. Handles
input validation, CSRF protection, session management, and error rendering via
Jinja2 templates.

**Job Manager** — Coordinates background task execution through Flask-Executor's
ThreadPoolExecutor. Manages job submission, progress tracking, state
transitions, and SQLite persistence. Exposes polling endpoints for real-time
frontend updates.

**Scraping Layer** — Platform-specific modules (Instagram, YouTube) with a
consistent interface for content enumeration, media downloading, and metadata
extraction. Encapsulates library configuration, error interpretation, and rate
limiting. Each module is independently replaceable.

**Storage Layer** — Manages filesystem organization, filename sanitization, and
database operations. Ensures consistent folder structures and maintains the
mapping between download jobs and physical files.

### 6.2 Data Flow

1. User submits URL through the web form
2. Flask validates URL format, detects platform, creates job record in SQLite
   (status: `pending`)
3. Response returns an HTMX partial inserting the new job into the active jobs
   list with polling configured
4. Flask-Executor spawns a background thread running the appropriate scraper
   module
5. Scraper downloads content to the filesystem, updating the job record with
   progress at each stage
6. HTMX polls the status endpoint every 2–3 seconds, receiving HTML fragments
   that update the progress display
7. On completion: job status → `completed`, interface shows links to content
8. On failure: job status → `failed`, error message stored, interface offers
   retry option

### 6.3 Project Structure

```text
project/
├── app.py                  # Flask entry point, routes, job management
├── config.py               # Centralized configuration with env var support
├── scrapers/
│   ├── __init__.py         # Common scraper interface/base class
│   ├── youtube_scraper.py  # yt-dlp + transcript integration
│   └── instagram_scraper.py # Instaloader + gallery-dl fallback
├── templates/
│   ├── base.html           # Layout with nav, dark mode toggle
│   ├── dashboard.html      # URL input + active jobs
│   ├── browse.html         # File browser
│   ├── history.html        # Download history table
│   └── partials/           # HTMX fragments (job card, progress bar, etc.)
├── static/                 # HTMX and Pico CSS (served locally)
├── downloads/
│   ├── youtube/
│   └── instagram/
├── scraper.db              # SQLite database
├── requirements.txt
└── README.md
```

---

## 7. User Interface Requirements

### 7.1 Layout and Visual Design

Minimalist design using Pico CSS with semantic HTML styling. Single-column
layout with a compact fixed header providing navigation to Dashboard, Browse,
and History. Dark mode matches system preference by default with manual override
toggle. All color choices must maintain WCAG AA contrast ratios.

### 7.2 Dashboard

The primary interaction point. Contains:

- Prominent URL input field with placeholder text showing example URLs for both
  platforms
- Submit button with immediate visual feedback on acceptance
- Active jobs section below, where each job shows: content title (or URL if
  unresolved), platform badge, progress bar with percentage, current operation
  text
- Queued jobs show queue position
- Completed jobs show links to browse content or download files directly

### 7.3 Browse Interface

Filesystem navigation through downloaded content organized by platform → creator
→ content. Features:

- Breadcrumb navigation showing current path with clickable ancestors
- Directory listings with thumbnails (where available), titles, and metadata
  summaries
- Individual content view: media player/image preview, structured metadata
  display, transcript text
- Delete button per content item with confirmation dialog

### 7.4 History Interface

Searchable, filterable table of all download operations. Features:

- Columns: date, platform, content title, status, file size
- Sortable by any column, default newest-first
- Filter controls for platform, status, and date range
- Per-row actions: view content (completed), retry (failed), delete record (any)
- Error summaries visible inline for failed jobs

---

## 8. Data Model

### 8.1 Jobs Table

| Column            | Type               | Description                                              |
| ----------------- | ------------------ | -------------------------------------------------------- |
| id                | TEXT PRIMARY KEY   | UUID v4                                                  |
| url               | TEXT NOT NULL      | Source URL                                               |
| platform          | TEXT NOT NULL      | `instagram` or `youtube`                                 |
| status            | TEXT NOT NULL      | `pending`, `running`, `completed`, `failed`, `cancelled` |
| title             | TEXT               | Content title (populated after resolution)               |
| progress          | INTEGER DEFAULT 0  | Percentage complete (0–100)                              |
| current_operation | TEXT               | Human-readable description of current activity           |
| error_message     | TEXT               | Error details if failed                                  |
| retry_count       | INTEGER DEFAULT 0  | Number of automatic retries attempted                    |
| bytes_downloaded  | INTEGER DEFAULT 0  | Total bytes downloaded                                   |
| created_at        | TIMESTAMP NOT NULL | Job creation time                                        |
| updated_at        | TIMESTAMP NOT NULL | Last status update                                       |
| completed_at      | TIMESTAMP          | Completion or failure time                               |

### 8.2 Files Table

| Column        | Type                | Description                                         |
| ------------- | ------------------- | --------------------------------------------------- |
| id            | INTEGER PRIMARY KEY | Auto-increment                                      |
| job_id        | TEXT NOT NULL       | Foreign key → jobs.id                               |
| file_path     | TEXT NOT NULL       | Relative path from downloads root                   |
| file_type     | TEXT NOT NULL       | `video`, `image`, `audio`, `metadata`, `transcript` |
| file_size     | INTEGER             | Size in bytes                                       |
| metadata_json | TEXT                | Complete source metadata as JSON                    |
| created_at    | TIMESTAMP NOT NULL  | Record creation time                                |

### 8.3 Settings Table

| Column     | Type               | Description                                          |
| ---------- | ------------------ | ---------------------------------------------------- |
| key        | TEXT PRIMARY KEY   | Configuration key (e.g., `max_concurrent_downloads`) |
| value      | TEXT NOT NULL      | Configuration value                                  |
| updated_at | TIMESTAMP NOT NULL | Last modification time                               |

---

## 9. API Design

### 9.1 Page Routes

| Method | Path             | Description                                                     |
| ------ | ---------------- | --------------------------------------------------------------- |
| GET    | `/`              | Dashboard with URL input and active jobs                        |
| GET    | `/browse`        | Browse root (platform listing)                                  |
| GET    | `/browse/<path>` | Browse subdirectory or content item                             |
| GET    | `/history`       | Download history with filters                                   |
| GET    | `/job/<job_id>`  | Job detail (full page or HTMX partial based on request headers) |

### 9.2 Action Endpoints

| Method | Path                   | Description                                                  |
| ------ | ---------------------- | ------------------------------------------------------------ |
| POST   | `/download`            | Accept URL input, create background job, return HTMX partial |
| POST   | `/job/<job_id>/cancel` | Cancel running/queued job, clean up partial downloads        |
| POST   | `/job/<job_id>/retry`  | Create new job with same URL as a failed job                 |
| DELETE | `/job/<job_id>`        | Delete job record and associated files                       |

### 9.3 Polling Endpoints

| Method | Path                   | Description                                                   |
| ------ | ---------------------- | ------------------------------------------------------------- |
| GET    | `/job/<job_id>/status` | Current progress as HTMX-swappable HTML fragment              |
| GET    | `/jobs/active`         | All active/queued jobs as HTML fragment for dashboard refresh |

All action endpoints include CSRF protection. All endpoints return HTMX partials
when `HX-Request` header is present, full pages otherwise.

---

## 10. Security Considerations

### 10.1 Credential Management

Instagram authentication uses browser cookie import as the primary method. This
approach provides sessions that appear as legitimate browser activity and avoids
storing plaintext passwords. Implementation requirements:

- Never store Instagram passwords in plaintext; prefer session cookies exported
  from Firefox or Chrome
- Encrypt session files at rest using Fernet symmetric encryption
- Store encryption keys in environment variables, never in committed
  configuration files
- Store session files outside the web root with restrictive filesystem
  permissions
- Never log or expose credentials or session tokens in error messages

### 10.2 Input Validation

- Validate all URLs against expected platform patterns before processing
- Reject URLs that do not match known formats with descriptive error messages
- Sanitize file paths generated from metadata to prevent directory traversal
  (all paths must resolve within the downloads directory)
- Escape all HTML output via Jinja2 auto-escaping; exercise particular care with
  user-generated content (captions, descriptions) that may contain malicious
  scripts
- Parameterize all SQLite queries to prevent SQL injection

### 10.3 Web Security

- CSRF protection on all state-changing endpoints
- Restrictive filesystem permissions on the downloads directory
- No exposure of absolute filesystem paths through the web interface
- Content-Security-Policy headers to restrict script sources

### 10.4 Rate Limiting and Anti-Detection

- Randomized delays between Instagram requests (default: 5–10 seconds)
- Exponential backoff with jitter on rate-limit responses (429/401)
- Single concurrent session per Instagram account
- Track request patterns and enforce cooldown periods after sustained activity

---

## 11. Risk Assessment

### 11.1 Risk Matrix

| Risk                                        | Likelihood | Impact | Mitigation                                                                        |
| ------------------------------------------- | ---------- | ------ | --------------------------------------------------------------------------------- |
| Instagram 401 errors / session invalidation | High       | High   | Browser cookie import, throwaway accounts, generous delays, gallery-dl fallback   |
| YouTube JS challenge changes                | Medium     | Medium | Keep yt-dlp updated (daily builds available), Deno runtime ensures JS execution   |
| Core library deprecation                    | Low        | High   | Modular scraper architecture enables library replacement; monitor GitHub activity |
| Instagram account bans                      | Medium     | Medium | Dedicated throwaway accounts only — never personal accounts                       |
| Disk space exhaustion during bulk downloads | Medium     | Low    | Pre-download space check, configurable threshold warning                          |
| Platform ToS changes or legal action        | Low        | High   | User-facing disclaimers, personal-use framing, no circumvention of DRM            |

### 11.2 Instagram-Specific Mitigations

The most effective approach uses browser cookie import rather than
username/password authentication. Users should export cookies from Firefox or
Chrome after logging into a dedicated throwaway account. Additional mitigations:

- Run only one scraping instance at a time
- Maintain 5–10 second randomized delays between requests
- Keep Instaloader updated to receive patches for rotating GraphQL doc_id values
- When Instaloader encounters persistent failures, automatically offer
  gallery-dl as a fallback (different authentication method, different request
  patterns)

### 11.3 Legal and Ethical Considerations

Content scraping exists in a complex legal environment. The application includes
the following safeguards:

- Prominent disclaimer in the UI and documentation: users are responsible for
  compliance with applicable laws and platform terms of service
- No features specifically designed to circumvent DRM or technical protection
  measures
- Application is designed for personal archival use, not redistribution
- No support for downloading content behind paywalls or subscription gates

---

## 12. Implementation Plan

### 12.1 Development Phases

| Phase     | Focus                 | Duration    | Deliverables                                                                                              |
| --------- | --------------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| 1         | Infrastructure        | 1 week      | Flask skeleton, SQLite schema, Pico CSS templates, URL validation, config module                          |
| 2         | YouTube Integration   | 2 weeks     | yt-dlp wrapper, quality selection, transcript extraction, metadata preservation, basic progress reporting |
| 3         | Instagram Integration | 2 weeks     | Instaloader wrapper, cookie-based session management, rate limiting, gallery-dl fallback detection        |
| 4         | Background Processing | 1 week      | Flask-Executor integration, job queue, concurrent downloads, progress polling, retry logic                |
| 5         | UI Polish             | 1 week      | HTMX dynamic updates, file browser, history interface, error display, dark mode, batch URL input          |
| 6         | Testing & Hardening   | 1 week      | Integration tests, error handling refinement, disk space checks, graceful shutdown, deployment docs       |
| **Total** |                       | **8 weeks** | **MVP ready for personal use**                                                                            |

Assumes a single developer working part-time with access to reference
implementations. YouTube (Phase 2) is implemented before Instagram (Phase 3)
because it carries lower technical risk and validates the core architecture.

### 12.2 Testing Strategy

- **Unit tests**: URL parsing, filename sanitization, metadata transformation,
  database operations
- **Integration tests**: Complete flow from URL submission → background download
  → file storage → database persistence
- **Failure mode tests**: Network interruptions, authentication failures, rate
  limiting, disk full, malformed metadata
- **Target coverage**: Minimum 70% for core scraper modules
- **Reference validation**: Compare output structures against
  sohamroyc/social-media-downloader

### 12.3 Graceful Shutdown

On application shutdown (SIGTERM/SIGINT):

1. Stop accepting new jobs
2. Signal running tasks to complete or clean up within a timeout (default: 30
   seconds)
3. Mark interrupted jobs as `pending` for resumption on restart
4. Clean up partial downloads that cannot be resumed

---

## 13. Success Metrics

### 13.1 Functional Criteria

| Metric                                                               | Target                             |
| -------------------------------------------------------------------- | ---------------------------------- |
| YouTube download success rate                                        | ≥ 95% of tested URLs               |
| Instagram download success rate (public profiles, authenticated)     | ≥ 80% of tested profiles           |
| Transcript extraction success rate (videos with available subtitles) | ≥ 90%                              |
| Web interface response time (navigation, form submission)            | < 200 ms                           |
| Job state recovery after restart                                     | 100% of persisted jobs recoverable |

### 13.2 Quality Criteria

| Metric                                                            | Target      |
| ----------------------------------------------------------------- | ----------- |
| Core scraper module test coverage                                 | ≥ 70%       |
| Critical security vulnerabilities in dependencies                 | 0           |
| Clean deployment on fresh Ubuntu 22.04+ following docs            | Pass        |
| Time from URL submission to download start (single job, no queue) | < 5 seconds |

### 13.3 Operational Criteria

| Metric                                           | Target                       |
| ------------------------------------------------ | ---------------------------- |
| Sustained operation without memory leak or crash | ≥ 24 hours with active queue |
| Mean time to address breaking library changes    | < 1 week after upstream fix  |
| Database backup (file copy) success              | 100%                         |

---

## 14. Dependencies & Deployment

### 14.1 Python Packages

```bash
pip install flask flask-executor instaloader gallery-dl "yt-dlp[default]" youtube-transcript-api
```

### 14.2 System Dependencies

```bash
# Deno (JavaScript runtime for yt-dlp YouTube support)
curl -fsSL https://deno.land/install.sh | sh

# FFmpeg (video/audio stream merging)
sudo apt install ffmpeg
```

### 14.3 Deployment

The application targets a single machine running Python 3.10+ on Linux (Ubuntu
22.04+ recommended). No containerization required.

- **Development**: Flask development server (`flask run`)
- **Production**: Gunicorn WSGI server (`gunicorn -w 1 -t 120 app:app`) — single
  worker to avoid SQLite write contention
- **Dependency isolation**: Python virtual environment (`python -m venv .venv`)
- **Backup**: Copy `scraper.db` and `downloads/` directory. SQLite backup can
  use standard file copy while the application is stopped, or `.backup` command
  while running.

### 14.4 Configuration

All configuration is managed through environment variables with sensible
defaults:

| Variable                 | Default                | Description                                     |
| ------------------------ | ---------------------- | ----------------------------------------------- |
| `SCRAPER_DOWNLOAD_DIR`   | `./downloads`          | Root directory for downloaded content           |
| `SCRAPER_DB_PATH`        | `./scraper.db`         | SQLite database path                            |
| `SCRAPER_MAX_CONCURRENT` | `2`                    | Maximum concurrent downloads                    |
| `SCRAPER_IG_DELAY_MIN`   | `5`                    | Minimum seconds between Instagram requests      |
| `SCRAPER_IG_DELAY_MAX`   | `10`                   | Maximum seconds between Instagram requests      |
| `SCRAPER_DISK_WARN_MB`   | `1024`                 | Warn when free disk space falls below this (MB) |
| `SCRAPER_SESSION_KEY`    | (required for IG auth) | Fernet encryption key for session storage       |
| `FLASK_SECRET_KEY`       | (required)             | Flask session/CSRF secret                       |

---

## 15. Appendix

### A. Code Examples

**Instaloader Usage Pattern**

```python
import instaloader

L = instaloader.Instaloader()
# Optionally load session from cookies
# L.load_session_from_file("throwaway_user")

profile = instaloader.Profile.from_username(L.context, "natgeo")
for post in profile.get_posts():
    L.download_post(post, target="natgeo")
```

**yt-dlp Usage Pattern**

```python
import yt_dlp

ydl_opts = {
    'outtmpl': 'downloads/youtube/%(uploader)s/%(title)s/video.%(ext)s',
    'quiet': True,
    'extract_flat': False,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://youtube.com/watch?v=VIDEO_ID'])
```

**youtube-transcript-api Usage (v1.2.4+ instance-based)**

```python
from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.fetch("VIDEO_ID")
full_text = " ".join([snippet.text for snippet in transcript])
```

### B. Reference Projects

| Project                           | Stars   | Value                                                                                   |
| --------------------------------- | ------- | --------------------------------------------------------------------------------------- |
| sohamroyc/social-media-downloader | —       | MIT-licensed Flask app combining yt-dlp + Instaloader; closest reference implementation |
| MeTube                            | ~6,000  | Production-quality yt-dlp web GUI with Docker; demonstrates download queue patterns     |
| YTPTube                           | —       | Advanced download manager with queue management and dual-mode UI                        |
| gallery-dl                        | 14,000+ | Multi-site image/video downloader; fallback for Instagram when Instaloader fails        |

### C. Glossary

| Term               | Definition                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| GraphQL doc_id     | Instagram's internal identifier for API query types, rotated periodically to disrupt scrapers          |
| TLS Fingerprinting | Detection technique analyzing SSL/TLS handshake patterns to identify automated clients                 |
| HTMX               | HTML-first library enabling AJAX, CSS transitions, and server-sent events through HTML attributes      |
| Flask-Executor     | Flask extension wrapping Python's ThreadPoolExecutor with application context preservation             |
| Deno               | Secure JavaScript/TypeScript runtime required by yt-dlp for YouTube's JS challenges since Nov 2025     |
| Fernet             | Symmetric encryption scheme from Python's cryptography library; used for session storage encryption    |
| gallery-dl         | Command-line tool for downloading images and videos from various hosting sites; backup for Instaloader |
