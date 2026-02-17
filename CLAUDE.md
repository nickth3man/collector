
## Common Commands

### Development
```bash
# Run development server
uv run python app.py

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_youtube_scraper.py

# Run tests with coverage
uv run pytest --cov=.

# Format code
uv run black .

# Lint code
uv run ruff check .
```

### Production
```bash
# Production server (single worker for SQLite compatibility)
uv run gunicorn -w 1 -t 120 app:app
```

## Architecture Overview

This is a Flask-based web application for downloading media from Instagram and YouTube. The architecture follows a job queue pattern with background scraping tasks and real-time progress updates via HTMX.

### Core Components

- **app.py**: Flask application entry point containing all routes, job management functions, and database operations. Uses Flask-Executor for background task execution.

- **config.py**: Centralized configuration using environment variables with validation. Defines URL patterns, job statuses, and file type constants.

- **scrapers/**: Platform-specific content extraction
  - `base_scraper.py`: Abstract `BaseScraper` class defining the interface for all scrapers. Provides shared utilities: filename sanitization, metadata saving, database file records.
  - `youtube_scraper.py`: Uses yt-dlp for video/playlist/channel downloads and youtube-transcript-api for caption extraction.
  - `instagram_scraper.py`: Primary uses Instaloader for authenticated session downloads; falls back to gallery-dl for carousel/gallery posts.

### Database Schema

SQLite database (default: `scraper.db`) with three tables:

- **jobs**: Tracks download jobs (id, url, platform, status, progress, error_message, retry_count, timestamps)
- **files**: Records downloaded files linked to jobs (job_id foreign key with CASCADE delete)
- **settings**: Key-value store for application settings

### Request Flow

1. User submits URL via `/download` (POST)
2. `detect_platform()` identifies YouTube or Instagram from URL patterns in config.py
3. `create_job()` creates a pending job record
4. `execute_download()` runs in background via Flask-Executor
5. Scraper reports progress via callback, updating job record
6. HTMX polls `/job/<id>/status` for real-time UI updates

### HTMX Integration

The frontend uses HTMX for dynamic content without page reloads. Key patterns:
- Routes check `HX-Request` header to return partials vs full pages
- Templates in `templates/partials/` are HTMX fragments
- `templates/base.html` includes HTMX library and Pico CSS

### Important Constraints

- **Single-worker production**: Use `gunicorn -w 1` to avoid SQLite write contention
- **Rate limiting**: Instagram requests have configurable delays (SCRAPER_IG_DELAY_MIN/MAX)
- **Session encryption**: Instagram cookies encrypted with Fernet key (SCRAPER_SESSION_KEY)
- **Use throwaway accounts**: Never use personal Instagram credentials for scraping

### Environment Variables

Key configuration via environment variables or `.env`:
- `FLASK_SECRET_KEY`: Required for production (Flask sessions/CSRF)
- `SCRAPER_SESSION_KEY`: Fernet key for encrypting Instagram cookies
- `SCRAPER_DOWNLOAD_DIR`: Root for downloaded content (default: `./downloads`)
- `SCRAPER_DB_PATH`: SQLite database path (default: `./scraper.db`)
- `SCRAPER_MAX_CONCURRENT`: Max parallel downloads (default: 2)
