# Database Indexes Implementation Plan

## 1. Overview

### Why Indexes Matter
Database indexes are critical for query performance and scalability:

- **Query Performance**: Indexes reduce the number of rows examined during queries, converting O(n) table scans into O(log n) index lookups
- **Scalability**: Without indexes, query performance degrades linearly as data grows. With indexes, performance remains consistent
- **Resource Efficiency**: Indexes reduce disk I/O and CPU usage by allowing the database to locate data quickly
- **User Experience**: Fast queries ensure responsive UI, especially for dashboard and statistics views

### Current State
- **No indexes exist** on any tables in the database
- All queries perform full table scans
- Repository methods like `get_active_jobs()`, `get_recent_jobs()`, `get_job_statistics()` will become slow as data grows
- File queries like `get_job_files()` and `get_orphaned_files()` will degrade with thousands of files

### Target State
- Strategic indexes on commonly queried columns
- Composite indexes for complex query patterns
- Efficient query execution plans verified via `EXPLAIN QUERY PLAN`
- Measurable performance improvements documented

## 2. Query Analysis

### JobRepository Queries

#### `get_active_jobs()`
**Query Pattern:**
```sql
SELECT * FROM jobs
WHERE status IN ('pending', 'running', 'cancelling')
```
**Analysis:**
- Filters by `status` column with IN clause
- Called frequently to check for active jobs
- Without index: Full table scan
- **Index needed**: `idx_jobs_status`

#### `get_recent_jobs()`
**Query Pattern:**
```sql
SELECT * FROM jobs
ORDER BY created_at DESC
LIMIT ?
```
**Analysis:**
- Sorts by `created_at` in descending order
- Called for dashboard display
- Without index: Full table scan + sort
- **Index needed**: `idx_jobs_created_at` (DESC)

#### `get_job_statistics()`
**Query Pattern:**
```sql
SELECT status, COUNT(*) as count
FROM jobs
GROUP BY status
```
**Analysis:**
- Groups by `status` column
- Called for statistics dashboard
- Without index: Full table scan
- **Index needed**: `idx_jobs_status`

#### `find_by(status=...)`
**Query Pattern:**
```sql
SELECT * FROM jobs
WHERE status = ?
```
**Analysis:**
- Direct equality filter on `status`
- Common query pattern
- **Index needed**: `idx_jobs_status`

#### `find_by(platform=...)`
**Query Pattern:**
```sql
SELECT * FROM jobs
WHERE platform = ?
```
**Analysis:**
- Direct equality filter on `platform`
- Used for filtering by platform
- **Index needed**: `idx_jobs_platform`

#### Combined Pattern: Status + Date
**Common real-world query:**
```sql
SELECT * FROM jobs
WHERE status IN ('pending', 'running')
ORDER BY created_at DESC
```
**Analysis:**
- Filters by status AND sorts by date
- Composite index most efficient
- **Index needed**: `idx_jobs_status_created` (composite)

### FileRepository Queries

#### `get_job_files()`
**Query Pattern:**
```sql
SELECT * FROM files
WHERE job_id = ?
ORDER BY created_at ASC
```
**Analysis:**
- Filters by `job_id` (foreign key)
- Sorts by `created_at`
- Called for every job detail view
- **Index needed**: `idx_files_job_id`
- **Secondary index**: `idx_files_created_at`

#### `get_files_by_type()`
**Query Pattern:**
```sql
SELECT * FROM files
WHERE file_type = ?
```
**Analysis:**
- Filters by `file_type`
- Used for filtering by media type
- **Index needed**: `idx_files_file_type`

#### `get_orphaned_files()`
**Query Pattern:**
```sql
SELECT f.* FROM files f
LEFT JOIN jobs j ON f.job_id = j.id
WHERE j.id IS NULL
```
**Analysis:**
- Join on `job_id`
- Finds files without valid jobs
- **Index needed**: `idx_files_job_id` (for join performance)

#### `get_job_files_by_type()`
**Query Pattern:**
```sql
SELECT * FROM files
WHERE job_id = ? AND file_type = ?
ORDER BY created_at ASC
```
**Analysis:**
- Filters by both `job_id` and `file_type`
- Composite index would help
- **Index needed**: `idx_files_job_id_type` (composite, optional)

## 3. Proposed Indexes

### Jobs Table Indexes

#### Single-Column Indexes

**idx_jobs_status**
- **Columns**: `status`
- **Type**: B-tree (default)
- **Justification**: Benefits `get_active_jobs()`, `get_job_statistics()`, `find_by(status=...)`
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_jobs_status
ON jobs(status);
```

**idx_jobs_platform**
- **Columns**: `platform`
- **Type**: B-tree
- **Justification**: Benefits `find_by(platform=...)`, platform-based filtering
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_jobs_platform
ON jobs(platform);
```

**idx_jobs_created_at**
- **Columns**: `created_at DESC`
- **Type**: B-tree with DESC
- **Justification**: Benefits `get_recent_jobs()`, any time-ordered queries
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_jobs_created_at
ON jobs(created_at DESC);
```

#### Composite Indexes

**idx_jobs_status_created**
- **Columns**: `(status, created_at DESC)`
- **Type**: Composite B-tree
- **Justification**: Optimizes queries filtering by status AND sorting by date
  - Covers `get_active_jobs()` with date ordering
  - More efficient than two separate indexes
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_jobs_status_created
ON jobs(status, created_at DESC);
```

