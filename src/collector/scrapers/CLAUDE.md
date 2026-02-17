# SCRAPERS KNOWLEDGE

## OVERVIEW

Platform adapters live here. Each scraper extends one contract, returns one
result shape, reports progress for live UI polling.

## STRUCTURE

- `base_scraper.py` - abstract contract + shared helpers (progress,
  metadata/file persistence, filename sanitization)
- `youtube_scraper.py` - `YouTubeScraper` using `yt-dlp` + transcript fetch via
  `youtube-transcript-api`
- `instagram_scraper.py` - `InstagramScraper` using `instaloader` +
  cookie/session auth + delay-based throttling
- `__init__.py` - package marker

## CONVENTIONS

- Inherit from `BaseScraper`
- Implement `scrape(url: str, job_id: str) -> dict[str, Any]`
- Return dict keys: `success`, `title`, `files`, `metadata`, `error`
- Never raise to caller for expected platform failures, set `error` and return
- Use `self.update_progress(progress_pct, operation_name)` for user-visible
  state
- Progress values are percent integers, operation text should be short,
  action-first
- Persist metadata with `save_metadata(...)`, persist file records with
  `save_file_record(...)`
- File entries appended to `result["files"]` use: `file_path`, `file_type`,
  `file_size`
- Keep platform detection/routing inside scraper (`_detect_url_type`, playlist
  detection, etc.)
- Keep platform-specific parsing private (`_extract_*`, `_fetch_*`,
  `_download_*`)

### Type Checking

- Annotate all public method signatures with types
- Use `dict[str, Any]` for scraper result dicts
- Abstract methods from `BaseScraper` must match parent signature exactly
- Run `uvx ty check` to catch signature mismatches

### YouTube Pattern

- Primary downloader: `yt_dlp.YoutubeDL`
- Supports single video plus playlist/channel metadata paths
- Quality handled by preset or format string, audio-only path supported
- Transcript attempt after media download via `YouTubeTranscriptApi`
- Metadata extracted from `yt-dlp` info dict and filtered for non-null values

### Instagram Pattern

- Primary downloader: `instaloader.Instaloader`
- URL classes: profile and post/reel
- Session auth from encrypted session file when available
- Delay between profile post requests uses randomized range
- Delay source is `min_delay` / `max_delay`, wired from `SCRAPER_IG_DELAY_MIN`
  and `SCRAPER_IG_DELAY_MAX`
- On auth/rate errors (`401`, `404`, `429`), return actionable `error` text

## WHERE TO LOOK

- Add new platform: create `<platform>_scraper.py` with class
  `<Platform>Scraper(BaseScraper)`
- First implement `scrape(...)` with standard result dict and progress
  checkpoints
- Add private helpers for URL parsing, media download, metadata mapping
- Reuse base helpers for metadata/file DB writes, avoid duplicate persistence
  logic
- Instantiate new scraper where jobs are dispatched, pass `db_path`,
  `download_dir`, `progress_callback`
- Ensure result contract stays identical so services/UI stay platform-agnostic
