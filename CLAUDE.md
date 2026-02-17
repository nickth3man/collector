# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-17
**Last Updated:** 2026-02-17
**Project:** Content Collector
**Stack:** Flask 3.x, Python 3.10+, HTMX, SQLite

---

## OVERVIEW

Flask web application for downloading media from Instagram and YouTube with
real-time progress tracking via HTMX polling. Uses repository/service pattern
with background threading for downloads.

**CI/CD:** GitHub Actions with Lint, Validate Config, and Test workflows
**Coverage:** 53.5% (179 tests passing)
**Package Manager:** uv (fast Python package manager)

---

## STRUCTURE

```text
./
├── wsgi.py                 # Thin entry point (imports from collector package)
├── src/
│   └── collector/          # Main package
│       ├── __init__.py     # create_app(), signal handlers
│       ├── config/         # Configuration package
│       ├── routes/         # Flask blueprints (API, jobs, pages, sessions)
│       ├── models/         # Data models (Job, File, Settings)
│       ├── services/       # Business logic layer
│       ├── repositories/   # Data access layer
│       ├── scrapers/       # YouTube + Instagram scrapers
│       ├── security/       # CSRF, path traversal protection
│       ├── templates/      # Jinja2 + HTMX templates
│       └── static/         # CDN-first assets with local fallback
├── tests/                  # pytest suite
├── scripts/                # Dev tooling (screenshot capture)
└── downloads/              # Downloaded content storage
```

---

## WHERE TO LOOK

| Task                   | Location                                  | Notes                                     |
| ---------------------- | ----------------------------------------- | ----------------------------------------- |
| Add new route          | `src/collector/routes/`                   | Create blueprint, import in `__init__.py` |
| Modify download logic  | `src/collector/scrapers/`                 | Extend `BaseScraper` abstract class       |
| Change database schema | `src/collector/repositories/` + `models/` | Repository creates tables in `__init__`   |
| Add API endpoint       | `src/collector/routes/api.py`             | JSON API routes                           |
| Update UI              | `src/collector/templates/`                | HTMX fragments in `partials/`             |
| Job management         | `src/collector/services/job_service.py`   | Background task coordination              |
| Security utils         | `src/collector/security/`                 | CSRF tokens, path validation              |

---

## CONVENTIONS

### Code Style

- **Line length:** 100 (Ruff configured)
- **Python:** 3.10+ with `from __future__ import annotations`
- **Types:** Use type hints, `| None` syntax, `collections.abc` imports
- **Formatting:** Ruff formatter (Black-compatible, 10-100x faster)
- **Linting:** Ruff (E, F, W, I, N, UP, B)
- **Type checking:** ty (10-100x faster than mypy/Pyright)
- **Web Assets:** Prettier for CSS, HTML, JSON, JavaScript with 100-char line
  width

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
- Set environment variables after importing Config class (class attributes are evaluated at import time)

### AVOID

- Increasing `SCRAPER_MAX_CONCURRENT` above 2 (IG rate limits)
- Using personal Instagram accounts (use throwaway + cookies)
- Modifying `JOB_UPDATE_ALLOWED_FIELDS` without security review
- Using Windows-style backslash paths in tests without platform detection (use `os.name` checks)

---

## TESTING

### Test Structure

```
tests/
├── integration/           # Integration tests (database indexes, etc.)
├── test_*.py             # Unit tests by module
└── conftest.py           # Shared pytest fixtures
```

### Key Fixtures

- `client`: Flask test client with app context
- `tmp_download_dir`: Temporary downloads directory for file tests
- `app`: Flask application instance

### Security Tests

Path traversal tests are platform-specific:
- **Windows:** Uses backslash paths (`..\\..\\..\\windows\\system32`)
- **Linux:** Uses forward slash paths (`../../../etc/shadow`)

Always use `os.name` checks for platform-specific security test paths.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_pages_routes.py -xvs

# Run specific test
uv run pytest tests/test_pages_routes.py::TestPagesRoutes::test_browse_path_traversal_attack -xvs
```

---

## COMMANDS

```bash
# Development
uv run python -m collector

# Tests
uv run pytest
uv run pytest --cov

# Formatting
uv run ruff format .                    # Python formatting
npx prettier --write .              # Web assets formatting (CSS, HTML, JS, JSON)

# Linting
uv run ruff check .
uv run ruff check --fix .  # Auto-fix issues

# Type checking
uv run ty check
uvx ty check  # Fast one-off check

# Production
uv run gunicorn -w 1 -t 120 wsgi:app
```

---

## NOTES

### Configuration

- **Config class attributes** are evaluated at import time, not instantiation time
- To test with custom config values, set environment variables BEFORE importing:
  ```python
  import os
  os.environ['FLASK_SECRET_KEY'] = 'test'
  from src.collector.config.settings import Config
  ```
- In CI/workflows, use `export` to set environment variables before Python commands

### Deployment

- **Gunicorn workers:** Use `-w 1` only (SQLite write contention)
- **Static assets:** CDN-first with `static/vendor/` fallback
- **Instagram auth:** Cookie-based via `instagram_cookies.txt` (not passwords)
- **Session encryption:** Fernet key required for cookie storage
- **Graceful shutdown:** Signal handlers wait for active downloads
- **File serving:** Always use `safe_send_file()` (path traversal protection)

### GitHub Actions

- **Lint:** Ruff formatting and linting checks
- **Validate Config:** Tests Config class instantiation, validation rules, and environment variable loading
- **Tests:** Full pytest suite with coverage reporting (currently 53.5%)
- All workflows use `uv` package manager (no pip cache)

### Platform Compatibility

- Path separators differ between Windows (`\`) and Linux (`/`)
- Security tests must account for platform differences using `os.name`
- Flask test client behavior may differ between platforms (e.g., absolute path handling)
- Always test security fixes on both platforms when possible
