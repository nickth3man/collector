# Variable Naming Improvement Plan

## 1. Overview

### Why Naming Matters
- **Code Readability**: Clear variable names make code self-documenting and easier to understand
- **Maintenance**: Well-named variables reduce cognitive load when debugging or modifying code
- **Onboarding**: New developers can grasp code intent faster with descriptive names
- **Code Review**: Better names reduce ambiguity in code reviews

### Scope
This plan focuses on renaming the **top 5 worst-named variables** identified in the scraper modules. These variables are overly generic, vague, or misleading, making code harder to understand at a glance.

**Target Files (EXCLUSIVE to this plan):**
- `src/collector/scrapers/instagram_scraper.py`
- `src/collector/scrapers/youtube_scraper.py`
- `src/collector/scrapers/base_scraper.py`

**Excluded from this plan (future consideration):**
- Other modules not in the scrapers directory
- Variables not in the top 5 priority list

---

## 2. Renaming Inventory

### Priority 1: `data` → `metadata_dict`

**Locations:**
- `src/collector/scrapers/youtube_scraper.py:380` - Function parameter
- `src/collector/scrapers/youtube_scraper.py:389` - Function variable

**What it represents:**
A dictionary containing extracted metadata from yt-dlp's info dict, cleaned and formatted for storage.

**Recommended new name:** `metadata_dict`

**Justification:**
- "data" is the most generic variable name possible
- The variable specifically holds metadata about a video
- "metadata_dict" clearly indicates both content (metadata) and type (dict)
- Aligns with other metadata variables in the codebase (e.g., `profile_metadata`, `post_metadata`)

**Current code context:**
```python
def _extract_metadata(self, info: dict) -> dict[str, Any]:
    """Extract relevant metadata from yt-dlp info dict.

    Args:
        info: Info dict from yt-dlp

    Returns:
        Cleaned metadata dictionary
    """
    metadata = {
        "platform": "youtube",
        "id": info.get("id"),
        ...
    }
```

**Scope:** Function-level (local to `_extract_metadata` method)

---

### Priority 2: `result` → `scrape_result`

**Locations:**
- `src/collector/scrapers/instagram_scraper.py:55` - `scrape()` method
- `src/collector/scrapers/instagram_scraper.py:198` - `_scrape_profile()` method
- `src/collector/scrapers/instagram_scraper.py:332` - `_scrape_post()` method
- `src/collector/scrapers/youtube_scraper.py:50` - `scrape()` method
- `src/collector/scrapers/youtube_scraper.py:99` - `_scrape_single_video()` method
- `src/collector/scrapers/youtube_scraper.py:244` - `_scrape_playlist()` method

**What it represents:**
A standardized dictionary containing the results of a scrape operation, including success status, files, metadata, title, and error information.

**Recommended new name:** `scrape_result`

**Justification:**
- "result" is overly generic - could be any type of result
- "scrape_result" clearly indicates this is the output of a scraping operation
- Prevents confusion with other result variables that might be added later
- Makes the code's purpose immediately clear when reading
- Consistent with the domain (scraping)

**Current code context:**
```python
def scrape(self, url: str, job_id: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": False,
        "title": None,
        "files": [],
        "metadata": {},
        "error": None,
    }
```

**Scope:** Function-level (local to each scrape method)

**Note:** Each method has its own `result` variable, so they can be renamed independently without conflicts.

---

### Priority 3: `files` → `downloaded_files`

**Locations:**
- `src/collector/scrapers/instagram_scraper.py:276` - Assignment from `_download_post_media()`
- `src/collector/scrapers/instagram_scraper.py:366` - Assignment from `_download_post_media()`
- `src/collector/scrapers/instagram_scraper.py:414` - Local variable in `_download_post_media()`

**What it represents:**
A list of dictionaries containing information about successfully downloaded media files (file_path, file_type, file_size).

**Recommended new name:** `downloaded_files`

**Justification:**
- "files" is ambiguous - could mean all files, filtered files, file paths, etc.
- "downloaded_files" clearly indicates these are files that were successfully downloaded
- Distinguishes from other file-related variables like `file_path`, `filepath`, `video_file`, etc.
- Makes the success condition implicit in the name

**Current code context:**
```python
def _download_post_media(...) -> list[dict[str, Any]]:
    """Download media files from a post.

    Returns:
        List of file info dicts
    """
    files = []
    ...
    files.append({
        "file_path": str(filepath.relative_to(self.download_dir)),
        "file_type": file_type,
        "file_size": filepath.stat().st_size,
    })
    return files
```

