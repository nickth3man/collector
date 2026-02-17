# SECURITY MODULE GUIDE

## OVERVIEW
Security helpers for request integrity and safe file access.
Use this module to enforce CSRF checks and block path traversal.

## STRUCTURE
- `security/csrf.py`
  - Token lifecycle helpers: generate, store in session, extract from request
  - Route guard helpers: `validate_csrf_request(request)`, `csrf_protected`
- `security/paths.py`
  - Path containment checks: `is_within_base()`, `resolve_user_path()`
  - Safe file response wrapper: `safe_send_file()`
  - Security exception: `PathSecurityError`
- `security/__init__.py`
  - Package marker for security helpers

## CONVENTIONS
- State-changing routes call `validate_csrf_request(request)` before mutation.
- Enforce CSRF on `POST`, `PUT`, `PATCH`, `DELETE` handlers.
- Accept CSRF token from form field `csrf_token` or header `X-CSRFToken`.
- Session key for CSRF token is `_csrf_token`.
- Token compare uses constant-time check via `hmac.compare_digest`.
- If CSRF validation fails, return `400` and stop route logic.
- Convert user-controlled paths with `resolve_user_path(base_dir, user_path)`.
- Treat `PathSecurityError` as a traversal attempt, deny request.
- Never pass raw user path into `send_file`.
- File serving always goes through `safe_send_file(base_dir, file_path, ...)`.
- `safe_send_file()` must enforce:
  - path is within base directory
  - path exists
  - path is a file
- Violation behavior in `safe_send_file()`:
  - outside base dir -> `403`
  - missing or non-file path -> `404`

## WHERE TO LOOK
- Add CSRF to a route: `security/csrf.py` -> `validate_csrf_request`, `csrf_protected`
- Debug missing CSRF token handling: `security/csrf.py` -> `extract_csrf_token`
- Change token/session constants: `security/csrf.py` constants block
- Validate user file path input: `security/paths.py` -> `resolve_user_path`
- Diagnose traversal failures: `security/paths.py` -> `PathSecurityError`, `is_within_base`
- Harden file download endpoint: `security/paths.py` -> `safe_send_file`