### Files Table Indexes

#### Single-Column Indexes

**idx_files_job_id**
- **Columns**: `job_id`
- **Type**: B-tree
- **Justification**:
  - Benefits `get_job_files()`
  - Speeds up JOIN with jobs table
  - Critical for foreign key performance
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_files_job_id
ON files(job_id);
```

**idx_files_file_type**
- **Columns**: `file_type`
- **Type**: B-tree
- **Justification**: Benefits `get_files_by_type()`, `get_video_files()`, etc.
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_files_file_type
ON files(file_type);
```

**idx_files_created_at**
- **Columns**: `created_at DESC`
- **Type**: B-tree with DESC
- **Justification**: Benefits time-based file queries, recent files display
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_files_created_at
ON files(created_at DESC);
```

#### Composite Indexes (Optional)

**idx_files_job_id_type**
- **Columns**: `(job_id, file_type)`
- **Type**: Composite B-tree
- **Justification**: Optimizes `get_job_files_by_type()`
  - Covers queries filtering by job AND type
- **SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_files_job_id_type
ON files(job_id, file_type);
```

### Settings Table Indexes

**No indexes needed** - Settings table uses primary key (`key`) for all queries and has very few rows (likely < 100).

## 4. Implementation Approach

### Option A: Model-based (Recommended)

**Rationale:**
- Fits existing codebase architecture
- Centralized index definitions in models
- Consistent with table creation approach
- Easy to maintain and version control

**Architecture:**
1. Add `get_indexes_sql()` class method to `BaseModel`
2. Each model defines its indexes as a list of dictionaries
3. Base model generates CREATE INDEX statements
4. Call during database initialization
5. Check for existing indexes before creating

**Advantages:**
- Declarative (indexes defined with models)
- Self-documenting (index definitions visible in models)
- Automatic creation on app startup
- Handles schema migrations gracefully

### Option B: Migration File (Alternative)

**Rationale:**
- Traditional database migration approach
- Better for production environments
- Explicit version control of schema changes

**Architecture:**
1. Create `migrations/` directory
2. Add `001_add_indexes.py` migration
3. Track migration state in settings table
4. Run migrations on startup

**Disadvantages:**
- More complex for this use case
- Requires migration tracking system
- Overkill for current needs

## 5. Implementation Steps

### Step 1: Add Index Support to BaseModel

**File**: `src/collector/models/base.py`

**Changes:**
1. Add `indexes` class variable to store index definitions
2. Add `get_indexes_sql()` class method
3. Add helper method for index name generation

**Before:**
```python
class BaseModel:
    table_name: ClassVar[str] = ""
    primary_key: ClassVar[str] = "id"
```

**After:**
```python
class BaseModel:
    table_name: ClassVar[str] = ""
    primary_key: ClassVar[str] = "id"
    indexes: ClassVar[list[dict[str, Any]]] = []

    @classmethod
    def get_indexes_sql(cls) -> list[str]:
        """Get SQL statements to create indexes for this model.

        Returns:
            List of CREATE INDEX SQL statements.
        """
        table_name = cls.get_table_name()
        index_statements = []

        for index_def in cls.indexeses:
            columns = index_def["columns"]
            unique = index_def.get("unique", False)
            index_name = index_def.get("name", cls._generate_index_name(columns))

            # Build column list with optional DESC
            column_defs = []
            for col in columns:
                if isinstance(col, tuple):
                    # (column_name, direction)
                    column_defs.append(f"{col[0]} {col[1]}")
                else:
                    column_defs.append(str(col))

            columns_str = ", ".join(column_defs)
            unique_str = "UNIQUE " if unique else ""

            sql = f"""
            CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
            ON {table_name}({columns_str})
            """.strip()

            index_statements.append(sql)

        return index_statements

    @classmethod
    def _generate_index_name(cls, columns: list[Any]) -> str:
        """Generate a consistent index name from columns.

        Args:
            columns: List of column definitions.

        Returns:
            Generated index name.
        """
        table_name = cls.get_table_name()
        col_names = []

        for col in columns:
            if isinstance(col, tuple):
                col_names.append(col[0])
            else:
                col_names.append(str(col))

        cols_str = "_".join(col_names)
        return f"idx_{table_name}_{cols_str}"
```

### Step 2: Define Indexes in Job Model

**File**: `src/collector/models/job.py`

**Changes:**
1. Add `indexes` class variable
2. Define all job-related indexes

**Implementation:**
```python
class Job(BaseModel):
    table_name = "jobs"

    # Index definitions
    indexes: ClassVar[list[dict[str, Any]]] = [
        {
            "columns": ["status"],
            "unique": False,
            "name": "idx_jobs_status"
        },
        {
            "columns": ["platform"],
            "unique": False,
            "name": "idx_jobs_platform"
        },
        {
            "columns": [("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_created_at"
        },
        {
            "columns": ["status", ("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_status_created"
        }
    ]

    # ... rest of the class remains unchanged
```