**Scope:** Function-level (local to `_download_post_media` and its callers)

---

### Priority 4: `parts` → `url_segments`

**Locations:**
- `src/collector/scrapers/instagram_scraper.py:569` - Local variable in `_extract_username()`

**What it represents:**
A list of URL path segments created by splitting a URL string on "/" characters.

**Recommended new name:** `url_segments`

**Justification:**
- "parts" is vague - parts of what?
- "url_segments" clearly indicates these are segments of a URL
- Aligns with URL parsing terminology
- Makes the operation (splitting URL into segments) immediately clear

**Current code context:**
```python
def _extract_username(self, url: str) -> str | None:
    """Extract username from profile URL.

    Returns:
        Username or None
    """
    # Must contain instagram.com
    if "instagram.com" not in url:
        return None

    # Handle various URL formats
    # instagram.com/username
    # instagram.com/username/
    # www.instagram.com/username
    parts = url.rstrip("/").split("/")
    if len(parts) >= 1:
        username = parts[-1]
        if username and not any(x in username for x in ["?", "=", ".", "instagram"]):
            return username
    return None
```

**Scope:** Block-level (local to `_extract_username` method)

---

### Priority 5: `i` → `post_index` / `video_index` / `carousel_index`

**Locations:**
- `src/collector/scrapers/instagram_scraper.py:258` - Loop variable in `_scrape_profile()`
- `src/collector/scrapers/instagram_scraper.py:261` - Used in condition
- `src/collector/scrapers/instagram_scraper.py:264` - Used in progress calculation
- `src/collector/scrapers/instagram_scraper.py:265` - Used in progress message
- `src/collector/scrapers/instagram_scraper.py:419` - Loop variable in `_download_post_media()`
- `src/collector/scrapers/instagram_scraper.py:429` - Used in filename
- `src/collector/scrapers/youtube_scraper.py:283` - Loop variable in `_scrape_playlist()`
- `src/collector/scrapers/youtube_scraper.py:302` - Used in progress calculation
- `src/collector/scrapers/youtube_scraper.py:303` - Used in progress message

**What it represents:**
A loop counter/index variable used to track position in iterations over posts, videos, or carousel items.

**Recommended new names:**
- `post_index` in `instagram_scraper.py:258` (iterating over posts)
- `carousel_index` in `instagram_scraper.py:419` (iterating over carousel items)
- `video_index` in `youtube_scraper.py:283` (iterating over videos)

**Justification:**
- Single-letter variables are notorious for poor readability
- "i" gives no context about what's being iterated
- Descriptive names make the code self-documenting
- Especially important when the index is used in user-facing progress messages
- Modern Python encourages meaningful variable names even for loop counters
- Helps distinguish between different loop contexts when debugging

**Current code context:**
```python
# In _scrape_profile
for i, post in enumerate(posts):
    if i > 0:
        delay = random.uniform(self.min_delay, self.max_delay)
        self.update_progress(
            int((i / total) * 90) + 10,
            f"Downloading post {i + 1}/{total} (waiting {delay:.1f}s)...",
        )

# In _download_post_media (carousel)
for i, sidecar_node in enumerate(post.get_sidecar_nodes()):
    filename = f"{i + 1}.{ext}"

# In _scrape_playlist
for i, entry in enumerate(entries):
    progress = int((i + 1) / total * 100)
    self.update_progress(progress, f"Processing {i + 1}/{total}: {video_title}")
```

**Scope:** Block-level (local to specific for-loops)

---

## 3. Implementation Steps

### For Each Variable:

#### Step 1: Find All Occurrences
Use Grep to find all occurrences of the variable name:
```bash
# Example for 'result'
grep -rn "\bresult\b" src/collector/scrapers/
```

**Verification checklist:**
- [ ] Found all variable declarations
- [ ] Found all variable usages
- [ ] Identified scope of each occurrence
- [ ] Checked for name conflicts with existing variables

#### Step 2: Understand the Scope
Analyze each occurrence to understand:
- Is it a parameter, local variable, or loop variable?
- What is its lifetime (function-level, block-level, method-level)?
- Are there any other variables with similar names in the same scope?
- Could the new name conflict with existing variables?

#### Step 3: Rename All Occurrences
For each occurrence of the variable:
1. Update the variable declaration/initialization
2. Update all references to the variable
3. Update any docstrings that mention the variable
4. Update any comments that reference the variable

