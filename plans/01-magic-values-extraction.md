# Implementation Plan: Magic Values Extraction

## 1. Overview

This plan addresses the extraction of hardcoded numeric literals (magic values) from the configuration validation logic in `src/collector/config/settings.py`. Magic values are hardcoded numbers that appear in validation logic without named constants, making the codebase harder to maintain and more prone to bugs.

### Why This Matters

- **Maintainability**: Changing validation limits requires searching through code for numeric literals
- **Prevents Bugs**: Magic values can be accidentally changed in one place but not another
- **Code Clarity**: Named constants self-document the intent of validation rules
- **Consistency**: Ensures validation limits are applied uniformly across the codebase

## 2. Current Issues

### Identified Magic Values

| Line | Value(s) | Context | Purpose |
|------|----------|---------|---------|
| 70 | `1` and `10` | `SCRAPER_MAX_CONCURRENT` validation | Minimum and maximum allowed concurrent jobs |
| 79 | `100` | `SCRAPER_DISK_WARN_MB` validation | Minimum disk warning threshold in MB |
| 26 | `1024` | `SCRAPER_DISK_WARN_MB` default value | Default disk warning threshold in MB |

### Detailed Analysis

**Lines 70-71: Concurrent Jobs Validation**
```python
if cls.SCRAPER_MAX_CONCURRENT < 1 or cls.SCRAPER_MAX_CONCURRENT > 10:
    errors.append("SCRAPER_MAX_CONCURRENT must be between 1 and 10")
```
- The values `1` and `10` represent the valid range for concurrent scraping jobs
- These limits prevent resource exhaustion
- Currently hardcoded in both the validation logic AND the error message

**Line 79-80: Disk Space Warning Validation**
```python
if cls.SCRAPER_DISK_WARN_MB < 100:
    errors.append("SCRAPER_DISK_WARN_MB should be at least 100 MB")
```
- The value `100` represents the minimum safe disk warning threshold
- Prevents warnings from being set too low to be useful
- Hardcoded in both validation and error message

**Line 26: Default Disk Warning Value**
```python
SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", "1024"))
```
- The value `1024` is the default disk warning threshold (1 GB)
- While this is a default value parameter, it should still be a named constant for consistency

## 3. Proposed Constants

### Constants to Add to Config Class

```python
class Config:
    """Centralized configuration with environment variable support."""

    # Validation Constants
    MIN_CONCURRENT_JOBS: int = 1
    MAX_CONCURRENT_JOBS: int = 10
    MIN_DISK_WARNING_MB: int = 100
    DEFAULT_DISK_WARNING_MB: int = 1024
```

### Constant Specifications

| Constant Name | Type | Value | Description |
|--------------|------|-------|-------------|
| `MIN_CONCURRENT_JOBS` | `int` | `1` | Minimum number of concurrent scraping jobs allowed |
| `MAX_CONCURRENT_JOBS` | `int` | `10` | Maximum number of concurrent scraping jobs allowed (prevents resource exhaustion) |
| `MIN_DISK_WARNING_MB` | `int` | `100` | Minimum disk space warning threshold in megabytes (prevents setting warnings too low) |
| `DEFAULT_DISK_WARNING_MB` | `int` | `1024` | Default disk space warning threshold in megabytes (1 GB) |

### Naming Convention

- Use `UPPER_SNAKE_CASE` for constants (Python convention)
- Prefix with descriptive qualifier: `MIN_`, `MAX_`, `DEFAULT_`
- Include units where applicable: `_MB` for megabyte values
- Names should be self-documenting and clear

## 4. Implementation Steps

### Step 1: Add Constant Definitions
**Location**: After the docstring in the `Config` class (after line 12)

```python
class Config:
    """Centralized configuration with environment variable support."""

    # Validation Constants
    MIN_CONCURRENT_JOBS: int = 1
    MAX_CONCURRENT_JOBS: int = 10
    MIN_DISK_WARNING_MB: int = 100
    DEFAULT_DISK_WARNING_MB: int = 1024

    # Paths
    SCRAPER_DOWNLOAD_DIR: Path = Path(os.environ.get("SCRAPER_DOWNLOAD_DIR", "./downloads"))
    ...
```

**Rationale**: Placing constants at the top of the class makes them easily discoverable and establishes them as fundamental configuration constraints.

### Step 2: Replace Default Value Reference
**Location**: Line 26

**Before**:
```python
SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", "1024"))
```

**After**:
```python
SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", str(DEFAULT_DISK_WARNING_MB)))
```

**Note**: Need to convert `DEFAULT_DISK_WARNING_MB` to string since `os.environ.get()` expects string values.

### Step 3: Replace Validation Logic - Concurrent Jobs
**Location**: Lines 70-71