### Step 3: Define Indexes in File Model

**File**: `src/collector/models/file.py`

**Changes:**
1. Add `indexes` class variable
2. Define all file-related indexes

**Implementation:**
```python
class File(BaseModel):
    table_name = "files"

    # Index definitions
    indexes: ClassVar[list[dict[str, Any]]] = [
        {
            "columns": ["job_id"],
            "unique": False,
            "name": "idx_files_job_id"
        },
        {
            "columns": ["file_type"],
            "unique": False,
            "name": "idx_files_file_type"
        },
        {
            "columns": [("created_at", "DESC")],
            "unique": False,
            "name": "idx_files_created_at"
        },
        {
            "columns": ["job_id", "file_type"],
            "unique": False,
            "name": "idx_files_job_id_type"
        }
    ]

    # ... rest of the class remains unchanged
```

### Step 4: Add Settings Model (No Indexes)

**File**: `src/collector/models/settings.py`

**Implementation:**
```python
class Settings(BaseModel):
    table_name = "settings"

    # No indexes needed for settings table
    indexes: ClassVar[list[dict[str, Any]]] = []

    # ... rest of the class remains unchanged
```

### Step 5: Create Index Creation Logic

**File**: `src/collector/config/database.py`

**Changes:**
1. Add `create_indexes()` method to `DatabaseConfig`
2. Add `ensure_indexes()` method that checks and creates indexes
3. Integrate into initialization flow

**Implementation:**
```python
class DatabaseConfig:
    # ... existing code ...

    def create_indexes(self, model_classes: list[type]) -> None:
        """Create indexes for the given model classes.

        Args:
            model_classes: List of model classes to create indexes for.
        """
        with self.get_connection() as conn:
            for model_class in model_classes:
                index_sqls = model_class.get_indexes_sql()

                for index_sql in index_sqls:
                    try:
                        conn.execute(index_sql)
                        print(f"Created index for {model_class.table_name}")
                    except sqlite3.OperationalError as e:
                        print(f"Index creation warning: {e}")
                        # Continue even if index exists

            conn.commit()

    def ensure_indexes(self, model_classes: list[type]) -> None:
        """Ensure all indexes exist for the given models.

        This method checks for existing indexes and creates any missing ones.

        Args:
            model_classes: List of model classes to check/create indexes for.
        """
        with self.get_connection() as conn:
            for model_class in model_classes:
                table_name = model_class.get_table_name()

                # Get existing indexes for this table
                existing_indexes = conn.execute(
                    f"SELECT name FROM sqlite_master "
                    f"WHERE type='index' AND tbl_name='{table_name}'"
                ).fetchall()

                existing_index_names = {row[0] for row in existing_indexes}

                # Create missing indexes
                index_sqls = model_class.get_indexes_sql()
                for index_sql in index_sqls:
                    # Extract index name from SQL
                    import re
                    match = re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)', index_sql, re.IGNORECASE)
                    if match:
                        index_name = match.group(1)

                        if index_name not in existing_index_names:
                            try:
                                conn.execute(index_sql)
                                print(f"Created missing index: {index_name}")
                            except sqlite3.OperationalError as e:
                                print(f"Error creating index {index_name}: {e}")

            conn.commit()

    def initialize_schema(self, model_classes: list[type]) -> None:
        """Initialize database schema including tables and indexes.

        Args:
            model_classes: List of model classes to initialize.
        """
        # Create tables first
        for model_class in model_classes:
            create_sql = model_class.get_create_table_sql()
            with self.get_connection() as conn:
                conn.execute(create_sql)
                conn.commit()

        # Then create indexes
        self.ensure_indexes(model_classes)
```

### Step 6: Integrate into Application Initialization

**File**: `src/collector/app.py` (or wherever Flask app initializes)

**Changes:**
1. Import model classes
2. Call index creation during app initialization

**Implementation:**
```python
from src.collector.models.job import Job
from src.collector.models.file import File
from src.collector.models.settings import Settings
from src.collector.config.database import get_db_config

def create_app():
    """Application factory."""
    app = Flask(__name__)

    # ... existing configuration ...

    # Initialize database schema
    with app.app_context():
        db_config = get_db_config()
        model_classes = [Job, File, Settings]
        db_config.initialize_schema(model_classes)

    return app
```

### Step 7: Handle Existing Databases (Migration)

**Approach:**
1. Use `IF NOT EXISTS` in all CREATE INDEX statements
2. Check for existing indexes before creating
3. Log index creation for debugging
4. Handle failures gracefully

**Implementation:**
The `ensure_indexes()` method in Step 5 already handles this:
- Checks existing indexes in `sqlite_master`
- Only creates missing indexes
- Logs all actions
- Handles errors gracefully

## 6. Migration Strategy

### For Existing Databases

**Strategy: Idempotent Index Creation**

**Key Principles:**
1. Use `CREATE INDEX IF NOT EXISTS` for safety
2. Check existing indexes in `sqlite_master`
3. Create only missing indexes
4. Log all actions for debugging
5. Never drop indexes automatically

