# REPOSITORIES KNOWLEDGE BASE

## OVERVIEW

Data access layer for SQLite-backed models used by the app.
Each repository wraps SQL, maps rows to models, and keeps query rules in one place.

## STRUCTURE

- `base.py`:
  - `BaseRepository[T]` generic CRUD foundation.
  - Central DB config resolution via `_get_db_config()`.
  - Shared helpers: `execute_custom_query()`, `execute_custom_update()`, `find_by()`, `find_one_by()`.
- `job_repository.py`:
  - `JobRepository` for job lifecycle and status/progress updates.
  - Adds query extensions like `status__in` handling.
- `file_repository.py`:
  - `FileRepository` for files linked to jobs.
  - Handles file-specific read/write paths and metadata JSON helpers.
- `settings_repository.py`:
  - `SettingsRepository` for key-value settings.
  - Typed getters/setters (`bool`, `int`, `float`) and batch operations.
- `__init__.py`:
  - Package exports for repository classes.

## CONVENTIONS

- Initialize schema in repository construction, call `self._ensure_table()` from `__init__` when adding new repositories.
- Use `BaseRepository` as the only parent for concrete repositories.
- Use `db_config.get_connection()` context manager for write transactions.
- Assume SQLite row factory returns dict-like rows, access fields by key.
- Convert rows to model instances with `Model.from_dict(...)` for domain-facing methods.
- Return plain dicts only for aggregate or mixed payload methods (example: job plus files, stats).
- Keep SQL close to repository methods, prefer parameterized placeholders (`?`).
- Put repository-specific filtering logic in repository methods, not in routes or services.

### Type Checking

- Repository methods must have typed signatures
- Use generic `BaseRepository[ModelType]` when extending base
- Database row types should be `dict[str, Any]` when using row factory
- Return model instances, not raw dicts, from finder methods
- Run `uvx ty check` to catch model/DB mapping issues

## ANTI-PATTERNS

- Never execute raw DB queries in routes, go through repositories.
- Never return raw cursor objects outside repositories.
- Never build SQL with string-concatenated user input.
- Never spread one entity's query logic across multiple repositories.
- Never bypass model mapping for normal entity reads.