**Before**:
```python
if cls.SCRAPER_MAX_CONCURRENT < 1 or cls.SCRAPER_MAX_CONCURRENT > 10:
    errors.append("SCRAPER_MAX_CONCURRENT must be between 1 and 10")
```

**After**:
```python
if cls.SCRAPER_MAX_CONCURRENT < cls.MIN_CONCURRENT_JOBS or cls.SCRAPER_MAX_CONCURRENT > cls.MAX_CONCURRENT_JOBS:
    errors.append(f"SCRAPER_MAX_CONCURRENT must be between {cls.MIN_CONCURRENT_JOBS} and {cls.MAX_CONCURRENT_JOBS}")
```

**Benefits**:
- Uses named constants instead of magic numbers
- Error message automatically reflects constant values
- Single source of truth for validation limits

### Step 4: Replace Validation Logic - Disk Warning
**Location**: Lines 79-80

**Before**:
```python
if cls.SCRAPER_DISK_WARN_MB < 100:
    errors.append("SCRAPER_DISK_WARN_MB should be at least 100 MB")
```

**After**:
```python
if cls.SCRAPER_DISK_WARN_MB < cls.MIN_DISK_WARNING_MB:
    errors.append(f"SCRAPER_DISK_WARN_MB should be at least {cls.MIN_DISK_WARNING_MB} MB")
```

**Benefits**:
- Named constant makes intent clear
- Error message automatically reflects the minimum value
- Easy to adjust minimum threshold in one place

### Step 5: Update Docstrings
**Location**: Review and update any docstrings that reference these values

Search for:
- Docstrings mentioning "1 and 10" for concurrent jobs
- Docstrings mentioning "100 MB" for disk warnings
- Docstrings mentioning "1024 MB" or "1 GB" for defaults

Update to reference constant names instead of hardcoded values.

### Step 6: Verify Type Hints
Ensure all new constants have proper type hints:
- All constants should be typed as `int`
- Consistent with existing code style

## 5. Testing Strategy

### Unit Tests to Create/Update

**Test 1: Verify Constants Exist and Have Correct Values**
```python
def test_config_validation_constants():
    """Test that validation constants are defined correctly."""
    assert Config.MIN_CONCURRENT_JOBS == 1
    assert Config.MAX_CONCURRENT_JOBS == 10
    assert Config.MIN_DISK_WARNING_MB == 100
    assert Config.DEFAULT_DISK_WARNING_MB == 1024
```

**Test 2: Validation Uses Constants**
```python
def test_concurrent_jobs_validation_uses_constants():
    """Test that validation respects MIN/MAX_CONCURRENT_JOBS constants."""
    # Test below minimum
    with mock.patch.object(Config, 'SCRAPER_MAX_CONCURRENT', Config.MIN_CONCURRENT_JOBS - 1):
        errors = Config.validate()
        assert any("must be between" in e for e in errors)

    # Test at minimum (should pass)
    with mock.patch.object(Config, 'SCRAPER_MAX_CONCURRENT', Config.MIN_CONCURRENT_JOBS):
        errors = Config.validate()
        assert not any("SCRAPER_MAX_CONCURRENT" in e for e in errors)

    # Test at maximum (should pass)
    with mock.patch.object(Config, 'SCRAPER_MAX_CONCURRENT', Config.MAX_CONCURRENT_JOBS):
        errors = Config.validate()
        assert not any("SCRAPER_MAX_CONCURRENT" in e for e in errors)

    # Test above maximum
    with mock.patch.object(Config, 'SCRAPER_MAX_CONCURRENT', Config.MAX_CONCURRENT_JOBS + 1):
        errors = Config.validate()
        assert any("must be between" in e for e in errors)
```

**Test 3: Disk Warning Validation Uses Constants**
```python
def test_disk_warning_validation_uses_constants():
    """Test that validation respects MIN_DISK_WARNING_MB constant."""
    # Test below minimum
    with mock.patch.object(Config, 'SCRAPER_DISK_WARN_MB', Config.MIN_DISK_WARNING_MB - 1):
        errors = Config.validate()
        assert any("should be at least" in e for e in errors)

    # Test at minimum (should pass)
    with mock.patch.object(Config, 'SCRAPER_DISK_WARN_MB', Config.MIN_DISK_WARNING_MB):
        errors = Config.validate()
        assert not any("SCRAPER_DISK_WARN_MB" in e for e in errors)
```

**Test 4: Default Value Uses Constant**
```python
def test_default_disk_warning_uses_constant():
    """Test that default disk warning value uses DEFAULT_DISK_WARNING_MB."""
    # Reset environment variable
    os.environ.pop('SCRAPER_DISK_WARN_MB', None)

    # Reload Config to pick up default
    import importlib
    import collector.config.settings
    importlib.reload(collector.config.settings)

    from collector.config.settings import Config
    assert Config.SCRAPER_DISK_WARN_MB == Config.DEFAULT_DISK_WARNING_MB
```