**Implementation:**
```python
def migrate_existing_database(db_config: DatabaseConfig) -> None:
    """Migrate existing database to add indexes.

    Args:
        db_config: Database configuration instance.
    """
    print("Starting database index migration...")

    model_classes = [Job, File, Settings]

    for model_class in model_classes:
        table_name = model_class.get_table_name()
        print(f"\nChecking indexes for {table_name}...")

        with db_config.get_connection() as conn:
            # Get current indexes
            current_indexes = conn.execute(
                f"SELECT name FROM sqlite_master "
                f"WHERE type='index' AND tbl_name='{table_name}'"
            ).fetchall()

            current_index_names = {row[0] for row in current_indexes}
            print(f"  Existing indexes: {current_index_names}")

            # Get required indexes
            required_indexes = model_class.get_indexes_sql()

            for index_sql in required_indexes:
                # Extract index name
                import re
                match = re.search(
                    r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)',
                    index_sql,
                    re.IGNORECASE
                )

                if match:
                    index_name = match.group(1)

                    if index_name not in current_index_names:
                        print(f"  Creating index: {index_name}")
                        try:
                            conn.execute(index_sql)
                            conn.commit()
                            print(f"    ✓ Successfully created {index_name}")
                        except Exception as e:
                            print(f"    ✗ Error creating {index_name}: {e}")
                    else:
                        print(f"  Index already exists: {index_name}")

    print("\nMigration complete!")
```

### Rollback Strategy

**If issues occur:**
1. Indexes can be dropped manually:
   ```sql
   DROP INDEX IF EXISTS idx_jobs_status;
   DROP INDEX IF EXISTS idx_jobs_platform;
   DROP INDEX IF EXISTS idx_files_job_id;
   -- etc.
   ```
2. Application will continue to work (just slower)
3. No data loss, only performance impact

### Verification Strategy

**After migration:**
1. Run verification script to check all indexes exist
2. Run `EXPLAIN QUERY PLAN` on key queries
3. Benchmark query performance
4. Compare before/after metrics

## 7. Verification

### Check Indexes Exist

**SQL Query:**
```sql
SELECT
    tbl_name,
    name,
    sql
FROM sqlite_master
WHERE type = 'index'
    AND tbl_name IN ('jobs', 'files')
    AND name LIKE 'idx_%'
ORDER BY tbl_name, name;
```

**Expected Output:**
```
jobs|idx_jobs_created_at|CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC)
jobs|idx_jobs_platform|CREATE INDEX idx_jobs_platform ON jobs(platform)
jobs|idx_jobs_status|CREATE INDEX idx_jobs_status ON jobs(status)
jobs|idx_jobs_status_created|CREATE INDEX idx_jobs_status_created ON jobs(status, created_at DESC)
files|idx_files_created_at|CREATE INDEX idx_files_created_at ON files(created_at DESC)
files|idx_files_file_type|CREATE INDEX idx_files_file_type ON files(file_type)
files|idx_files_job_id|CREATE INDEX idx_files_job_id ON files(job_id)
files|idx_files_job_id_type|CREATE INDEX idx_files_job_id_type ON files(job_id, file_type)
```

### Verify Index Usage with EXPLAIN QUERY PLAN

**Test Query 1: get_active_jobs()**
```sql
EXPLAIN QUERY PLAN
SELECT * FROM jobs
WHERE status IN ('pending', 'running', 'cancelling');
```

**Expected Output (with index):**
```
SCAN jobs USING INDEX idx_jobs_status
```

**Test Query 2: get_recent_jobs()**
```sql
EXPLAIN QUERY PLAN
SELECT * FROM jobs
ORDER BY created_at DESC
LIMIT 10;
```

**Expected Output (with index):**
```
SCAN jobs USING INDEX idx_jobs_created_at
```

**Test Query 3: get_job_files()**
```sql
EXPLAIN QUERY PLAN
SELECT * FROM files
WHERE job_id = 'some-job-id'
ORDER BY created_at ASC;
```

**Expected Output (with index):**
```
SEARCH files USING INDEX idx_files_job_id (job_id=?)
```

**Test Query 4: get_orphaned_files()**
```sql
EXPLAIN QUERY PLAN
SELECT f.* FROM files f
LEFT JOIN jobs j ON f.job_id = j.id
WHERE j.id IS NULL;
```

**Expected Output (with index):**
```
SEARCH files USING INDEX idx_files_job_id
```

### Performance Benchmarking