**Example for `result` → `scrape_result`:**
```python
# Before
result: dict[str, Any] = {...}
result["success"] = True
return result

# After
scrape_result: dict[str, Any] = {...}
scrape_result["success"] = True
return scrape_result
```

#### Step 4: Ensure No Name Conflicts
After renaming, verify:
- [ ] No other variables in the same scope have the new name
- [ ] No parameters or class attributes have the new name
- [ ] No built-in Python names are shadowed
- [ ] No imports conflict with the new name

#### Step 5: Search for Related Documentation
Search for any mentions in:
- Docstrings
- Comments
- README files
- Documentation files
- Type annotations

**Search command:**
```bash
grep -rn "result" src/collector/scrapers/ --include="*.md" --include="*.txt"
```

---

## 4. Risk Mitigation

### Potential Issues with Renaming

#### Issue 1: Breaking References
**Risk:** Other modules or files might reference these variables through inheritance, imports, or documentation.

**Mitigation:**
- This plan is scoped ONLY to the three scraper files
- These are private methods (prefixed with `_`), so external code shouldn't depend on them
- Run all tests after each rename to catch any issues
- Use IDE refactoring tools (see Section 6) for safer renaming

#### Issue 2: Name Collisions
**Risk:** The new name might conflict with existing variables or imported names.

**Mitigation:**
- Check all scopes before renaming
- Verify no existing variables have the target name
- Ensure no built-ins are shadowed
- Check imports for name conflicts

#### Issue 3: Breaking Tests
**Risk:** Test files might reference these variables or expect specific variable names.

**Mitigation:**
- Run the full test suite after each rename
- Check if any test files access these private methods
- Update any test assertions that might be affected

#### Issue 4: Documentation Inconsistency
**Risk:** Comments or docstrings might still reference old variable names.

**Mitigation:**
- Update all docstrings that reference the variable
- Update all inline comments
- Search for the old name in documentation files

#### Issue 5: Merge Conflicts
**Risk:** If others are working on these files simultaneously, renaming could cause merge conflicts.

**Mitigation:**
- Coordinate with team before starting
- Create a feature branch for this work
- Complete all renames in a single pull request
- Communicate the renaming plan to the team

### Testing Approach for Each Rename

#### Before Renaming:
1. Run the full test suite to establish baseline
2. Document all passing tests
3. Create a checklist of tests to verify

#### After Each Rename:
1. Run all scraper-related tests
2. Run integration tests that use the scrapers
3. Manually test each scraper if possible
4. Check for any runtime errors or warnings
5. Verify type hints still work correctly

#### Specific Test Commands:
```bash
# Run all tests
pytest

# Run only scraper tests
pytest tests/ -k scraper

# Run specific scraper tests
pytest tests/test_instagram_scraper.py
pytest tests/test_youtube_scraper.py
```

---

## 5. Code Examples

### Example 1: `result` → `scrape_result`

**Before:**
```python
# src/collector/scrapers/instagram_scraper.py:55
def scrape(self, url: str, job_id: str) -> dict[str, Any]:
    """Scrape Instagram content from URL.

    Args:
        url: Instagram URL (profile, post, reel)
        job_id: Job ID for tracking

    Returns:
        Result dictionary with success status, files, metadata
    """
    result: dict[str, Any] = {
        "success": False,
        "title": None,
        "files": [],
        "metadata": {},
        "error": None,
    }

    try:
        self._use_gallery_dl = False
        self.update_progress(0, "Initializing Instagram scraper")

        # Detect URL type
        url_type = self._detect_url_type(url)

        if url_type == "profile":
            return self._scrape_profile(url, job_id)
        elif url_type == "post":
            return self._scrape_post(url, job_id)
        else:
            result["error"] = f"Unsupported URL type: {url_type}"
            return result

    except Exception as e:
        logger.exception("Error scraping Instagram URL: %s", url)
        result["error"] = str(e)
        return result
```