### Manual Testing Steps

1. **Configuration Validation Test**
   - Set `SCRAPER_MAX_CONCURRENT=0` → Should fail validation
   - Set `SCRAPER_MAX_CONCURRENT=11` → Should fail validation
   - Set `SCRAPER_MAX_CONCURRENT=1` → Should pass validation
   - Set `SCRAPER_MAX_CONCURRENT=10` → Should pass validation
   - Set `SCRAPER_DISK_WARN_MB=99` → Should fail validation
   - Set `SCRAPER_DISK_WARN_MB=100` → Should pass validation

2. **Error Message Verification**
   - Trigger validation errors
   - Verify error messages contain the constant values
   - Ensure messages are clear and accurate

3. **Integration Testing**
   - Run existing test suite: `pytest tests/`
   - Ensure no regressions in configuration validation
   - Verify application starts successfully with valid config

### Test Execution Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file for config
pytest tests/unit/test_config.py -v

# Run with coverage
pytest tests/ --cov=src/collector/config --cov-report=html
```

## 6. Code Examples

### Example 1: Complete Config Class with Constants

**Before**:
```python
class Config:
    """Centralized configuration with environment variable support."""

    # Paths
    SCRAPER_DOWNLOAD_DIR: Path = Path(os.environ.get("SCRAPER_DOWNLOAD_DIR", "./downloads"))
    SCRAPER_DB_PATH: Path = Path(os.environ.get("SCRAPER_DB_PATH", "./instance/scraper.db"))

    # Concurrency
    SCRAPER_MAX_CONCURRENT: int = int(os.environ.get("SCRAPER_MAX_CONCURRENT", "2"))

    # Instagram rate limiting
    SCRAPER_IG_DELAY_MIN: float = float(os.environ.get("SCRAPER_IG_DELAY_MIN", "5.0"))
    SCRAPER_IG_DELAY_MAX: float = float(os.environ.get("SCRAPER_IG_DELAY_MAX", "10.0"))

    # Disk space warnings (in MB)
    SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", "1024"))
```

**After**:
```python
class Config:
    """Centralized configuration with environment variable support."""

    # Validation Constants
    MIN_CONCURRENT_JOBS: int = 1
    MAX_CONCURRENT_JOBS: int = 10
    MIN_DISK_WARNING_MB: int = 100
    DEFAULT_DISK_WARNING_MB: int = 1024

    # Paths
    SCRAPER_DOWNLOAD_DIR: Path = Path(os.environ.get("SCRAPER_DOWNLOAD_DIR", "./downloads"))
    SCRAPER_DB_PATH: Path = Path(os.environ.get("SCRAPER_DB_PATH", "./instance/scraper.db"))

    # Concurrency
    SCRAPER_MAX_CONCURRENT: int = int(os.environ.get("SCRAPER_MAX_CONCURRENT", "2"))

    # Instagram rate limiting
    SCRAPER_IG_DELAY_MIN: float = float(os.environ.get("SCRAPER_IG_DELAY_MIN", "5.0"))
    SCRAPER_IG_DELAY_MAX: float = float(os.environ.get("SCRAPER_IG_DELAY_MAX", "10.0"))

    # Disk space warnings (in MB)
    SCRAPER_DISK_WARN_MB: int = int(os.environ.get("SCRAPER_DISK_WARN_MB", str(DEFAULT_DISK_WARNING_MB)))
```

### Example 2: Validation Method Transformation

**Before**:
```python
@classmethod
def validate(cls) -> list[str]:
    """Validate configuration and return list of errors.

    Returns empty list if configuration is valid.
    """
    errors: list[str] = []

    # Validate numeric ranges
    if cls.SCRAPER_MAX_CONCURRENT < 1 or cls.SCRAPER_MAX_CONCURRENT > 10:
        errors.append("SCRAPER_MAX_CONCURRENT must be between 1 and 10")

    if cls.SCRAPER_IG_DELAY_MIN < 0:
        errors.append("SCRAPER_IG_DELAY_MIN must be non-negative")

    if cls.SCRAPER_IG_DELAY_MAX <= cls.SCRAPER_IG_DELAY_MIN:
        errors.append("SCRAPER_IG_DELAY_MAX must be greater than SCRAPER_IG_DELAY_MIN")

    if cls.SCRAPER_DISK_WARN_MB < 100:
        errors.append("SCRAPER_DISK_WARN_MB should be at least 100 MB")

    return errors