**Benchmark Script:**
```python
import time
from src.collector.repositories.job_repository import JobRepository
from src.collector.repositories.file_repository import FileRepository

def benchmark_query(query_func, iterations=100):
    """Benchmark a database query.

    Args:
        query_func: Function that executes the query.
        iterations: Number of times to run the query.

    Returns:
        Average execution time in milliseconds.
    """
    start_time = time.time()

    for _ in range(iterations):
        query_func()

    end_time = time.time()
    total_time = end_time - start_time
    avg_time_ms = (total_time / iterations) * 1000

    return avg_time_ms

# Benchmark jobs queries
job_repo = JobRepository()

print("=== Job Query Benchmarks ===")
print(f"get_active_jobs(): {benchmark_query(job_repo.get_active_jobs):.2f}ms avg")
print(f"get_recent_jobs(10): {benchmark_query(lambda: job_repo.get_recent_jobs(10)):.2f}ms avg")
print(f"get_job_statistics(): {benchmark_query(job_repo.get_job_statistics):.2f}ms avg")

# Benchmark files queries
file_repo = FileRepository()

print("\n=== File Query Benchmarks ===")
print(f"get_job_files(job_id): {benchmark_query(lambda: file_repo.get_job_files('test-id')):.2f}ms avg")
print(f"get_orphaned_files(): {benchmark_query(file_repo.get_orphaned_files):.2f}ms avg")
```

### Test Verification

**Add test to verify indexes exist:**

**File**: `tests/integration/test_database_indexes.py`

```python
import pytest
import sqlite3
from src.collector.models.job import Job
from src.collector.models.file import File
from src.collector.config.database import get_db_config


def test_jobs_indexes_exist(app):
    """Test that all job indexes are created."""
    db_config = get_db_config()

    with db_config.get_connection() as conn:
        # Get indexes for jobs table
        indexes = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND tbl_name='jobs' AND name LIKE 'idx_%'"
        ).fetchall()

        index_names = {row[0] for row in indexes}

        # Verify expected indexes exist
        expected_indexes = {
            'idx_jobs_status',
            'idx_jobs_platform',
            'idx_jobs_created_at',
            'idx_jobs_status_created'
        }

        assert expected_indexes.issubset(index_names), \
            f"Missing indexes: {expected_indexes - index_names}"


def test_files_indexes_exist(app):
    """Test that all file indexes are created."""
    db_config = get_db_config()

    with db_config.get_connection() as conn:
        # Get indexes for files table
        indexes = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND tbl_name='files' AND name LIKE 'idx_%'"
        ).fetchall()

        index_names = {row[0] for row in indexes}

        # Verify expected indexes exist
        expected_indexes = {
            'idx_files_job_id',
            'idx_files_file_type',
            'idx_files_created_at',
            'idx_files_job_id_type'
        }

        assert expected_indexes.issubset(index_names), \
            f"Missing indexes: {expected_indexes - index_names}"


def test_index_usage_on_active_jobs(app):
    """Test that get_active_jobs uses the status index."""
    db_config = get_db_config()

    # Create some test jobs
    from src.collector.repositories.job_repository import JobRepository
    job_repo = JobRepository()

    job_repo.create_job("https://example.com/1", "youtube")
    job_repo.create_job("https://example.com/2", "instagram")
    job_repo.create_job("https://example.com/3", "youtube")

    # Check query plan
    with db_config.get_connection() as conn:
        plan = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT * FROM jobs WHERE status IN ('pending', 'running', 'cancelling')"
        ).fetchall()

        # Verify index is used
        plan_str = str(plan)
        assert 'idx_jobs_status' in plan_str or 'INDEX' in plan_str, \
            "Query should use idx_jobs_status index"


def test_index_usage_on_job_files(app):
    """Test that get_job_files uses the job_id index."""
    db_config = get_db_config()

    # Create test job and files
    from src.collector.repositories.job_repository import JobRepository
    from src.collector.repositories.file_repository import FileRepository

    job_repo = JobRepository()
    file_repo = FileRepository()

    job = job_repo.create_job("https://example.com", "youtube")
    file_repo.create_file(job.id, "/path/to/video.mp4", "video", 1024000)

    # Check query plan
    with db_config.get_connection() as conn:
        plan = conn.execute(
            f"EXPLAIN QUERY PLAN "
            f"SELECT * FROM files WHERE job_id = '{job.id}'"
        ).fetchall()

        # Verify index is used
        plan_str = str(plan)
        assert 'idx_files_job_id' in plan_str or 'INDEX' in plan_str, \
            "Query should use idx_files_job_id index"
```

## 8. Code Examples

### BaseModel Changes

**File**: `src/collector/models/base.py`

**Complete Changes:**