**After:**
```python
# src/collector/scrapers/instagram_scraper.py:55
def scrape(self, url: str, job_id: str) -> dict[str, Any]:
    """Scrape Instagram content from URL.

    Args:
        url: Instagram URL (profile, post, reel)
        job_id: Job ID for tracking

    Returns:
        Scrape result dictionary with success status, files, metadata
    """
    scrape_result: dict[str, Any] = {
        "success": False,
        "title": None,
        "files": [],
        "metadata": {},
        "error": None,
    }

    try:
        self._use_gallery_dl = False
        self.update_progress(0, "Initializing Instagram scraper")

        # Detect URL type
        url_type = self._detect_url_type(url)

        if url_type == "profile":
            return self._scrape_profile(url, job_id)
        elif url_type == "post":
            return self._scrape_post(url, job_id)
        else:
            scrape_result["error"] = f"Unsupported URL type: {url_type}"
            return scrape_result

    except Exception as e:
        logger.exception("Error scraping Instagram URL: %s", url)
        scrape_result["error"] = str(e)
        return scrape_result
```

**Changes:**
- Line 61: `result` → `scrape_result`
- Line 76: `result["error"]` → `scrape_result["error"]`
- Line 76: `return result` → `return scrape_result`
- Line 80: `result["error"]` → `scrape_result["error"]`
- Line 81: `return result` → `return scrape_result`
- Line 58: Updated docstring from "Result dictionary" to "Scrape result dictionary"

---

### Example 2: `files` → `downloaded_files`

**Before:**
```python
# src/collector/scrapers/instagram_scraper.py:276
def _scrape_profile(self, url: str, job_id: str) -> dict[str, Any]:
    ...
    for i, post in enumerate(posts):
        try:
            # Rate limiting
            if i > 0:
                delay = random.uniform(self.min_delay, self.max_delay)
                self.update_progress(
                    int((i / total) * 90) + 10,
                    f"Downloading post {i + 1}/{total} (waiting {delay:.1f}s)...",
                )
                time.sleep(delay)

            # Download post
            post_dir = (
                output_dir / f"{post.shortcode}_{post.date_utc.strftime('%Y%m%d_%H%M%S')}"
            )
            post_dir.mkdir(exist_ok=True)

            # Download media
            files = self._download_post_media(loader, post, post_dir, job_id)
            result["files"].extend(files)

            # Save post metadata
            post_metadata = self._extract_post_metadata(post)
            metadata_path = post_dir / "metadata.json"
            self.save_metadata(job_id, post_metadata, metadata_path)
```

**After:**
```python
# src/collector/scrapers/instagram_scraper.py:276
def _scrape_profile(self, url: str, job_id: str) -> dict[str, Any]:
    ...
    for post_index, post in enumerate(posts):
        try:
            # Rate limiting
            if post_index > 0:
                delay = random.uniform(self.min_delay, self.max_delay)
                self.update_progress(
                    int((post_index / total) * 90) + 10,
                    f"Downloading post {post_index + 1}/{total} (waiting {delay:.1f}s)...",
                )
                time.sleep(delay)

            # Download post
            post_dir = (
                output_dir / f"{post.shortcode}_{post.date_utc.strftime('%Y%m%d_%H%M%S')}"
            )
            post_dir.mkdir(exist_ok=True)

            # Download media
            downloaded_files = self._download_post_media(loader, post, post_dir, job_id)
            scrape_result["files"].extend(downloaded_files)

            # Save post metadata
            post_metadata = self._extract_post_metadata(post)
            metadata_path = post_dir / "metadata.json"
            self.save_metadata(job_id, post_metadata, metadata_path)
```

**Changes in `_scrape_profile`:**
- Line 258: `for i, post` → `for post_index, post`
- Line 261: `if i > 0` → `if post_index > 0`
- Line 264: `int((i / total) * 90)` → `int((post_index / total) * 90)`
- Line 265: `Downloading post {i + 1}` → `Downloading post {post_index + 1}`
- Line 276: `files = ` → `downloaded_files = `
- Line 277: `result["files"].extend(files)` → `scrape_result["files"].extend(downloaded_files)`

**Changes in `_download_post_media`:**
```python
# Before
def _download_post_media(...) -> list[dict[str, Any]]:
    files = []
    ...
    files.append({
        "file_path": str(filepath.relative_to(self.download_dir)),
        "file_type": file_type,
        "file_size": filepath.stat().st_size,
    })
    return files

# After
def _download_post_media(...) -> list[dict[str, Any]]:
    downloaded_files = []
    ...
    downloaded_files.append({
        "file_path": str(filepath.relative_to(self.download_dir)),
        "file_type": file_type,
        "file_size": filepath.stat().st_size,
    })
    return downloaded_files
```

---

### Example 3: `parts` → `url_segments`

