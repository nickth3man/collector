# Content Collector

A Flask-based web application for downloading media from Instagram and YouTube with real-time progress tracking.

## Features

- **YouTube Support**: Download videos, playlists, and channels with transcripts
- **Instagram Support**: Download photos, videos, reels, and profile posts
- **Real-time Progress**: Watch downloads progress via HTMX polling
- **Metadata Preservation**: Captions, descriptions, timestamps, and engagement metrics saved as JSON
- **File Browser**: Navigate downloaded content by platform → profile → content
- **Download History**: Track all downloads with filtering and retry options
- **Dark Mode**: Automatic dark mode based on system preference with manual toggle

## Requirements

- Python 3.10 or higher
- Deno (JavaScript runtime for yt-dlp YouTube support)
- FFmpeg (for video/audio stream merging)

## Installation

1. **Install system dependencies:**

```bash
# Deno (required by yt-dlp)
curl -fsSL https://deno.land/install.sh | sh

# FFmpeg
sudo apt install ffmpeg
```

2. **Install Python dependencies using uv:**

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync
```

3. **Set up environment variables:**

Create a `.env` file or set environment variables:

```bash
# Required
export FLASK_SECRET_KEY="your-secret-key-here"

# Optional (with defaults shown)
export SCRAPER_DOWNLOAD_DIR="./downloads"
export SCRAPER_DB_PATH="./scraper.db"
export SCRAPER_MAX_CONCURRENT="2"
export SCRAPER_IG_DELAY_MIN="5"
export SCRAPER_IG_DELAY_MAX="10"
export SCRAPER_DISK_WARN_MB="1024"
export FLASK_HOST="127.0.0.1"
export FLASK_PORT="5000"
```

## Usage

### Development Server

```bash
uv run python app.py
```

The web interface will be available at http://localhost:5000

### Production Server

For production use Gunicorn with a single worker (to avoid SQLite write contention):

```bash
uv run gunicorn -w 1 -t 120 app:app
```

## Instagram Cookie Authentication (Recommended)

Instagram scraping works best with authenticated sessions. Instead of passwords, use browser cookies:

### Export Cookies from Chrome/Firefox

1. **Install a cookie export extension:**
   - Chrome: "Get cookies.txt LOCALLY" or "EditThisCookie"
   - Firefox: "Cookie Quick Manager"

2. **Log into Instagram** in your browser using a throwaway account

3. **Export cookies** to a file named `instagram_cookies.txt`

4. **Place the file** in the project root (outside the web root for security)

5. **Set the session key** (for encryption):
   ```bash
   export SCRAPER_SESSION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
   ```

### Why Use Cookies?

- More reliable than username/password
- Appears as legitimate browser activity
- Avoids password storage security issues
- Works with throwaway accounts

### Important: Use Throwaway Accounts

**Never use your personal Instagram account** for scraping. Create a dedicated throwaway account:
- Doesn't need real personal information
- Can be replaced if banned
- Protects your main account from suspension

## Project Structure

```
collector/
├── app.py                      # Flask entry point, routes, job management
├── app_factory.py              # Application factory pattern
├── executor_adapter.py         # Task execution abstraction
├── config.py                   # Configuration with environment variable support
├── pyproject.toml              # uv project configuration
├── security/
│   ├── csrf.py                 # CSRF token generation/validation
│   └── paths.py                # Path traversal protection
├── scrapers/
│   ├── base_scraper.py         # Abstract base class
│   ├── youtube_scraper.py      # yt-dlp + transcript integration
│   └── instagram_scraper.py    # Instaloader + gallery-dl fallback
├── templates/
│   ├── base.html               # Layout with nav and dark mode
│   ├── dashboard.html          # URL input + active jobs
│   ├── browse.html             # File browser
│   ├── history.html            # Download history table
│   └── partials/               # HTMX fragments
├── static/
│   └── vendor/                 # Local fallback assets (Pico CSS, HTMX)
├── downloads/                  # Downloaded content
│   ├── youtube/
│   └── instagram/
├── tests/
└── scraper.db                  # SQLite database
```

### Static Asset Policy

Frontend assets (Pico CSS, HTMX) use **CDN-first with local fallback**:

1. Primary: Load from CDN for performance and caching
2. Fallback: If CDN fails, automatically load from `static/vendor/`

This ensures the app works offline and degrades gracefully when CDNs are unavailable.

## Configuration

All settings are managed through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_DOWNLOAD_DIR` | `./downloads` | Root directory for downloads |
| `SCRAPER_DB_PATH` | `./scraper.db` | SQLite database path |
| `SCRAPER_MAX_CONCURRENT` | `2` | Maximum concurrent downloads |
| `SCRAPER_IG_DELAY_MIN` | `5` | Min seconds between IG requests |
| `SCRAPER_IG_DELAY_MAX` | `10` | Max seconds between IG requests |
| `SCRAPER_DISK_WARN_MB` | `1024` | Disk space warning threshold (MB) |
| `SCRAPER_SESSION_KEY` | - | Fernet key for session encryption |
| `FLASK_SECRET_KEY` | - | Flask session/CSRF secret |
| `FLASK_HOST` | `127.0.0.1` | Server host |
| `FLASK_PORT` | `5000` | Server port |

## Troubleshooting

### Instagram 401 Errors

If you see persistent 401 Unauthorized errors:
1. Refresh your session cookies (export new cookies.txt)
2. Increase request delays: `SCRAPER_IG_DELAY_MIN=10 SCRAPER_IG_DELAY_MAX=20`
3. Wait 24-48 hours before trying again

### YouTube Download Issues

If YouTube downloads fail:
1. Ensure Deno is installed: `deno --version`
2. Update yt-dlp: `uv pip install --upgrade yt-dlp`
3. Check the error message for specific issues

### Disk Space

Monitor disk space before large downloads:
```bash
df -h
```

The app will warn when free space falls below 1 GB (configurable).

## Legal Disclaimer

**This tool is for personal use only.** You are responsible for:
- Complying with applicable laws and regulations
- Respecting platform Terms of Service
- Not redistributing downloaded content
- Honoring copyright and intellectual property rights
- Using appropriate authentication (throwaway accounts)

The developers are not responsible for misuse of this software.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Credits

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [HTMX](https://htmx.org/) - Dynamic HTML
- [Pico CSS](https://picocss.com/) - Minimal styling
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Instaloader](https://instaloader.github.io/) - Instagram scraper
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - Transcript extraction