```python
"""
Base model class for database entities.

This module provides a base model class with common functionality for all database entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, TypeVar
from uuid import uuid4
import re

T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """Base model class with common functionality for all database entities.

    This class provides common fields and methods that are shared across all
    database entities, including id, timestamps, and basic serialization.
    """

    # Table name for the model (to be overridden by subclasses)
    table_name: ClassVar[str] = ""

    # Primary key field name
    primary_key: ClassVar[str] = "id"

    # Index definitions (to be overridden by subclasses)
    indexes: ClassVar[list[dict[str, Any]]] = []

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        self.id: str = kwargs.get("id", str(uuid4()))
        self.created_at: datetime = kwargs.get("created_at", datetime.utcnow())
        self.updated_at: datetime = kwargs.get("updated_at", datetime.utcnow())

        # Set any additional attributes passed in kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and not callable(getattr(self, key)):
                setattr(self, key, value)

    # ... [existing methods: to_dict, from_dict, update_timestamp, __repr__, __eq__, __hash__] ...

    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model.

        Returns:
            Table name for the model.
        """
        return cls.table_name or cls.__name__.lower() + "s"

    @classmethod
    def get_create_table_sql(cls) -> str:
        """Get SQL statement to create the table for this model.

        Returns:
            SQL CREATE TABLE statement.
        """
        table_name = cls.get_table_name()
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {cls.primary_key} TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """

    @classmethod
    def get_indexes_sql(cls) -> list[str]:
        """Get SQL statements to create indexes for this model.

        Returns:
            List of CREATE INDEX SQL statements.
        """
        table_name = cls.get_table_name()
        index_statements = []

        for index_def in cls.indexeses:
            columns = index_def["columns"]
            unique = index_def.get("unique", False)
            index_name = index_def.get("name", cls._generate_index_name(columns))

            # Build column list with optional DESC
            column_defs = []
            for col in columns:
                if isinstance(col, tuple):
                    # (column_name, direction)
                    column_defs.append(f"{col[0]} {col[1]}")
                else:
                    column_defs.append(str(col))

            columns_str = ", ".join(column_defs)
            unique_str = "UNIQUE " if unique else ""

            sql = f"CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})"
            index_statements.append(sql)

        return index_statements

    @classmethod
    def _generate_index_name(cls, columns: list[Any]) -> str:
        """Generate a consistent index name from columns.

        Args:
            columns: List of column definitions.

        Returns:
            Generated index name.
        """
        table_name = cls.get_table_name()
        col_names = []

        for col in columns:
            if isinstance(col, tuple):
                col_names.append(col[0])
            else:
                col_names.append(str(col))

        cols_str = "_".join(col_names)
        return f"idx_{table_name}_{cols_str}"

    # ... [rest of existing methods: get_insert_sql, get_update_sql, get_select_by_id_sql, get_delete_by_id_sql] ...
```

### Job Model with Indexes

**File**: `src/collector/models/job.py`

**Changes:**

```python
"""
Job model for database entities.

This module provides the Job model class for managing job records in the database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from .base import BaseModel


class Job(BaseModel):
    """Job model representing a download job.

    This model represents a job in the system, including its status, progress,
    and metadata about the download operation.
    """

    # Table name for this model
    table_name = "jobs"

    # Index definitions for performance
    indexes: ClassVar[list[dict[str, Any]]] = [
        {
            "columns": ["status"],
            "unique": False,
            "name": "idx_jobs_status"
        },
        {
            "columns": ["platform"],
            "unique": False,
            "name": "idx_jobs_platform"
        },
        {
            "columns": [("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_created_at"
        },
        {
            "columns": ["status", ("created_at", "DESC")],
            "unique": False,
            "name": "idx_jobs_status_created"
        }
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Job model with provided attributes.

        Args:
            **kwargs: Field values to set on the model instance.
        """
        super().__init__(**kwargs)

        # Job-specific fields
        self.url: str = kwargs.get("url", "")
        self.platform: str = kwargs.get("platform", "")
        self.status: str = kwargs.get("status", "pending")
        self.title: str | None = kwargs.get("title")
        self.progress: int = kwargs.get("progress", 0)
        self.current_operation: str | None = kwargs.get("current_operation")
        self.error_message: str | None = kwargs.get("error_message")
        self.retry_count: int = kwargs.get("retry_count", 0)
        self.bytes_downloaded: int = kwargs.get("bytes_downloaded", 0)
        self.completed_at: datetime | None = kwargs.get("completed_at")

    # ... [rest of existing methods unchanged] ...
```

### Index Creation in Database.py

**File**: `src/collector/config/database.py`

**Complete Changes:**

