"""Tests for SessionService."""

from unittest.mock import Mock, patch

from repositories.settings_repository import SettingsRepository
from services.session_manager import SessionManager
from services.session_service import SessionService


class TestSessionService:
    """Test cases for SessionService."""

    def test_init(self):
        """Test SessionService initialization."""
        session_manager = Mock(spec=SessionManager)
        settings_repo = Mock(spec=SettingsRepository)

        service = SessionService(session_manager, settings_repo)

        assert service.session_manager == session_manager
        assert service.settings_repository == settings_repo

    def test_init_with_defaults(self):
        """Test SessionService initialization with default settings repository."""
        service = SessionService()

        assert service.session_manager is None
        assert service.settings_repository is not None

    @patch("services.session_service.SessionManager")
    def test_upload_session_success(self, mock_manager_class):
        """Test successful session upload."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_cookies_data = {"cookies": [{"name": "ds_user_id", "value": "12345"}]}
        mock_manager.load_cookies_from_file.return_value = mock_cookies_data

        mock_session_file = Mock()
        mock_manager.save_session.return_value = mock_session_file

        service = SessionService(session_manager=mock_manager)
        result = service.upload_session("cookie data", "cookies.txt")

        assert result["success"] is True
        assert result["username"] == "12345"
        assert result["session_file"] == mock_session_file
        assert "uploaded successfully" in result["message"]

    @patch("services.session_service.SessionManager")
    def test_upload_session_invalid_format(self, mock_manager_class):
        """Test session upload with invalid file format."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        service = SessionService(session_manager=mock_manager)
        result = service.upload_session("cookie data", "cookies.json")

        assert result["success"] is False
        assert ".txt format" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_upload_session_no_manager(self, mock_manager_class):
        """Test session upload when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.upload_session("cookie data", "cookies.txt")

        assert result["success"] is False
        assert "Session manager not available" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_upload_session_value_error(self, mock_manager_class):
        """Test session upload when cookies file is invalid."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_cookies_from_file.side_effect = ValueError("Invalid cookies")

        service = SessionService(session_manager=mock_manager)
        result = service.upload_session("invalid cookies", "cookies.txt")

        assert result["success"] is False
        assert result["error"] == "Invalid cookies"

    @patch("services.session_service.SessionManager")
    def test_load_session_success(self, mock_manager_class):
        """Test successful session load."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_session_data = {"username": "testuser", "valid": True}
        mock_manager.load_session.return_value = mock_session_data

        service = SessionService(session_manager=mock_manager)
        result = service.load_session("testuser")

        assert result["success"] is True
        assert result["session_data"] == mock_session_data
        assert result["username"] == "testuser"

    @patch("services.session_service.SessionManager")
    def test_load_session_not_found(self, mock_manager_class):
        """Test loading a session that doesn't exist."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_session.return_value = None

        service = SessionService(session_manager=mock_manager)
        result = service.load_session("nonexistent")

        assert result["success"] is False
        assert "No saved session found" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_load_session_no_manager(self, mock_manager_class):
        """Test loading a session when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.load_session("testuser")

        assert result["success"] is False
        assert "Session manager not available" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_validate_session_success(self, mock_manager_class):
        """Test successful session validation."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.validate_session.return_value = True

        service = SessionService(session_manager=mock_manager)
        result = service.validate_session({"username": "testuser"})

        assert result["success"] is True
        assert result["is_valid"] is True
        assert "Session is valid" in result["message"]

    @patch("services.session_service.SessionManager")
    def test_validate_session_invalid(self, mock_manager_class):
        """Test validating an invalid session."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.validate_session.return_value = False

        service = SessionService(session_manager=mock_manager)
        result = service.validate_session({"username": "testuser"})

        assert result["success"] is True
        assert result["is_valid"] is False
        assert "Session has expired" in result["message"]

    @patch("services.session_service.SessionManager")
    def test_validate_session_no_manager(self, mock_manager_class):
        """Test validating a session when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.validate_session({"username": "testuser"})

        assert result["success"] is False
        assert "Session manager not available" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_list_sessions_success(self, mock_manager_class):
        """Test successful session listing."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_sessions = [
            {"username": "user1", "created_at": "2023-01-01"},
            {"username": "user2", "created_at": "2023-01-02"},
        ]
        mock_manager.list_sessions.return_value = mock_sessions

        service = SessionService(session_manager=mock_manager)
        result = service.list_sessions()

        assert result["success"] is True
        assert result["sessions"] == mock_sessions
        assert result["count"] == 2

    @patch("services.session_service.SessionManager")
    def test_list_sessions_no_manager(self, mock_manager_class):
        """Test listing sessions when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.list_sessions()

        assert result["success"] is False
        assert "Session manager not available" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_delete_session_success(self, mock_manager_class):
        """Test successful session deletion."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.delete_session.return_value = True

        service = SessionService(session_manager=mock_manager)
        result = service.delete_session("testuser")

        assert result["success"] is True
        assert "testuser" in result["message"]
        assert "deleted successfully" in result["message"]

    @patch("services.session_service.SessionManager")
    def test_delete_session_not_found(self, mock_manager_class):
        """Test deleting a session that doesn't exist."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.delete_session.return_value = False

        service = SessionService(session_manager=mock_manager)
        result = service.delete_session("nonexistent")

        assert result["success"] is False
        assert "Session not found" in result["error"]

    @patch("services.session_service.SessionManager")
    def test_delete_session_no_manager(self, mock_manager_class):
        """Test deleting a session when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.delete_session("testuser")

        assert result["success"] is False
        assert "Session manager not available" in result["error"]

    @patch("services.session_service.SettingsRepository")
    @patch("services.session_service.SessionManager")
    def test_get_config_status_with_encryption(self, mock_manager_class, mock_settings_class):
        """Test getting configuration status with encryption enabled."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.encryption_key = "test_key"

        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        mock_setting = Mock()
        mock_setting.value = "/tmp/downloads"
        mock_settings.get_by_key.return_value = mock_setting

        service = SessionService(session_manager=mock_manager, settings_repository=mock_settings)
        result = service.get_config_status()

        assert result["success"] is True
        assert result["encryption_enabled"] is True
        assert result["downloads_dir"] == "/tmp/downloads"

    @patch("services.session_service.SettingsRepository")
    @patch("services.session_service.SessionManager")
    def test_get_config_status_no_encryption(self, mock_manager_class, mock_settings_class):
        """Test getting configuration status with encryption disabled."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.encryption_key = None

        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        service = SessionService(session_manager=mock_manager, settings_repository=mock_settings)
        result = service.get_config_status()

        assert result["success"] is True
        assert result["encryption_enabled"] is False
        assert result["downloads_dir"] is None

    @patch("services.session_service.SessionManager")
    def test_extract_username_from_cookies(self, mock_manager_class):
        """Test extracting username from cookies data."""
        service = SessionService()

        cookies_data = {
            "cookies": [
                {"name": "sessionid", "value": "session123"},
                {"name": "ds_user_id", "value": "user456"},
                {"name": "mid", "value": "mid789"},
            ]
        }

        result = service.extract_username_from_cookies(cookies_data)
        assert result == "user456"

        # Test when no ds_user_id cookie
        cookies_data_no_user = {
            "cookies": [
                {"name": "sessionid", "value": "session123"},
                {"name": "mid", "value": "mid789"},
            ]
        }

        result = service.extract_username_from_cookies(cookies_data_no_user)
        assert result is None

    @patch("services.session_service.SessionManager")
    def test_cookies_to_session_dict(self, mock_manager_class):
        """Test converting cookies to session dictionary."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        cookies_data = {"cookies": [{"name": "test", "value": "value"}]}
        expected_dict = {"cookies_dict": "converted"}
        mock_manager.cookies_to_session_dict.return_value = expected_dict

        service = SessionService(session_manager=mock_manager)
        result = service.cookies_to_session_dict(cookies_data)

        assert result == expected_dict
        mock_manager.cookies_to_session_dict.assert_called_once_with(cookies_data)

    @patch("services.session_service.SessionManager")
    def test_cookies_to_session_dict_no_manager(self, mock_manager_class):
        """Test converting cookies when no session manager is available."""
        service = SessionService(session_manager=None)
        result = service.cookies_to_session_dict({"cookies": []})

        assert result == {}

    @patch("services.session_service.SessionService.load_session")
    @patch("services.session_service.SessionService.validate_session")
    def test_get_session_for_url_success(self, mock_validate, mock_load):
        """Test getting session for URL successfully."""
        mock_session_data = {"username": "testuser", "valid": True}
        mock_load.return_value = {"success": True, "session_data": mock_session_data}
        mock_validate.return_value = {"success": True, "is_valid": True}

        service = SessionService()
        result = service.get_session_for_url("https://www.instagram.com/testuser")

        assert result["success"] is True
        assert result["username"] == "testuser"
        assert result["session_data"] == mock_session_data
        assert result["is_valid"] is True

    @patch("services.session_service.SessionService.load_session")
    def test_get_session_for_url_no_username(self, mock_load):
        """Test getting session for URL with no extractable username."""
        service = SessionService()
        result = service.get_session_for_url("https://www.instagram.com/")

        assert result["success"] is False
        assert "Could not extract username" in result["error"]
        mock_load.assert_not_called()

    @patch("services.session_service.SessionService.load_session")
    @patch("services.session_service.SessionService.validate_session")
    def test_get_session_for_url_session_expired(self, mock_validate, mock_load):
        """Test getting session for URL when session has expired."""
        mock_session_data = {"username": "testuser", "valid": False}
        mock_load.return_value = {"success": True, "session_data": mock_session_data}
        mock_validate.return_value = {"success": True, "is_valid": False}

        service = SessionService()
        result = service.get_session_for_url("https://www.instagram.com/testuser")

        assert result["success"] is False
        assert result["error"] == "Session has expired"

    @patch("services.session_service.SessionService.load_session")
    def test_get_session_for_url_no_session(self, mock_load):
        """Test getting session for URL when no session exists."""
        mock_load.return_value = {"success": False, "error": "No saved session found"}

        service = SessionService()
        result = service.get_session_for_url("https://www.instagram.com/testuser")

        assert result["success"] is False
        assert "No saved session found" in result["error"]
