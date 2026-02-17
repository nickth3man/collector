"""YouTube scraper using yt-dlp and youtube-transcript-api."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from scrapers.base_scraper import BaseScraper
from config import FILE_TYPE_AUDIO, FILE_TYPE_METADATA, FILE_TYPE_TRANSCRIPT, FILE_TYPE_VIDEO

logger = logging.getLogger(__name__)


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube content using yt-dlp."""

    # Default quality options
    QUALITY_PRESETS = {
        "4k": "2160",
        "1080": "1080",
        "720": "720",
        "480": "480",
        "audio": "bestaudio/best",
    }

    def __init__(self, *args, quality: str = "1080", **kwargs):
        """Initialize YouTube scraper.

        Args:
            quality: Maximum video quality (e.g., "1080" for 1080p)
        """
        super().__init__(*args, **kwargs)
        self.quality = quality

    def scrape(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape YouTube video(s) from URL.

        Args:
            url: YouTube URL (video, playlist, channel)
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
            self.update_progress(0, "Initializing YouTube scraper")

            # Check if this is a playlist/channel
            if self._is_playlist_or_channel(url):
                return self._scrape_playlist(url, job_id)
            else:
                return self._scrape_single_video(url, job_id)

        except Exception as e:
            logger.exception("Error scraping YouTube URL: %s", url)
            result["error"] = str(e)
            return result

    def _is_playlist_or_channel(self, url: str) -> bool:
        """Check if URL is a playlist or channel.

        Args:
            url: YouTube URL

        Returns:
            True if playlist/channel, False if single video
        """
        playlist_patterns = [
            r"playlist\?list=",
            r"/channel/",
            r"/c/",
            r"/user/",
        ]
        return any(re.search(pattern, url) for pattern in playlist_patterns)

    def _scrape_single_video(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape a single YouTube video.

        Args:
            url: YouTube video URL
            job_id: Job ID

        Returns:
            Result dictionary
        """
        result: dict[str, Any] = {
            "success": False,
            "title": None,
            "files": [],
            "metadata": {},
            "error": None,
        }

        try:
            self.update_progress(5, "Extracting video info")

            # Configure yt-dlp options
            quality_format = (
                f"bestvideo[height<={self.quality}]+bestaudio/best[height<={self.quality}]/best"
            )
            if self.quality == "audio":
                quality_format = "bestaudio/best"

            output_dir = self.download_dir / "youtube"
            output_template = str(output_dir / "%(uploader)s" / "%(title)s" / "video.%(ext)s")

            ydl_opts = {
                "format": quality_format,
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "writesubtitles": False,  # We'll fetch transcripts separately
                "writeautomaticsub": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First extract info without downloading
                self.update_progress(10, "Fetching video metadata")
                info = ydl.extract_info(url, download=False)

                if not info:
                    result["error"] = "Could not extract video info"
                    return result

                title = info.get("title", "Unknown Title")
                _uploader = info.get("uploader", "Unknown Channel")
                result["title"] = title

                self.update_progress(20, f"Downloading: {title}")

                # Download the video
                info = ydl.extract_info(url, download=True)

                # Get the actual file path
                video_path = ydl.prepare_filename(info)
                video_file = Path(video_path)

                # Get metadata
                metadata = self._extract_metadata(info)
                result["metadata"] = metadata

                self.update_progress(70, "Saving metadata")

                # Save metadata
                metadata_path = video_file.parent / "metadata.json"
                self.save_metadata(job_id, metadata, metadata_path)

                if metadata_path.exists():
                    self.save_file_record(
                        job_id,
                        str(metadata_path.relative_to(self.download_dir)),
                        FILE_TYPE_METADATA,
                        metadata_path.stat().st_size,
                        metadata,
                    )
                    result["files"].append(
                        {
                            "file_path": str(metadata_path.relative_to(self.download_dir)),
                            "file_type": FILE_TYPE_METADATA,
                            "file_size": metadata_path.stat().st_size,
                        }
                    )

                self.update_progress(80, "Fetching transcript")

                # Fetch and save transcript
                video_id = info.get("id")
                if video_id:
                    transcript_path = self._fetch_transcript(video_id, video_file.parent)
                    if transcript_path:
                        self.save_file_record(
                            job_id,
                            str(transcript_path.relative_to(self.download_dir)),
                            FILE_TYPE_TRANSCRIPT,
                            transcript_path.stat().st_size,
                        )
                        result["files"].append(
                            {
                                "file_path": str(transcript_path.relative_to(self.download_dir)),
                                "file_type": FILE_TYPE_TRANSCRIPT,
                                "file_size": transcript_path.stat().st_size,
                            }
                        )

                self.update_progress(90, "Finalizing")

                # Record video file
                if video_file.exists():
                    file_type = (
                        FILE_TYPE_VIDEO
                        if video_file.suffix not in [".m4a", ".mp3"]
                        else FILE_TYPE_AUDIO
                    )
                    self.save_file_record(
                        job_id,
                        str(video_file.relative_to(self.download_dir)),
                        file_type,
                        video_file.stat().st_size,
                    )
                    result["files"].append(
                        {
                            "file_path": str(video_file.relative_to(self.download_dir)),
                            "file_type": file_type,
                            "file_size": video_file.stat().st_size,
                        }
                    )

                result["success"] = True
                self.update_progress(100, "Complete")

        except Exception as e:
            logger.exception("Error downloading YouTube video: %s", url)
            result["error"] = str(e)

        return result

    def _scrape_playlist(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape a YouTube playlist or channel.

        Note: For playlists, this creates a single job but returns info
        about all videos. The UI may want to create individual jobs per video.

        Args:
            url: YouTube playlist/channel URL
            job_id: Job ID

        Returns:
            Result dictionary with all videos info
        """
        result: dict[str, Any] = {
            "success": False,
            "title": None,
            "files": [],
            "metadata": {},
            "error": None,
        }

        try:
            self.update_progress(5, "Extracting playlist info")

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Don't download, just extract info
                "ignoreerrors": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    result["error"] = "Could not extract playlist info"
                    return result

                title = info.get("title", "Playlist")
                result["title"] = f"Playlist: {title}"

                entries = info.get("entries", [])
                total = len(entries)

                result["metadata"] = {
                    "type": "playlist",
                    "title": title,
                    "uploader": info.get("uploader"),
                    "video_count": total,
                    "videos": [],
                }

                for i, entry in enumerate(entries):
                    if not entry:
                        continue

                    video_url = (
                        entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    )
                    video_title = entry.get("title", "Unknown")

                    result["metadata"]["videos"].append(
                        {
                            "id": entry.get("id"),
                            "title": video_title,
                            "url": video_url,
                            "duration": entry.get("duration"),
                            "view_count": entry.get("view_count"),
                        }
                    )

                    progress = int((i + 1) / total * 100)
                    self.update_progress(progress, f"Processing {i + 1}/{total}: {video_title}")

                result["success"] = True
                self.update_progress(100, f"Found {total} videos in playlist")

        except Exception as e:
            logger.exception("Error processing YouTube playlist: %s", url)
            result["error"] = str(e)

        return result

    def _fetch_transcript(self, video_id: str, output_dir: Path) -> Path | None:
        """Fetch and save transcript for a video.

        Args:
            video_id: YouTube video ID
            output_dir: Directory to save transcript

        Returns:
            Path to transcript file, or None if unavailable
        """
        try:
            api = YouTubeTranscriptApi()

            # Try to get transcript (manually created first, then auto-generated)
            try:
                transcript_list = api.fetch(video_id, languages=["en"])
                transcript = transcript_list
            except Exception:
                # Fallback to auto-generated
                try:
                    transcript_list = api.fetch(video_id, languages=["en"], languages_auto=True)
                    transcript = transcript_list
                except Exception:
                    # No transcript available
                    logger.info("No transcript available for video %s", video_id)
                    return None

            # Format as plain text
            transcript_text = self._format_transcript(transcript)

            # Save to file
            transcript_path = output_dir / "transcript.txt"
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            logger.info("Saved transcript for video %s", video_id)
            return transcript_path

        except Exception as e:
            logger.warning("Could not fetch transcript for %s: %s", video_id, e)
            return None

    def _format_transcript(self, transcript: list[dict]) -> str:
        """Format transcript as readable text.

        Args:
            transcript: List of transcript entries

        Returns:
            Formatted transcript text
        """
        lines = []
        for entry in transcript:
            text = entry.get("text", "")
            start = entry.get("start", 0)
            _duration = entry.get("duration", 0)

            # Format timestamp as MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"

            lines.append(f"[{timestamp}] {text}")

        return "\n".join(lines)

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
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "uploader_url": info.get("uploader_url"),
            "channel": info.get("channel"),
            "channel_id": info.get("channel_id"),
            "channel_url": info.get("channel_url"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "upload_date": info.get("upload_date"),
            "release_date": info.get("release_date"),
            "availability": info.get("availability"),
            "tags": info.get("tags"),
            "categories": info.get("categories"),
            "live_status": info.get("live_status"),
            "playable_in_embed": info.get("playable_in_embed"),
            "width": info.get("width"),
            "height": info.get("height"),
            "fps": info.get("fps"),
            "format": info.get("format"),
            "format_id": info.get("format_id"),
            "ext": info.get("ext"),
            "filesize": info.get("filesize"),
            "url": info.get("webpage_url"),
        }

        # Remove None values
        return {k: v for k, v in metadata.items() if v is not None}
