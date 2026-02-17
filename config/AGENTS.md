# CONFIG KNOWLEDGE BASE

**Generated:** 2026-02-17  
**Scope:** `config/` package only

## OVERVIEW

Centralized runtime configuration for scraper and Flask settings.  
Defaults come from environment variables, then validated through `Config.validate()`.

## STRUCTURE

| File | Role | Notes |
|------|------|-------|
| `config/settings.py` | Primary settings source | `Config` class reads env vars, exposes typed class attributes, validates ranges and required values |
| `config/database.py` | DB config + connection helpers | `DatabaseConfig` owns SQLite path setup and context-managed connections |
| `config/__init__.py` | Package export surface | Re-exports config symbols for package-level imports |
| `config.py` (repo root) | Backward-compat shim | Re-exports from `config.settings` so legacy imports keep working |

## CONVENTIONS

- Env naming prefixes: `SCRAPER_*` for scraper/runtime, `FLASK_*` for Flask/app concerns.
- `Config` values are class attributes, loaded via `os.environ.get("NAME", default)`.
- Cast at declaration point, for example `int(...)`, `float(...)`, bool parsing via lowercase membership checks.
- Path settings use `pathlib.Path`, not raw strings.
- Validation lives in `Config.validate()`, returns `list[str]` errors instead of raising.
- Directory creation checks live in config layer (`validate`, `ensure_directories`, DB path parent creation).
- Keep constants that shape behavior close to settings, URL patterns, status enums, file-type enums.

## WHERE TO LOOK

- Add new app setting: `config/settings.py` inside `Config` with env key, default, and type cast.
- Add rule for new setting: extend `Config.validate()` with explicit error text.
- Add directory requirement: update `Config.ensure_directories()` or `DatabaseConfig._ensure_db_directory()`.
- Add DB connection behavior: `config/database.py` in `DatabaseConfig` helpers.
- Preserve legacy import paths: if new symbol must be old-import compatible, re-export through root `config.py`.