**Before:**
```python
# src/collector/scrapers/instagram_scraper.py:552
def _extract_username(self, url: str) -> str | None:
    """Extract username from profile URL.

    Args:
        url: Instagram profile URL

    Returns:
        Username or None
    """
    # Must contain instagram.com
    if "instagram.com" not in url:
        return None

    # Handle various URL formats
    # instagram.com/username
    # instagram.com/username/
    # www.instagram.com/username
    parts = url.rstrip("/").split("/")
    if len(parts) >= 1:
        username = parts[-1]
        if username and not any(x in username for x in ["?", "=", ".", "instagram"]):
            return username
    return None
```

**After:**
```python
# src/collector/scrapers/instagram_scraper.py:552
def _extract_username(self, url: str) -> str | None:
    """Extract username from profile URL.

    Args:
        url: Instagram profile URL

    Returns:
        Username or None
    """
    # Must contain instagram.com
    if "instagram.com" not in url:
        return None

    # Handle various URL formats
    # instagram.com/username
    # instagram.com/username/
    # www.instagram.com/username
    url_segments = url.rstrip("/").split("/")
    if len(url_segments) >= 1:
        username = url_segments[-1]
        if username and not any(x in username for x in ["?", "=", ".", "instagram"]):
            return username
    return None
```

**Changes:**
- Line 569: `parts = ` → `url_segments = `
- Line 570: `if len(parts)` → `if len(url_segments)`
- Line 571: `parts[-1]` → `url_segments[-1]`

---

### Example 4: `i` → `carousel_index` (in carousel loop)

**Before:**
```python
# src/collector/scrapers/instagram_scraper.py:419
if post.typename == "GraphSidecar":
    # Carousel with multiple items
    for i, sidecar_node in enumerate(post.get_sidecar_nodes()):
        if sidecar_node.is_video:
            url = sidecar_node.video_url
            ext = "mp4"
            file_type = FILE_TYPE_VIDEO
        else:
            url = sidecar_node.display_url
            ext = "jpg"
            file_type = FILE_TYPE_IMAGE

        filename = f"{i + 1}.{ext}"
        filepath = output_dir / filename

        # Download file
        loader.context.download_pic(
            filename=str(filepath), url=url, mtime=post.date_local.timestamp()
        )

        if filepath.exists():
            self.save_file_record(
                job_id,
                str(filepath.relative_to(self.download_dir)),
                file_type,
                filepath.stat().st_size,
            )
            files.append(
                {
                    "file_path": str(filepath.relative_to(self.download_dir)),
                    "file_type": file_type,
                    "file_size": filepath.stat().st_size,
                }
            )
```

**After:**
```python
# src/collector/scrapers/instagram_scraper.py:419
if post.typename == "GraphSidecar":
    # Carousel with multiple items
    for carousel_index, sidecar_node in enumerate(post.get_sidecar_nodes()):
        if sidecar_node.is_video:
            url = sidecar_node.video_url
            file_extension = "mp4"
            file_type = FILE_TYPE_VIDEO
        else:
            url = sidecar_node.display_url
            file_extension = "jpg"
            file_type = FILE_TYPE_IMAGE

        filename = f"{carousel_index + 1}.{file_extension}"
        filepath = output_dir / filename

        # Download file
        loader.context.download_pic(
            filename=str(filepath), url=url, mtime=post.date_local.timestamp()
        )

        if filepath.exists():
            self.save_file_record(
                job_id,
                str(filepath.relative_to(self.download_dir)),
                file_type,
                filepath.stat().st_size,
            )
            downloaded_files.append(
                {
                    "file_path": str(filepath.relative_to(self.download_dir)),
                    "file_type": file_type,
                    "file_size": filepath.stat().st_size,
                }
            )
```

**Changes:**
- Line 419: `for i, sidecar_node` → `for carousel_index, sidecar_node`
- Line 422: `ext = "mp4"` → `file_extension = "mp4"`
- Line 426: `ext = "jpg"` → `file_extension = "jpg"`
- Line 429: `f"{i + 1}.{ext}"` → `f"{carousel_index + 1}.{file_extension}"`
- Line 444: `files.append(` → `downloaded_files.append(`

---

### Example 5: `data` → `metadata_dict` (function parameter)

**Before:**
```python
# src/collector/scrapers/youtube_scraper.py:380
def _extract_metadata(self, info: dict) -> dict[str, Any]:
    """Extract relevant metadata from yt-dlp info dict.

    Args:
        info: Info dict from yt-dlp

    Returns:
        Cleaned metadata dictionary
    """
    metadata = {
        "platform": "youtube",
        "id": info.get("id"),
        "title": info.get("title"),
        "description": info.get("description"),
        ...
    }

    # Remove None values
    return {k: v for k, v in metadata.items() if v is not None}
```