```

**After**:
```python
@classmethod
def validate(cls) -> list[str]:
    """Validate configuration and return list of errors.

    Returns empty list if configuration is valid.
    """
    errors: list[str] = []

    # Validate numeric ranges
    if cls.SCRAPER_MAX_CONCURRENT < cls.MIN_CONCURRENT_JOBS or cls.SCRAPER_MAX_CONCURRENT > cls.MAX_CONCURRENT_JOBS:
        errors.append(f"SCRAPER_MAX_CONCURRENT must be between {cls.MIN_CONCURRENT_JOBS} and {cls.MAX_CONCURRENT_JOBS}")

    if cls.SCRAPER_IG_DELAY_MIN < 0:
        errors.append("SCRAPER_IG_DELAY_MIN must be non-negative")

    if cls.SCRAPER_IG_DELAY_MAX <= cls.SCRAPER_IG_DELAY_MIN:
        errors.append("SCRAPER_IG_DELAY_MAX must be greater than SCRAPER_IG_DELAY_MIN")

    if cls.SCRAPER_DISK_WARN_MB < cls.MIN_DISK_WARNING_MB:
        errors.append(f"SCRAPER_DISK_WARN_MB should be at least {cls.MIN_DISK_WARNING_MB} MB")

    return errors
```

### Example 3: Error Message Dynamic Values

**Demonstration of how error messages now automatically reflect constant values:**

```python
# If constants are changed to:
MIN_CONCURRENT_JOBS: int = 2
MAX_CONCURRENT_JOBS: int = 20

# Error message automatically becomes:
# "SCRAPER_MAX_CONCURRENT must be between 2 and 20"
```

This eliminates the need to update error messages when constants change!

## 7. Benefits Summary

### Code Quality Improvements

1. **Single Source of Truth**: Validation limits defined in one place
2. **Self-Documenting Code**: Constant names explain the purpose of each value
3. **Maintainability**: Changing limits requires updating only the constant definition
4. **Consistency**: Error messages automatically reflect current validation rules
5. **Testability**: Easy to test validation logic by mocking constants
6. **Type Safety**: Type hints make constants' types explicit

### Bug Prevention

1. **Prevents Drift**: Error messages stay in sync with validation logic
2. **Prevents Typos**: No risk of typing "10" in one place and "11" in another
3. **Easy Code Review**: Changes to validation limits are obvious and localized
4. **Refactoring Safety**: IDE can find all usages of a constant

### Developer Experience

1. **IntelliSense Support**: IDEs can suggest constant names
2. **Clear Intent**: `MIN_CONCURRENT_JOBS` is clearer than `1`
3. **Easy Discovery**: All validation limits grouped at top of class
4. **Documentation**: Constants serve as inline documentation

## 8. Additional Considerations

### Future Enhancements

1. **Consider Making Constants Configurable**: If these limits need to vary by environment, they could become environment variables themselves
2. **Add Validation Tests**: Ensure constants themselves are valid (e.g., MIN < MAX)
3. **Document Rationale**: Add comments explaining why these specific limits were chosen
4. **Related Constants**: Look for other magic values in the codebase that could benefit from similar extraction

### Potential Extension: Runtime Constants

If these values need to be adjustable at runtime without code changes:

```python
class Config:
    # These could become environment variables
    MIN_CONCURRENT_JOBS: int = int(os.environ.get("SCRAPER_MIN_CONCURRENT_JOBS", "1"))
    MAX_CONCURRENT_JOBS: int = int(os.environ.get("SCRAPER_MAX_CONCURRENT_JOBS", "10"))
    MIN_DISK_WARNING_MB: int = int(os.environ.get("SCRAPER_MIN_DISK_WARNING_MB", "100"))
```

However, for the current scope, keeping them as class constants is appropriate.

## 9. Implementation Checklist

- [ ] Add constant definitions to Config class
- [ ] Update default value for `SCRAPER_DISK_WARN_MB` to use `DEFAULT_DISK_WARNING_MB`
- [ ] Update concurrent jobs validation to use `MIN_CONCURRENT_JOBS` and `MAX_CONCURRENT_JOBS`
- [ ] Update disk warning validation to use `MIN_DISK_WARNING_MB`
- [ ] Update error messages to use f-strings with constants
- [ ] Review and update docstrings
- [ ] Create/update unit tests for new constants
- [ ] Run existing test suite to ensure no regressions
- [ ] Verify error messages display correctly
- [ ] Manual testing with various configuration values

## 10. Success Criteria

The implementation will be considered successful when:

1. All magic values (1, 10, 100, 1024) are replaced with named constants
2. No hardcoded numeric literals remain in validation logic
3. All tests pass with new constants in place
4. Error messages correctly display constant values
5. Code review confirms no regressions
6. Documentation is updated to reflect the changes

---

**Document Version**: 1.0
**Created**: 2025-02-17
**Status**: Ready for Implementation
**Estimated Effort**: 1-2 hours
