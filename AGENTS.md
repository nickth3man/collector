# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-17  
**Project:** Content Collector  
**Stack:** Flask 3.x, Python 3.10+, HTMX, SQLite

---

## OVERVIEW

Flask web application for downloading media from Instagram and YouTube with real-time progress tracking via HTMX polling. Uses repository/service pattern with background threading for downloads.

---

## STRUCTURE

```
./
├── wsgi.py                 # Thin entry point (imports from collector package)
├── config.py               # Backward-compat config exports
├── src/
│   └── collector/          # Main package
│       ├── __init__.py     # create_app(), signal handlers
│       ├── config/         # Configuration package
│       ├── routes/         # Flask blueprints (API, jobs, pages, sessions)
│       ├── models/         # Data models (Job, File, Settings)
│       ├── services/       # Business logic layer
│       ├── repositories/   # Data access layer
│       ├── scrapers/       # YouTube + Instagram scrapers
│       └── security/       # CSRF, path traversal protection
├── templates/              # Jinja2 + HTMX templates
├── static/                 # CDN-first assets with local fallback
├── tests/                  # pytest suite
└── downloads/              # Downloaded content storage
```

---

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new route | `src/collector/routes/` | Create blueprint, import in `__init__.py` |
| Modify download logic | `src/collector/scrapers/` | Extend `BaseScraper` abstract class |
| Change database schema | `src/collector/repositories/` + `models/` | Repository creates tables in `__init__` |
| Add API endpoint | `src/collector/routes/api.py` | JSON API routes |
| Update UI | `templates/` | HTMX fragments in `partials/` |
| Job management | `src/collector/services/job_service.py` | Background task coordination |
| Security utils | `src/collector/security/` | CSRF tokens, path validation |

---

## CONVENTIONS

### Code Style
- **Line length:** 100 (Black + Ruff configured)
- **Python:** 3.10+ with `from __future__ import annotations`
- **Types:** Use type hints, `| None` syntax, `collections.abc` imports
- **Formatting:** Black with Ruff linting (E, F, W, I, N, UP, B)

### Naming
- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/vars:** `snake_case`
- **Private:** `_leading_underscore`
- **Constants:** `UPPER_SNAKE_CASE`

### Import Pattern
```python
from __future__ import annotations

import stdlib

import third_party

from .local_modules import X  # Relative imports within package
```

### Flask Patterns
- **Blueprints:** All routes in `src/collector/routes/` package
- **Factory:** `create_app()` in `src/collector/__init__.py`
- **CSRF:** All POST/DELETE routes must call `validate_csrf_request(request)`
- **HTMX:** Check `"HX-Request" in request.headers` for fragment responses

### Database
- **SQLite** with row factory → dict access
- **Pattern:** Repository classes initialize their own tables
- **Context manager:** `with get_db() as conn:`

---

## ANTI-PATTERNS

### NEVER
- Add routes outside `src/collector/routes/`
- Skip CSRF validation on state-changing routes
- Store files outside `SCRAPER_DOWNLOAD_DIR`
- Access database directly from routes (use repositories)
- Block main thread (use `ExecutorAdapter` for background work)

### AVOID
- Increasing `SCRAPER_MAX_CONCURRENT` above 2 (IG rate limits)
- Using personal Instagram accounts (use throwaway + cookies)
- Modifying `JOB_UPDATE_ALLOWED_FIELDS` without security review

---

## COMMANDS

```bash
# Development
uv run python -m collector

# Tests
uv run pytest
uv run pytest --cov

# Linting
uv run black .
uv run ruff check .

# Production
uv run gunicorn -w 1 -t 120 wsgi:app
```

---

## NOTES

- **Gunicorn workers:** Use `-w 1` only (SQLite write contention)
- **Static assets:** CDN-first with `static/vendor/` fallback
- **Instagram auth:** Cookie-based via `instagram_cookies.txt` (not passwords)
- **Session encryption:** Fernet key required for cookie storage
- **Graceful shutdown:** Signal handlers wait for active downloads
- **File serving:** Always use `safe_send_file()` (path traversal protection)