**After:**
```python
# src/collector/scrapers/youtube_scraper.py:380
def _extract_metadata(self, yt_dlp_info: dict) -> dict[str, Any]:
    """Extract relevant metadata from yt-dlp info dict.

    Args:
        yt_dlp_info: Info dict from yt-dlp

    Returns:
        Cleaned metadata dictionary
    """
    metadata_dict = {
        "platform": "youtube",
        "id": yt_dlp_info.get("id"),
        "title": yt_dlp_info.get("title"),
        "description": yt_dlp_info.get("description"),
        ...
    }

    # Remove None values
    return {k: v for k, v in metadata_dict.items() if v is not None}
```

**Changes:**
- Line 380: `info: dict` → `yt_dlp_info: dict` (also improving this parameter name)
- Line 384: `info: Info dict` → `yt_dlp_info: Info dict` (docstring)
- Line 389: `metadata = {` → `metadata_dict = {`
- Lines 391-417: All `info.get()` → `yt_dlp_info.get()`
- Line 421: `for k, v in metadata.items()` → `for k, v in metadata_dict.items()`

---

## 6. Verification

### How to Verify No References Were Missed

#### Method 1: IDE Refactoring Tools (Recommended)
Using an IDE with refactoring support (VS Code, PyCharm, etc.):

1. **VS Code with Python extension:**
   - Right-click on variable name
   - Select "Rename Symbol" (F2)
   - Type new name and press Enter
   - IDE automatically finds and updates all references

2. **PyCharm:**
   - Place cursor on variable name
   - Press Shift+F6 (or Refactor → Rename)
   - Type new name and press Enter
   - Preview all changes before applying
   - Click "Do Refactor"

**Benefits:**
- Automatically finds all references
- Updates comments and docstrings
- Shows preview before applying changes
- Tracks changes across files
- Safe and reliable

#### Method 2: Manual Grep-Based Verification
If not using IDE refactoring tools:

1. **Before renaming:**
   ```bash
   # Find all occurrences
   grep -rn "\bresult\b" src/collector/scrapers/*.py > /tmp/before_rename.txt

   # Count occurrences
   grep -c "\bresult\b" src/collector/scrapers/*.py
   ```

2. **After renaming:**
   ```bash
   # Verify old name is gone (should return nothing)
   grep -rn "\bresult\b" src/collector/scrapers/*.py

   # Verify new name exists
   grep -rn "\bscrape_result\b" src/collector/scrapers/*.py > /tmp/after_rename.txt

   # Count should match before count
   grep -c "\bscrape_result\b" src/collector/scrapers/*.py
   ```

3. **Search for potential misses:**
   ```bash
   # Check for any remaining references in comments/docstrings
   grep -rn "result" src/collector/scrapers/*.py | grep -v "scrape_result" | grep -v "download_result" | grep -v "# "
   ```

#### Method 3: Test-Based Verification
Run tests to ensure functionality is preserved:

```bash
# Run all tests
pytest -v

# Run specific scraper tests
pytest tests/ -k "instagram or youtube" -v

# Run with coverage
pytest --cov=src/collector/scrapers tests/ -v
```

**What to check:**
- All tests pass after rename
- No new warnings or errors
- Coverage remains the same
- No test failures related to renamed variables

#### Method 4: Git Diff Verification
Use git to review all changes:

```bash
# Stage all changes
git add src/collector/scrapers/

# Review changes
git diff --cached src/collector/scrapers/

# Look for:
# - All instances of old name are changed
# - No unintended changes
# - Consistent renaming throughout
```

---

## 7. Additional Improvements

### Future Consideration Variables (6-10)

These variables from the top 10 analysis are recommended for future improvements but are **NOT part of this plan**:

#### 6. `conn` → `db_connection`
**Locations:** Likely in database-related files (not in scrapers)

**Justification:** "conn" is abbreviated and unclear. "db_connection" clearly indicates a database connection.

#### 7. `safe_fields` → `validated_fields`
**Locations:** Likely in validation/security-related files

**Justification:** "safe" is subjective. "validated" is more precise about what happened to the fields.

#### 8. `tmp` → `temp_file`
**Locations:** Likely in file handling code

