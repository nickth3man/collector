# SERVICES KNOWLEDGE BASE

## OVERVIEW

Service layer holds orchestration and domain workflows between routes and
repositories. Keep HTTP concerns out, keep SQL out, keep cross-repository logic
here.

## STRUCTURE

- `job_service.py`: Job lifecycle orchestration, safe field updates, retry
  creation, cancel/delete flows.
- `scraper_service.py`: URL validation, platform detection, scraper selection,
  download execution state machine.
- `session_service.py`: Route-facing session workflows,
  upload/load/validate/list/delete with structured result dicts.
- `session_manager.py`: Encrypted session persistence, cookies parsing, session
  file I/O, expiry checks.
- `executor_adapter.py`: Minimal task execution abstraction via daemon thread
  submission.
- `__init__.py`: Public service exports.

## CONVENTIONS

- Services own business rules and orchestration, routes call services.
- Services call repositories, never open DB connections directly.
- Prefer constructor injection with sane defaults for repositories/managers.
- Keep method outputs route-friendly, return structured dicts for success/error
  where needed.
- Use logging for operational visibility, include job/session identifiers in
  messages.
- Use UTC ISO timestamps for completion or lifecycle markers.

### Type Checking

- All service methods must have type annotations
- Constructor parameters should be typed with concrete classes or protocols
- Return types should be explicit, avoid bare `dict` (use `dict[str, Any]` or
  structured TypedDict)
- Run `uvx ty check` before committing service changes

- `JobService` patterns:
- Enforce update allowlist in `update_job`, reject unknown fields.
- Use repository methods for status/progress/statistics mutations.
- Handle file cleanup through repository records plus configured download root.

- `ScraperService` patterns:
- Validate URL shape first, detect supported platform before execution.
- Build progress callback that delegates progress writes to repository.
- Mark job `running`, then terminal `completed` or `failed` with timestamp.
- Resolve Instagram session through `SessionManager` when available.

- `SessionManager` patterns:
- Persist sessions under `config_dir/sessions/*.session`.
- Encrypt/decrypt with Fernet, fail fast if encryption key missing.
- Parse Netscape `cookies.txt`, keep Instagram auth cookies only.
- Sanitize username before filename use.
- Validate session freshness from `loaded_at` against expiry window.

- `ExecutorAdapter` patterns:
- `submit_job(func, *args)` starts daemon `Thread` and returns handle.
- Keep adapter thin so execution backend can be swapped later.

## WHERE TO LOOK

- Add or change job retry/cancel/delete behavior: `services/job_service.py`
- Change progress update or terminal status behavior:
  `services/scraper_service.py`
- Change task execution backend semantics: `services/executor_adapter.py`
- Change session upload/load/validation API contract:
  `services/session_service.py`
- Change encryption, cookie parsing, session file rules:
  `services/session_manager.py`
- Export a new service for app wiring: `services/__init__.py`
