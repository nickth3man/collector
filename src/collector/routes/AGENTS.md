# ROUTES KNOWLEDGE BASE

## OVERVIEW

This directory contains Flask blueprints only. Each module owns one route domain
and delegates business logic to services.

## STRUCTURE

- `__init__.py`: re-exports `pages_bp`, `jobs_bp`, `sessions_bp`, `api_bp`.
- `pages.py`: UI page routes, file browsing, preview rendering, history filters.
- `jobs.py`: job lifecycle routes, create/cancel/retry/delete, HTMX job
  fragments.
- `sessions.py`: Instagram session upload/list/delete flows.
- `api.py`: JSON config status endpoint for frontend checks.

## CONVENTIONS

- **Blueprint ownership:** keep route concerns local to one module, avoid
  cross-module route handlers.
- **Registration source:** blueprints are mounted in `app_factory.py`, not from
  this package.
- **CSRF rule:** every state-changing route (`POST`, `DELETE`) calls
  `validate_csrf_request(request)` first.
- **HTMX detection:** use `"HX-Request" in request.headers` to branch partial vs
  full-page response.
- **Error handling:** use `abort()` for HTTP status failures (`403`, `404`,
  etc.).
- **User feedback:** use `flash()` for non-HTMX redirects and user-visible
  success/error messages.
- **Response split:** HTMX paths return fragments or short HTML/error payloads,
  full requests redirect or render templates.
- **Service boundary:** routes orchestrate request/response only, heavy logic
  lives in service layer.

### Type Checking

- Route handler return types should be explicit: `str`, `Response`,
  `tuple[str, int]`
- Import Flask types: `Request`, `Response`, `Blueprint`
- Service dependencies should be typed at module level
- Run `uvx ty check` to verify Flask type usage

## ANTI-PATTERNS

- Skipping CSRF checks on any mutating endpoint.
- Returning full-page templates to HTMX polling/fragment requests.
- Embedding business rules in route functions instead of calling services.
- Using inconsistent error strategy, for example raw strings for non-HTMX
  failures instead of `abort()` or `flash()+redirect`.
- Mutating data inside GET routes.
- Bypassing `__init__.py` exports when importing blueprints in application
  setup.