**Justification:** "tmp" is abbreviated. "temp_file" is clearer and follows Python naming conventions.

#### 9. `ext` → `file_extension`
**Locations:**
- `src/collector/scrapers/instagram_scraper.py:422` (in carousel loop)
- `src/collector/scrapers/instagram_scraper.py:426` (in carousel loop)
- `src/collector/scrapers/instagram_scraper.py:429` (in carousel loop)
- And several more in video/image file handling

**Justification:** "ext" is abbreviated. "file_extension" is clear and self-documenting.

**Note:** This variable appears frequently in the carousel loop (Example 4 above), so it could be renamed alongside the `i` → `carousel_index` change.

#### 10. `match` → `regex_match`
**Locations:**
- `src/collector/scrapers/instagram_scraper.py:589` - `_extract_shortcode()` method

**Justification:** "match" is generic. "regex_match" clearly indicates it's a regex match object. Also avoids potential confusion with the `match` statement introduced in Python 3.10.

**Current code:**
```python
def _extract_shortcode(self, url: str) -> str | None:
    """Extract shortcode from post URL.

    Args:
        url: Instagram post URL

    Returns:
        Shortcode or None
    """
    # instagram.com/p/shortcode/
    # instagram.com/reel/shortcode/
    import re

    match = re.search(r"/(p|reel)/([^/?]+)", url)
    if match:
        return match.group(2)
    return None
```

**Recommended change:**
```python
def _extract_shortcode(self, url: str) -> str | None:
    """Extract shortcode from post URL.

    Args:
        url: Instagram post URL

    Returns:
        Shortcode or None
    """
    # instagram.com/p/shortcode/
    # instagram.com/reel/shortcode/
    import re

    regex_match = re.search(r"/(p|reel)/([^/?]+)", url)
    if regex_match:
        return regex_match.group(2)
    return None
```

---

## 8. Implementation Order

### Recommended Sequence

1. **Start with `parts` → `url_segments`** (easiest, only 3 occurrences)
   - Lowest risk
   - Single function scope
   - Clear benefit

2. **Then `i` → `post_index/carousel_index/video_index`** (high impact, high visibility)
   - Multiple locations but independent
   - Significant readability improvement
   - User-facing impact (progress messages)

3. **Then `files` → `downloaded_files`** (moderate complexity)
   - Single function plus callers
   - Clear improvement in clarity
   - Consistent with "downloaded" terminology

4. **Then `data` → `metadata_dict`** (single location)
   - Only in one function
   - Significant clarity improvement
   - Aligns with existing metadata naming

5. **Finally `result` → `scrape_result`** (most occurrences, highest impact)
   - Most frequent variable
   - Biggest readability impact
   - Consistent across all scrapers
   - Do last to minimize merge conflict risk

### Why This Order?
- Start with easiest/lowest-risk changes
- Build confidence with successful renames
- Leave the most impactful/complex changes for last
- Allows for incremental testing after each change
- Reduces risk of merge conflicts

---

## 9. Success Criteria

### Definition of Done

For this plan to be considered complete, the following must be true:

- [ ] All 5 priority variables have been renamed in all three scraper files
- [ ] All occurrences of old variable names have been replaced
- [ ] All docstrings referencing old variable names have been updated
- [ ] All comments referencing old variable names have been updated
- [ ] All existing tests pass after the changes
- [ ] No new linting warnings have been introduced
- [ ] Code follows PEP 8 naming conventions
- [ ] Git diff shows only intentional variable name changes
- [ ] No merge conflicts with main branch
- [ ] At least one code review has been completed

### Quality Metrics

- **Code Readability:** Variable names should clearly indicate their purpose
- **Consistency:** Similar concepts should use similar naming patterns
- **No Abbreviations:** Variable names should not use abbreviations (except very common ones like `url`, `id`)
- **Length:** Variable names should be long enough to be descriptive but short enough to be readable
- **Type Clarity:** Variable names should indicate the type when helpful (e.g., `_dict`, `_list`, `_path`)

---

## 10. Rollback Plan

### If Issues Arise

If renaming causes unexpected problems:

1. **Immediate rollback:**
   ```bash
   # Revert changes
   git reset --hard HEAD

   # Or revert specific files
   git checkout HEAD -- src/collector/scrapers/
   ```

2. **Partial rollback:**
   - Revert only the problematic variable rename
   - Keep successful renames
   - Investigate the issue separately

