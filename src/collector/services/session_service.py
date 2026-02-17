"""Session service for managing Instagram sessions.

This service wraps the SessionManager and provides structured outputs
suitable for controller integration.
"""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from ..repositories.settings_repository import SettingsRepository
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing Instagram sessions."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        settings_repository: SettingsRepository | None = None,
    ) -> None:
        """Initialize the session service.

        Args:
            session_manager: Session manager instance
            settings_repository: Repository for settings operations
        """
        if session_manager:
            self.session_manager = session_manager
        else:
            try:
                config_dir = Path(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "./downloads"))
                encryption_key = current_app.config.get("SCRAPER_SESSION_KEY")
                self.session_manager = SessionManager(config_dir=config_dir, encryption_key=encryption_key)
            except RuntimeError:
                self.session_manager = None

        self.settings_repository = settings_repository or SettingsRepository()

    def upload_session(self, cookies_file_content: str, filename: str) -> dict[str, Any]:
        """Upload a cookies.txt file to create a session.

        Args:
            cookies_file_content: Content of the cookies.txt file
            filename: Original filename of the uploaded file

        Returns:
            Dictionary with upload result
        """
        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        if not filename.endswith(".txt"):
            return {"success": False, "error": "File must be .txt format (cookies.txt)"}

        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
                tmp.write(cookies_file_content)
                tmp_path = Path(tmp.name)

            # Load cookies from file
            cookies_data = self.session_manager.load_cookies_from_file(tmp_path)

            # Create a username/session identifier from the cookies
            username = None
            for cookie in cookies_data.get("cookies", []):
                if cookie["name"] == "ds_user_id":
                    # ds_user_id contains username info
                    username = cookie["value"]
                    break

            if not username:
                # Generate a session ID from timestamp
                username = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Save encrypted session
            session_dict = {
                "username": username,
                "cookies": cookies_data["cookies"],
                "source_file": filename,
            }
            session_file = self.session_manager.save_session(username, session_dict)

            # Clean up temp file
            tmp_path.unlink()

            logger.info("Session uploaded successfully for username: %s", username)
            return {
                "success": True,
                "username": username,
                "session_file": str(session_file),
                "message": "Session uploaded successfully",
            }

        except ValueError as e:
            logger.error("Error uploading session: %s", e)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Error uploading session: %s", e)
            return {"success": False, "error": f"Failed to upload session: {str(e)}"}

    def load_session(self, username: str) -> dict[str, Any]:
        """Load and decrypt session data from disk.

        Args:
            username: Instagram username

        Returns:
            Dictionary with load result
        """
        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        try:
            session_data = self.session_manager.load_session(username)
            if not session_data:
                return {"success": False, "error": f"No saved session found for {username}"}

            return {"success": True, "session_data": session_data, "username": username}

        except Exception as e:
            logger.exception("Error loading session: %s", e)
            return {"success": False, "error": f"Failed to load session: {str(e)}"}

    def validate_session(self, session_data: dict[str, Any]) -> dict[str, Any]:
        """Check if a session is still valid (not expired).

        Args:
            session_data: Session data to validate

        Returns:
            Dictionary with validation result
        """
        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        try:
            is_valid = self.session_manager.validate_session(session_data)
            return {
                "success": True,
                "is_valid": is_valid,
                "message": "Session is valid" if is_valid else "Session has expired",
            }

        except Exception as e:
            logger.exception("Error validating session: %s", e)
            return {"success": False, "error": f"Failed to validate session: {str(e)}"}

    def list_sessions(self) -> dict[str, Any]:
        """List all saved sessions.

        Returns:
            Dictionary with list result
        """
        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        try:
            sessions = self.session_manager.list_sessions()
            return {"success": True, "sessions": sessions, "count": len(sessions)}

        except Exception as e:
            logger.exception("Error listing sessions: %s", e)
            return {"success": False, "error": f"Failed to list sessions: {str(e)}"}

    def delete_session(self, username: str) -> dict[str, Any]:
        """Delete a saved session.

        Args:
            username: Username to delete

        Returns:
            Dictionary with delete result
        """
        if not self.session_manager:
            return {"success": False, "error": "Session manager not available"}

        try:
            deleted = self.session_manager.delete_session(username)
            if deleted:
                return {"success": True, "message": f"Session for {username} deleted successfully"}
            else:
                return {"success": False, "error": f"Session not found for {username}"}

        except Exception as e:
            logger.exception("Error deleting session: %s", e)
            return {"success": False, "error": f"Failed to delete session: {str(e)}"}

    def get_config_status(self) -> dict[str, Any]:
        """Get configuration status for UI.

        Returns:
            Dictionary with configuration status
        """
        try:
            # Get encryption status from settings or session manager
            encryption_enabled = False
            if self.session_manager and self.session_manager.encryption_key:
                encryption_enabled = True

            # Get download directory from settings
            download_dir = None
            if self.settings_repository:
                download_dir_setting = self.settings_repository.get_by_key("download_dir")
                if download_dir_setting:
                    download_dir = download_dir_setting.value

            return {
                "success": True,
                "encryption_enabled": encryption_enabled,
                "downloads_dir": download_dir,
                "message": "Configuration status retrieved successfully",
            }

        except Exception as e:
            logger.exception("Error getting config status: %s", e)
            return {"success": False, "error": f"Failed to get configuration status: {str(e)}"}

    def extract_username_from_cookies(self, cookies_data: dict[str, Any]) -> str | None:
        """Extract username from cookies data.

        Args:
            cookies_data: Cookies data from load_cookies_from_file

        Returns:
            Username if found, None otherwise
        """
        for cookie in cookies_data.get("cookies", []):
            if cookie["name"] == "ds_user_id":
                return cookie["value"]
        return None

    def cookies_to_session_dict(self, cookies_data: dict[str, Any]) -> dict[str, Any]:
        """Convert loaded cookies to session dictionary for Instaloader.

        Args:
            cookies_data: Data from load_cookies_from_file

        Returns:
            Session dictionary compatible with Instaloader
        """
        if not self.session_manager:
            return {}

        return self.session_manager.cookies_to_session_dict(cookies_data)

    def get_session_for_url(self, url: str) -> dict[str, Any]:
        """Get session for Instagram URL if available.

        Args:
            url: Instagram URL

        Returns:
            Dictionary with session result
        """
        import re

        # Extract username from URL
        match = re.search(r"instagram\.com/([^/?]+)", url)
        if not match:
            return {"success": False, "error": "Could not extract username from URL"}

        username = match.group(1)
        session_result = self.load_session(username)

        if not session_result["success"]:
            return session_result

        # Validate session
        validation_result = self.validate_session(session_result["session_data"])

        if not validation_result["success"]:
            return validation_result

        if not validation_result["is_valid"]:
            return {"success": False, "error": "Session has expired"}

        return {
            "success": True,
            "username": username,
            "session_data": session_result["session_data"],
            "is_valid": True,
        }
