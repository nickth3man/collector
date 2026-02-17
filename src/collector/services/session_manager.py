"""Session management for Instagram with Fernet encryption.

This module handles loading, saving, and encrypting Instagram sessions
from cookies.txt files.
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages encrypted Instagram sessions."""

    def __init__(self, config_dir: Path, encryption_key: str | None = None):
        """Initialize session manager.

        Args:
            config_dir: Directory to store session files
            encryption_key: Fernet key for encrypting sessions (optional)
        """
        self.config_dir = config_dir
        self.encryption_key = encryption_key
        self.sessions_dir = config_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Fernet cipher if key is provided
        self.cipher: Fernet | None = None
        if encryption_key:
            # Ensure key is proper base64 for Fernet
            key_bytes = (
                encryption_key.encode()
                if len(encryption_key.split(".")) < 2
                else encryption_key.encode()
            )
            if len(encryption_key.split(".")) >= 2:
                # Already a valid Fernet key
                self.cipher = Fernet(encryption_key)
            else:
                # Derive a proper Fernet key from the provided key
                # Fernet requires 32-byte base64-encoded key
                import hashlib

                key_hash = hashlib.sha256(key_bytes).digest()
                self.cipher = Fernet(base64.urlsafe_b64encode(key_hash))

    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher instance.

        Returns:
            Fernet cipher

        Raises:
            ValueError: If no encryption key is configured
        """
        if not self.cipher:
            raise ValueError(
                "No encryption key configured. Set SCRAPER_SESSION_KEY environment variable."
            )
        return self.cipher

    def load_cookies_from_file(self, cookies_file: Path) -> dict[str, Any]:
        """Load cookies from a cookies.txt file (Netscape format).

        Args:
            cookies_file: Path to cookies.txt file

        Returns:
            Dictionary with cookie data

        Raises:
            ValueError: If file format is invalid
        """
        cookies = []

        with open(cookies_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse Netscape cookie format
                # tab-separated: domain \t flag \t path \t secure \t expiration \t name \t value
                parts = line.split("\t")
                if len(parts) < 7:
                    continue

                cookie = {
                    "domain": parts[0],
                    "path": parts[2],
                    "secure": parts[3].lower() == "true",
                    "expiration": parts[4],
                    "name": parts[5],
                    "value": parts[6],
                }

                # Filter for Instagram session cookies
                cookie_name = str(cookie["name"])
                cookie_domain = str(cookie["domain"])
                if "instagram.com" in cookie_domain and cookie_name in [
                    "sessionid",
                    "ds_user_id",
                    "mid",
                    "ig_did",
                    "rur",
                    "shbid",
                    "csrftoken",
                ]:
                    cookies.append(cookie)

        if not cookies:
            raise ValueError(
                f"No valid Instagram cookies found in {cookies_file}. "
                "Please export cookies from Instagram using a browser extension."
            )

        logger.info("Loaded %d Instagram cookies from %s", len(cookies), cookies_file)

        return {
            "cookies": cookies,
            "source_file": str(cookies_file),
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_session(self, username: str, session_data: dict[str, Any]) -> Path:
        """Encrypt and save session data to disk.

        Args:
            username: Instagram username
            session_data: Session data to encrypt and save

        Returns:
            Path to saved session file
        """
        cipher = self._get_cipher()

        # Serialize session data
        session_json = json.dumps(session_data, default=str)

        # Encrypt
        encrypted_data = cipher.encrypt(session_json.encode())

        # Save to file
        safe_username = self._sanitize_username(username)
        session_file = self.sessions_dir / f"{safe_username}.session"

        with open(session_file, "wb") as f:
            f.write(encrypted_data)

        logger.info("Saved encrypted session for %s to %s", username, session_file)

        return session_file

    def load_session(self, username: str) -> dict[str, Any] | None:
        """Load and decrypt session data from disk.

        Args:
            username: Instagram username

        Returns:
            Decrypted session data, or None if not found
        """
        if not self.encryption_key:
            logger.warning("No encryption key configured, cannot load sessions")
            return None

        cipher = self._get_cipher()
        safe_username = self._sanitize_username(username)
        session_file = self.sessions_dir / f"{safe_username}.session"

        if not session_file.exists():
            logger.warning("No saved session found for %s", username)
            return None

        try:
            # Read encrypted data
            with open(session_file, "rb") as f:
                encrypted_data = f.read()

            # Decrypt
            decrypted_json = cipher.decrypt(encrypted_data)
            session_data = json.loads(decrypted_json)

            logger.info("Loaded encrypted session for %s", username)
            return session_data

        except InvalidToken:
            logger.error("Failed to decrypt session for %s (wrong key?)", username)
            return None
        except Exception as e:
            logger.error("Error loading session for %s: %s", username, e)
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all saved sessions.

        Returns:
            List of session info dictionaries
        """
        sessions = []

        for session_file in self.sessions_dir.glob("*.session"):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)

                # Extract username from filename
                username = session_file.stem

                sessions.append(
                    {
                        "username": username,
                        "file": str(session_file),
                        "created_at": mtime.isoformat(),
                    }
                )
            except Exception as e:
                logger.warning("Error reading session file %s: %s", session_file, e)

        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def delete_session(self, username: str) -> bool:
        """Delete a saved session.

        Args:
            username: Username to delete

        Returns:
            True if deleted, False if not found
        """
        safe_username = self._sanitize_username(username)
        session_file = self.sessions_dir / f"{safe_username}.session"

        if session_file.exists():
            session_file.unlink()
            logger.info("Deleted session for %s", username)
            return True

        return False

    def _sanitize_username(self, username: str) -> str:
        """Sanitize username for use as filename.

        Args:
            username: Raw username

        Returns:
            Sanitized username safe for filenames
        """
        # Remove special characters
        import re

        return re.sub(r'[<>:"/\\|?*]', "_", username)

    def cookies_to_session_dict(self, cookies_data: dict[str, Any]) -> dict[str, Any]:
        """Convert loaded cookies to session dictionary for Instaloader.

        Args:
            cookies_data: Data from load_cookies_from_file

        Returns:
            Session dictionary compatible with Instaloader
        """
        # Extract relevant cookie values
        cookies_dict = {}
        for cookie in cookies_data.get("cookies", []):
            cookies_dict[cookie["name"]] = cookie["value"]

        return {
            "cookies": cookies_dict,
            "loaded_at": cookies_data.get("loaded_at"),
        }

    def validate_session(self, session_data: dict[str, Any]) -> bool:
        """Check if a session is still valid (not expired).

        Args:
            session_data: Session data to validate

        Returns:
            True if session appears valid, False otherwise
        """
        loaded_at = session_data.get("loaded_at")
        if not loaded_at:
            return False

        # Instagram sessions typically last ~1 week
        # Check if loaded within last 7 days
        try:
            loaded_date = datetime.fromisoformat(loaded_at)
            expiry = loaded_date + timedelta(days=7)
            return datetime.now(timezone.utc) < expiry
        except Exception:
            return False