```python
"""
Database configuration for the Python Content Scraper.

This module provides database configuration and connection management.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
import re

from flask import current_app, g

from .settings import Config


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize database configuration.

        Args:
            db_path: Path to the SQLite database file. If None, uses Config.SCRAPER_DB_PATH.
        """
        self.db_path = db_path or Config.SCRAPER_DB_PATH
        self._ensure_db_directory()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        if self.db_path.parent:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection.

        Yields:
            SQLite database connection with row factory set to dict.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ... [existing methods: execute_query, execute_update, execute_many] ...

    def create_indexes(self, model_classes: list[type]) -> None:
        """Create indexes for the given model classes.

        Args:
            model_classes: List of model classes to create indexes for.
        """
        print("Creating database indexes...")

        with self.get_connection() as conn:
            for model_class in model_classes:
                table_name = model_class.get_table_name()
                index_sqls = model_class.get_indexes_sql()

                if not index_sqls:
                    continue

                print(f"\n{table_name}:")
                for index_sql in index_sqls:
                    try:
                        # Extract index name for logging
                        match = re.search(
                            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)',
                            index_sql,
                            re.IGNORECASE
                        )
                        index_name = match.group(1) if match else "unknown"

                        conn.execute(index_sql)
                        print(f"  ✓ Created: {index_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  ✗ Error: {e}")

            conn.commit()
            print("\nIndex creation complete!")

    def ensure_indexes(self, model_classes: list[type]) -> None:
        """Ensure all indexes exist for the given models.

        This method checks for existing indexes and creates any missing ones.

        Args:
            model_classes: List of model classes to check/create indexes for.
        """
        print("Ensuring database indexes exist...")

        with self.get_connection() as conn:
            for model_class in model_classes:
                table_name = model_class.get_table_name()

                # Get existing indexes for this table
                existing_indexes = conn.execute(
                    f"SELECT name FROM sqlite_master "
                    f"WHERE type='index' AND tbl_name='{table_name}' AND name LIKE 'idx_%'"
                ).fetchall()

                existing_index_names = {row[0] for row in existing_indexes}

                # Get required indexes
                index_sqls = model_class.get_indexes_sql()

                if not index_sqls:
                    continue

                print(f"\n{table_name}:")

                for index_sql in index_sqls:
                    # Extract index name
                    match = re.search(
                        r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+(\w+)',
                        index_sql,
                        re.IGNORECASE
                    )

                    if match:
                        index_name = match.group(1)

                        if index_name not in existing_index_names:
                            try:
                                conn.execute(index_sql)
                                print(f"  ✓ Created: {index_name}")
                            except sqlite3.OperationalError as e:
                                print(f"  ✗ Error creating {index_name}: {e}")
                        else:
                            print(f"  ✓ Exists: {index_name}")

            conn.commit()
            print("\nIndex verification complete!")

    def initialize_schema(self, model_classes: list[type]) -> None:
        """Initialize database schema including tables and indexes.

        Args:
            model_classes: List of model classes to initialize.
        """
        print("Initializing database schema...")

        # Create tables first
        for model_class in model_classes:
            table_name = model_class.get_table_name()
            create_sql = model_class.get_create_table_sql()

            with self.get_connection() as conn:
                conn.execute(create_sql)
                conn.commit()
                print(f"  ✓ Table: {table_name}")

        # Then ensure indexes exist
        self.ensure_indexes(model_classes)

        print("Schema initialization complete!")

    def get_index_info(self, table_name: str) -> list[dict[str, Any]]:
        """Get information about indexes for a table.

        Args:
            table_name: Name of the table to get index info for.

        Returns:
            List of dictionaries containing index information.
        """
        with self.get_connection() as conn:
            indexes = conn.execute(
                f"SELECT name, sql FROM sqlite_master "
                f"WHERE type='index' AND tbl_name='{table_name}' AND name LIKE 'idx_%' "
                f"ORDER BY name"
            ).fetchall()

            return [{"name": row[0], "sql": row[1]} for row in indexes]

    # ... [existing methods: get_db_config, get_db, close_db] ...
```

## 9. Performance Testing

### Test Dataset Creation

**Script**: `scripts/create_test_dataset.py`

```python
"""Create test dataset for performance testing."""

import random
from datetime import datetime, timedelta
from src.collector.repositories.job_repository import JobRepository
from src.collector.repositories.file_repository import FileRepository

def create_test_dataset(num_jobs: int = 1000, files_per_job: int = 3) -> None:
    """Create a test dataset with specified number of jobs and files.

    Args:
        num_jobs: Number of jobs to create.
        files_per_job: Average number of files per job.
    """
    job_repo = JobRepository()
    file_repo = FileRepository()

    platforms = ["youtube", "instagram", "tiktok"]
    statuses = ["pending", "running", "completed", "failed", "cancelled"]
    file_types = ["video", "audio", "image", "metadata"]

    print(f"Creating {num_jobs} jobs...")

    for i in range(num_jobs):
        # Create job
        platform = random.choice(platforms)
        status = random.choice(statuses)

        job = job_repo.create_job(
            url=f"https://{platform}.com/video/{i}",
            platform=platform,
            title=f"Test Video {i}"
        )

        # Update status randomly
        if status in ["completed", "failed", "cancelled"]:
            if status == "completed":
                job_repo.complete_job(job.id)
            elif status == "failed":
                job_repo.fail_job(job.id, "Test error")
            else:
                job_repo.update_job_status(job.id, status)

        # Create files
        num_files = random.randint(1, files_per_job + 1)
        for j in range(num_files):
            file_type = random.choice(file_types)
            file_repo.create_file(
                job_id=job.id,
                file_path=f"/downloads/{job.id}/{j}.{file_type}",
                file_type=file_type,
                file_size=random.randint(100000, 10000000)
            )

        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} jobs...")

    print(f"\nDataset creation complete!")
    print(f"  Jobs: {job_repo.count()}")
    print(f"  Files: {file_repo.count()}")
```

### Benchmarking Script

**Script**: `scripts/benchmark_indexes.py`

