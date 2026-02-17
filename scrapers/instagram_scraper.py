"""Instagram scraper using Instaloader with gallery-dl fallback."""

from __future__ import annotations

import json
import logging
import random
import tempfile
import time
from pathlib import Path
from typing import Any

import instaloader

from config import FILE_TYPE_IMAGE, FILE_TYPE_METADATA, FILE_TYPE_VIDEO
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class InstagramScraper(BaseScraper):
    """Scraper for Instagram content using Instaloader."""

    def __init__(
        self,
        *args,
        min_delay: float = 5.0,
        max_delay: float = 10.0,
        session_file: Path | None = None,
        **kwargs,
    ):
        """Initialize Instagram scraper.

        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
            session_file: Path to encrypted session file for authentication
        """
        super().__init__(*args, **kwargs)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session_file = session_file
        self._use_gallery_dl = False

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

    def _detect_url_type(self, url: str) -> str:
        """Detect the type of Instagram URL.

        Args:
            url: Instagram URL

        Returns:
            URL type: 'profile', 'post', 'reel', 'unknown'
        """
        if "/p/" in url or "/reel/" in url:
            return "post"
        elif "instagram.com/" in url and not any(x in url for x in ["/p/", "/reel/", "/tv/"]):
            return "profile"
        return "unknown"

    def _get_instaloader(self) -> instaloader.Instaloader:
        """Get configured Instaloader instance.

        Returns:
            Configured Instaloader instance
        """
        loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
        )

        # Load session if available
        if self.session_file and self.session_file.exists():
            try:
                # The session file is encrypted from our session_manager
                # We need to decrypt it first before passing to Instaloader
                # But Instaloader expects a specific format, so we decrypt to a temp file
                from cryptography.fernet import Fernet, InvalidToken

                # Read encrypted session
                with open(self.session_file, "rb") as f:
                    encrypted_data = f.read()

                # Try to decrypt using the session manager's approach
                # We'll need the encryption key - check env var
                import os

                key_str = os.environ.get("SCRAPER_SESSION_KEY")
                if key_str:
                    import base64

                    from cryptography.hazmat.primitives import hashes
                    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

                    # Derive proper Fernet key
                    key_bytes = key_str.encode()
                    if len(key_str.split(".")) < 2:
                        # Not a proper Fernet key, derive one
                        kdf = PBKDF2HMAC(
                            algorithm=hashes.SHA256(),
                            length=32,
                            salt=b"instagram_scraper",
                            iterations=100000,
                        )
                        key_bytes = kdf.derive(key_bytes)
                    else:
                        key_bytes = key_str.encode()

                    cipher = Fernet(
                        base64.urlsafe_b64encode(key_bytes)
                        if len(key_str.split(".")) < 2
                        else key_str
                    )

                    try:
                        decrypted_json = cipher.decrypt(encrypted_data)
                        session_data = json.loads(decrypted_json)

                        # Create a temporary session file in Instaloader's format
                        # Instaloader expects: username -> session file with cookies
                        with tempfile.NamedTemporaryFile(
                            mode="w", delete=False, suffix=".json"
                        ) as tmp:
                            tmp.write(json.dumps(session_data.get("cookies", {})))
                            tmp_path = Path(tmp.name)

                        # Load session with Instaloader
                        loader.load_session_from_file("instagram_user", str(tmp_path))
                        logger.info("Loaded encrypted Instagram session from file")

                        # Clean up temp file
                        tmp_path.unlink()
                    except InvalidToken:
                        logger.warning("Could not decrypt session file (wrong key?)")
                    except Exception as e:
                        logger.warning("Error processing session file: %s", e)
                else:
                    logger.warning("No SCRAPER_SESSION_KEY set, cannot load encrypted session")

            except Exception as e:
                logger.warning("Could not load session file: %s", e)

        return loader

    def _scrape_profile(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape all posts from an Instagram profile.

        Args:
            url: Instagram profile URL
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
            self.update_progress(5, "Extracting username from URL")

            # Extract username from URL
            username = self._extract_username(url)
            if not username:
                result["error"] = "Could not extract username from URL"
                return result

            result["title"] = f"@{username}"
            self.update_progress(10, f"Loading profile: @{username}")

            loader = self._get_instaloader()

            try:
                profile = instaloader.Profile.from_username(loader.context, username)
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "404" in error_msg or "429" in error_msg:
                    result["error"] = (
                        f"Authentication error: {error_msg}. Try refreshing session cookies."
                    )
                    return result
                raise

            output_dir = self.download_dir / "instagram" / username
            output_dir.mkdir(parents=True, exist_ok=True)

            # Collect metadata
            profile_metadata = {
                "platform": "instagram",
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "external_url": profile.external_url,
                "followers": profile.followers,
                "following": profile.following,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified,
                "profile_pic_url": profile.profile_pic_url,
                "posts_count": profile.mediacount,
                "url": url,
            }
            result["metadata"] = profile_metadata

            self.update_progress(15, "Downloading profile posts")

            posts = list(profile.get_posts())
            total = len(posts)
            downloaded = 0
            failed = 0

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

                    if metadata_path.exists():
                        self.save_file_record(
                            job_id,
                            str(metadata_path.relative_to(self.download_dir)),
                            FILE_TYPE_METADATA,
                            metadata_path.stat().st_size,
                            post_metadata,
                        )

                    downloaded += 1

                except Exception as e:
                    logger.warning("Failed to download post %s: %s", post.shortcode, e)
                    failed += 1
                    continue

            # Save profile-level metadata
            profile_metadata_path = output_dir / "profile_metadata.json"
            self.save_metadata(job_id, profile_metadata, profile_metadata_path)

            if profile_metadata_path.exists():
                self.save_file_record(
                    job_id,
                    str(profile_metadata_path.relative_to(self.download_dir)),
                    FILE_TYPE_METADATA,
                    profile_metadata_path.stat().st_size,
                    profile_metadata,
                )

            result["success"] = True
            self.update_progress(100, f"Downloaded {downloaded} posts ({failed} failed)")

        except Exception as e:
            logger.exception("Error scraping Instagram profile: %s", url)
            result["error"] = str(e)

        return result

    def _scrape_post(self, url: str, job_id: str) -> dict[str, Any]:
        """Scrape a single Instagram post/reel.

        Args:
            url: Instagram post URL
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
            self.update_progress(10, "Fetching post info")

            loader = self._get_instaloader()

            # Extract shortcode from URL
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                result["error"] = "Could not extract post shortcode from URL"
                return result

            post = instaloader.Post.from_shortcode(loader.context, shortcode)

            # Get username for directory
            username = post.owner_username
            output_dir = self.download_dir / "instagram" / username
            output_dir.mkdir(parents=True, exist_ok=True)

            post_dir = output_dir / f"{post.shortcode}_{post.date_utc.strftime('%Y%m%d_%H%M%S')}"
            post_dir.mkdir(exist_ok=True)

            result["title"] = f"Post by @{username}"

            self.update_progress(30, "Downloading media")

            # Download media
            files = self._download_post_media(loader, post, post_dir, job_id)
            result["files"].extend(files)

            self.update_progress(70, "Saving metadata")

            # Save metadata
            post_metadata = self._extract_post_metadata(post)
            metadata_path = post_dir / "metadata.json"
            self.save_metadata(job_id, post_metadata, metadata_path)

            if metadata_path.exists():
                self.save_file_record(
                    job_id,
                    str(metadata_path.relative_to(self.download_dir)),
                    FILE_TYPE_METADATA,
                    metadata_path.stat().st_size,
                    post_metadata,
                )

            result["metadata"] = post_metadata
            result["success"] = True

            self.update_progress(100, "Complete")

        except Exception as e:
            logger.exception("Error scraping Instagram post: %s", url)
            result["error"] = str(e)

        return result

    def _download_post_media(
        self,
        loader: instaloader.Instaloader,
        post: instaloader.Post,
        output_dir: Path,
        job_id: str,
    ) -> list[dict[str, Any]]:
        """Download media files from a post.

        Args:
            loader: Instaloader instance
            post: Post object
            output_dir: Directory to save files
            job_id: Job ID

        Returns:
            List of file info dicts
        """
        files = []

        try:
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

            elif post.is_video:
                # Single video
                filepath = output_dir / f"video.{post.url.split('.')[-1].split('?')[0]}"
                loader.download_post(post, target=str(output_dir))

                # Find the downloaded video file
                for ext in ["mp4", "mov"]:
                    potential_file = output_dir / f"video.{ext}"
                    if potential_file.exists():
                        filepath = potential_file
                        break

                if filepath.exists():
                    self.save_file_record(
                        job_id,
                        str(filepath.relative_to(self.download_dir)),
                        FILE_TYPE_VIDEO,
                        filepath.stat().st_size,
                    )
                    files.append(
                        {
                            "file_path": str(filepath.relative_to(self.download_dir)),
                            "file_type": FILE_TYPE_VIDEO,
                            "file_size": filepath.stat().st_size,
                        }
                    )

            else:
                # Single image
                filepath = output_dir / "photo.jpg"
                loader.download_post(post, target=str(output_dir))

                # Find the downloaded image file
                for ext in ["jpg", "webp", "png"]:
                    potential_file = output_dir / f"photo.{ext}"
                    if potential_file.exists():
                        filepath = potential_file
                        break

                if filepath.exists():
                    self.save_file_record(
                        job_id,
                        str(filepath.relative_to(self.download_dir)),
                        FILE_TYPE_IMAGE,
                        filepath.stat().st_size,
                    )
                    files.append(
                        {
                            "file_path": str(filepath.relative_to(self.download_dir)),
                            "file_type": FILE_TYPE_IMAGE,
                            "file_size": filepath.stat().st_size,
                        }
                    )

        except Exception as e:
            logger.error("Error downloading media for post %s: %s", post.shortcode, e)

        return files

    def _extract_post_metadata(self, post: instaloader.Post) -> dict[str, Any]:
        """Extract metadata from a post.

        Args:
            post: Post object

        Returns:
            Metadata dictionary
        """
        # Extract hashtags
        hashtags = [tag.strip("#") for tag in post.caption_hashtags if tag]

        # Extract mentions
        mentions = [mention.strip("@") for mention in post.caption_mentions if mention]

        metadata = {
            "platform": "instagram",
            "shortcode": post.shortcode,
            "url": f"https://www.instagram.com/p/{post.shortcode}/",
            "type": post.typename,
            "owner": {
                "username": post.owner_username,
                "id": post.owner_id,
            },
            "caption": post.caption,
            "hashtags": hashtags,
            "mentions": mentions,
            "date_utc": post.date_utc.isoformat() if post.date_utc else None,
            "date_local": post.date_local.isoformat() if post.date_local else None,
            "likes": post.likes,
            "comments": post.comments,
            "is_video": post.is_video,
            "video_url": post.video_url if post.is_video else None,
            "video_view_count": post.video_view_count if post.is_video else None,
            "display_url": post.url,
            "sponsored": post.is_sponsored,
            "location": post.location.name if post.location else None,
        }

        return metadata

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
