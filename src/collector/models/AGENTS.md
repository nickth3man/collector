# MODELS KNOWLEDGE BASE

## OVERVIEW

Model classes represent DB entities as typed Python objects. They support
repository and service code with field contracts, conversion helpers, and small
domain behaviors.

## STRUCTURE

- `models/base.py`: shared model behavior, IDs/timestamps, dict conversion, base
  SQL helper methods.
- `models/job.py`: job entity, status/progress/error fields, lifecycle helper
  methods.
- `models/file.py`: file entity linked to a job, metadata helpers, file
  classification helpers.
- `models/settings.py`: key/value setting entity, typed coercion helpers for
  bool/int/float.
- `models/__init__.py`: package exports for model imports.

## CONVENTIONS

- Define entities as class-based, dataclass-like models with typed attrs
  populated from `__init__(**kwargs)`.
- Inherit from `BaseModel` for shared fields and serialization behavior.
- Set `table_name` on concrete models.
- Override `primary_key` when entity key is not `id`.
- Keep `to_dict()` and `from_dict()` symmetrical for each model.
- Encode `datetime` values as ISO strings in `to_dict()`, decode in
  `from_dict()`.
- Keep helper methods entity-focused, for example status transitions or typed
  setting accessors.
- Keep models free of DB connection logic.
- Repository layer owns actual schema creation and migration decisions.

### Type Checking

- All model fields must have type annotations
- Use `from __future__ import annotations` for forward references
- Prefer `| None` over `Optional[T]` for nullable types
- Import types from `collections.abc` when possible (`Mapping`, `Sequence`)
- Run `uvx ty check` to verify type correctness

## WHERE TO LOOK

- Add shared fields/behavior used by multiple models: `models/base.py`.
- Add or change job fields/types: `models/job.py`, then sync repository mapping
  and SQL handling.
- Add or change file fields/types: `models/file.py`, then verify ID typing and
  metadata serialization.
- Add or change settings fields/types: `models/settings.py`, then update typed
  getters/setters.
- Change serialization rules for any entity: update both `to_dict()` and
  `from_dict()` in that model.
- Expose a new model at package level: `models/__init__.py`.