```python
"""Benchmark database queries before and after indexes."""

import time
from typing import Callable
from src.collector.repositories.job_repository import JobRepository
from src.collector.repositories.file_repository import FileRepository


def benchmark_query(name: str, query_func: Callable, iterations: int = 100) -> float:
    """Benchmark a database query.

    Args:
        name: Name of the query for display.
        query_func: Function that executes the query.
        iterations: Number of times to run the query.

    Returns:
        Average execution time in milliseconds.
    """
    # Warm-up
    query_func()

    # Benchmark
    start_time = time.perf_counter()

    for _ in range(iterations):
        query_func()

    end_time = time.perf_counter()
    total_time = end_time - start_time
    avg_time_ms = (total_time / iterations) * 1000

    print(f"{name:40s}: {avg_time_ms:6.2f}ms avg ({iterations} iterations)")

    return avg_time_ms


def run_benchmarks() -> dict[str, float]:
    """Run all benchmarks and return results.

    Returns:
        Dictionary mapping query names to average execution times.
    """
    job_repo = JobRepository()
    file_repo = FileRepository()

    results = {}

    print("=" * 70)
    print("DATABASE QUERY BENCHMARKS")
    print("=" * 70)

    print("\nJob Queries:")
    print("-" * 70)

    results['get_active_jobs'] = benchmark_query(
        "get_active_jobs()",
        job_repo.get_active_jobs,
        iterations=50
    )

    results['get_recent_jobs'] = benchmark_query(
        "get_recent_jobs(10)",
        lambda: job_repo.get_recent_jobs(10),
        iterations=50
    )

    results['get_job_statistics'] = benchmark_query(
        "get_job_statistics()",
        job_repo.get_job_statistics,
        iterations=50
    )

    results['find_by_status'] = benchmark_query(
        "find_by(status='completed')",
        lambda: job_repo.find_by(status='completed'),
        iterations=50
    )

    results['find_by_platform'] = benchmark_query(
        "find_by(platform='youtube')",
        lambda: job_repo.find_by(platform='youtube'),
        iterations=50
    )

    print("\nFile Queries:")
    print("-" * 70)

    # Get a job ID for file queries
    jobs = job_repo.find_by(status='completed', limit=1)
    job_id = jobs[0].id if jobs else None

    if job_id:
        results['get_job_files'] = benchmark_query(
            "get_job_files(job_id)",
            lambda: file_repo.get_job_files(job_id),
            iterations=100
        )

    results['get_files_by_type'] = benchmark_query(
        "get_files_by_type('video')",
        lambda: file_repo.get_files_by_type('video'),
        iterations=50
    )

    results['get_orphaned_files'] = benchmark_query(
        "get_orphaned_files()",
        file_repo.get_orphaned_files,
        iterations=10
    )

    print("\n" + "=" * 70)

    return results


if __name__ == "__main__":
    results = run_benchmarks()

    print("\nSUMMARY:")
    print("-" * 70)
    for name, time_ms in results.items():
        print(f"  {name:30s}: {time_ms:6.2f}ms")
    print("-" * 70)
```

### Performance Comparison

**Expected Improvements:**

| Query | Without Index (1000 jobs) | With Index (1000 jobs) | Improvement |
|-------|--------------------------|------------------------|-------------|
| `get_active_jobs()` | ~15ms | ~2ms | 7.5x faster |
| `get_recent_jobs()` | ~20ms | ~1ms | 20x faster |
| `get_job_statistics()` | ~25ms | ~3ms | 8.3x faster |
| `find_by(status)` | ~12ms | ~1ms | 12x faster |
| `get_job_files()` | ~5ms | ~0.5ms | 10x faster |
| `get_orphaned_files()` | ~50ms | ~5ms | 10x faster |

**Note**: Actual performance will vary based on hardware, dataset size, and SQLite configuration.

## 10. Summary

### Implementation Checklist

- [ ] Add `indexes` class variable to `BaseModel`
- [ ] Add `get_indexes_sql()` method to `BaseModel`
- [ ] Add `_generate_index_name()` helper to `BaseModel`
- [ ] Define indexes in `Job` model
- [ ] Define indexes in `File` model
- [ ] Add empty indexes list to `Settings` model
- [ ] Add `create_indexes()` method to `DatabaseConfig`
- [ ] Add `ensure_indexes()` method to `DatabaseConfig`
- [ ] Add `initialize_schema()` method to `DatabaseConfig`
- [ ] Update application initialization to create indexes
- [ ] Add migration logic for existing databases
- [ ] Add tests to verify indexes exist
- [ ] Add tests to verify index usage
- [ ] Run benchmarks to measure performance improvement
- [ ] Update documentation

### Risk Assessment

**Low Risk:**
- Using `IF NOT EXISTS` prevents errors
- Indexes don't affect application logic
- Can be dropped if issues occur
- No data modification

**Medium Risk:**
- Slight storage overhead (~10-20%)
- Slight write performance impact (~5%)
- Need to test with production data volumes

**Mitigation:**
- Comprehensive testing
- Gradual rollout
- Monitoring and metrics
- Rollback plan documented

### Success Criteria

1. All indexes created successfully on new installations
2. Existing databases updated with indexes
3. Query performance improved by 5x+ on common queries
4. No regressions in application functionality
5. Tests pass with 100% coverage of index-related code
6. Documentation updated with index information

### Next Steps

1. Implement the changes following this plan
2. Run comprehensive tests
3. Benchmark with realistic data volumes
4. Monitor in staging environment
5. Deploy to production with monitoring
6. Document actual performance improvements

---

**Plan Version:** 1.0
**Last Updated:** 2025-02-17
**Author:** Implementation Plan
**Status:** Ready for Implementation