3. **Issue types that might require rollback:**
   - Test failures that can't be resolved
   - Performance degradation
   - Breaking changes in public APIs
   - Integration issues with other modules

4. **Before rolling back:**
   - Document what went wrong
   - Save the failing test case
   - Note any error messages
   - Consider if the issue is with the rename or something else

---

## 11. Timeline Estimate

### Time Required

| Variable | Estimated Time | Complexity |
|----------|---------------|------------|
| `parts` → `url_segments` | 15 minutes | Low |
| `i` → `*_index` | 30 minutes | Medium |
| `files` → `downloaded_files` | 30 minutes | Medium |
| `data` → `metadata_dict` | 20 minutes | Low |
| `result` → `scrape_result` | 45 minutes | High |
| **Total** | **~2.5 hours** | - |

### Additional Time
- Testing: 30 minutes
- Code review: 30 minutes
- Documentation updates: 15 minutes
- Buffer for unexpected issues: 30 minutes

**Total estimated time: 4 hours**

---

## 12. Related Documentation

### Referenced Plans
- Plan 01: Codebase structure analysis (if exists)
- Plan 02: Initial variable naming analysis (if exists)

### Python Naming Conventions
- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 20 -- The Zen of Python](https://peps.python.org/pep-0020/) (Explicit is better than implicit)

### Best Practices
- Use descriptive names over single letters (except for loop counters in very short loops)
- Avoid abbreviations unless widely understood
- Name variables based on what they represent, not their type
- Use `_` suffix to avoid shadowing built-ins (e.g., `type_` instead of `type`)
- Be consistent with naming patterns across the codebase

---

## Appendix A: Complete File Listing

### Files Modified in This Plan

1. `src/collector/scrapers/instagram_scraper.py`
   - Line 55: `result` → `scrape_result`
   - Line 198: `result` → `scrape_result`
   - Line 258: `i` → `post_index`
   - Line 276: `files` → `downloaded_files`
   - Line 332: `result` → `scrape_result`
   - Line 366: `files` → `downloaded_files`
   - Line 414: `files` → `downloaded_files`
   - Line 419: `i` → `carousel_index`
   - Line 422: `ext` → `file_extension` (optional, recommended)
   - Line 569: `parts` → `url_segments`
   - Line 589: `match` → `regex_match` (optional, future consideration)

2. `src/collector/scrapers/youtube_scraper.py`
   - Line 50: `result` → `scrape_result`
   - Line 99: `result` → `scrape_result`
   - Line 244: `result` → `scrape_result`
   - Line 283: `i` → `video_index`
   - Line 380: `info` → `yt_dlp_info` (parameter improvement)
   - Line 389: `metadata` → `metadata_dict`

3. `src/collector/scrapers/base_scraper.py`
   - No changes required (variables here are well-named)

---

## Appendix B: Testing Checklist

### Pre-Rename Testing
- [ ] Run full test suite and document results
- [ ] Note all passing tests
- [ ] Document any currently failing tests (should be none)

### Post-Rename Testing
After each variable rename:

- [ ] Run full test suite
- [ ] Run scraper-specific tests
- [ ] Check for any new warnings
- [ ] Verify type hints still work
- [ ] Check for import errors
- [ ] Verify no syntax errors
- [ ] Test each scraper manually if possible

### Final Verification
- [ ] All tests pass
- [ ] No linting warnings
- [ ] No type checking errors
- [ ] Git diff reviewed
- [ ] Code review completed
- [ ] Documentation updated

---

## Appendix C: Command Reference

### Useful Commands for This Work

```bash
# Find all occurrences of a variable
grep -rn "\bresult\b" src/collector/scrapers/

# Count occurrences
grep -c "\bresult\b" src/collector/scrapers/*.py

# Find variable in specific file
grep -n "\bresult\b" src/collector/scrapers/instagram_scraper.py

# Show context around matches
grep -C 3 "\bresult\b" src/collector/scrapers/*.py

# Search for variable in docstrings/comments
grep -rn "result" src/collector/scrapers/ --include="*.py" | grep -E "(#|\"\"\"|''')"

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_instagram_scraper.py -v

# Run with coverage
pytest --cov=src/collector/scrapers tests/

# Check linting
pylint src/collector/scrapers/

# Check type hints
mypy src/collector/scrapers/

# Git diff review
git diff src/collector/scrapers/

# Stage changes
git add src/collector/scrapers/

# Commit
git commit -m "Improve variable naming in scrapers"
```

---

**End of Plan**
