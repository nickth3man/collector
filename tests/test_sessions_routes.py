"""Tests for sessions routes."""

from __future__ import annotations

from io import BytesIO

import pytest


class TestSessionsRoutes:
    """Test cases for session management routes."""

    # ========================================================================
    # GET /sessions tests
    # ========================================================================

    def test_list_sessions_success(self, client, mock_session_service, sample_session, auto_mock_csrf):
        """Test successfully listing sessions."""
        mock_session_service.return_value.list_sessions.return_value = {
            "success": True,
            "sessions": [sample_session]
        }

        response = client.get("/sessions")

        assert response.status_code == 200
        mock_session_service.return_value.list_sessions.assert_called_once()

    def test_list_sessions_empty(self, client, mock_session_service, auto_mock_csrf):
        """Test listing sessions when none exist."""
        mock_session_service.return_value.list_sessions.return_value = {
            "success": True,
            "sessions": []
        }

        response = client.get("/sessions")

        assert response.status_code == 200
        mock_session_service.return_value.list_sessions.assert_called_once()

    def test_list_sessions_service_error(self, client, mock_session_service, auto_mock_csrf):
        """Test listing sessions when service returns error."""
        mock_session_service.return_value.list_sessions.return_value = {
            "success": False,
            "error": "Database error"
        }

        response = client.get("/sessions")

        assert response.status_code == 200
        mock_session_service.return_value.list_sessions.assert_called_once()

    def test_list_sessions_exception(self, client, mock_session_service, auto_mock_csrf):
        """Test listing sessions when service raises exception."""
        mock_session_service.return_value.list_sessions.side_effect = Exception("Service error")

        response = client.get("/sessions", follow_redirects=False)

        assert response.status_code == 302

    # ========================================================================
    # POST /sessions/upload tests
    # ========================================================================

    def test_upload_session_success_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test successful session upload via HTMX."""
        cookies_content = "cookie1=value1\ncookie2=value2"
        cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

        mock_session_service.return_value.upload_session.return_value = {
            "success": True,
            "username": "testuser"
        }

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": cookies_file},
            headers={"HX-Request": "true"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 200
        assert b"success" in response.data.lower() or b"uploaded" in response.data.lower()
        mock_session_service.return_value.upload_session.assert_called_once()

    def test_upload_session_success_regular(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test successful session upload via regular request."""
        cookies_content = "cookie1=value1\ncookie2=value2"
        cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

        mock_session_service.return_value.upload_session.return_value = {
            "success": True,
            "username": "testuser"
        }

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": cookies_file},
            follow_redirects=False
        )

        assert response.status_code == 302

    def test_upload_session_no_file_htmx(self, client, auto_mock_csrf):
        """Test upload with no file uploaded via HTMX."""
        response = client.post(
            "/sessions/upload",
            data={},
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 400
        assert b"no file" in response.data.lower()

    def test_upload_session_no_file_regular(self, client, auto_mock_csrf):
        """Test upload with no file uploaded via regular request."""
        response = client.post(
            "/sessions/upload",
            data={},
            follow_redirects=False
        )

        assert response.status_code == 302

    def test_upload_session_empty_filename_htmx(self, client, auto_mock_csrf):
        """Test upload with empty filename via HTMX."""
        empty_file = (BytesIO(b""), "")

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": empty_file},
            headers={"HX-Request": "true"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 400
        assert b"no file" in response.data.lower() or b"selected" in response.data.lower()

    def test_upload_session_wrong_extension_htmx(self, client, auto_mock_csrf):
        """Test upload with wrong file extension via HTMX."""
        wrong_file = (BytesIO(b"content"), "cookies.json")

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": wrong_file},
            headers={"HX-Request": "true"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 400
        assert b".txt" in response.data.lower()

    def test_upload_session_service_error_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test upload when service returns error via HTMX."""
        cookies_content = "cookie1=value1"
        cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

        mock_session_service.return_value.upload_session.return_value = {
            "success": False,
            "error": "Invalid cookies format"
        }

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": cookies_file},
            headers={"HX-Request": "true"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 400
        assert b"invalid cookies format" in response.data.lower()

    def test_upload_session_exception_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test upload when service raises exception via HTMX."""
        cookies_content = "cookie1=value1"
        cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

        mock_session_service.return_value.upload_session.side_effect = Exception("Processing error")

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": cookies_file},
            headers={"HX-Request": "true"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 500
        assert b"failed to upload" in response.data.lower()

    def test_upload_session_missing_csrf(self, client):
        """Test upload without CSRF token."""
        cookies_content = "cookie1=value1"
        cookies_file = (BytesIO(cookies_content.encode()), "cookies.txt")

        response = client.post(
            "/sessions/upload",
            data={"cookies_file": cookies_file},
        )

        assert response.status_code == 403

    # ========================================================================
    # POST /sessions/<username>/delete tests
    # ========================================================================

    def test_delete_session_success_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test successful session deletion via HTMX."""
        mock_session_service.return_value.delete_session.return_value = {
            "success": True
        }

        response = client.post(
            "/sessions/testuser/delete",
            data={},
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 204
        assert response.data == b""
        mock_session_service.return_value.delete_session.assert_called_once_with("testuser")

    def test_delete_session_success_regular(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test successful session deletion via regular request."""
        mock_session_service.return_value.delete_session.return_value = {
            "success": True
        }

        response = client.post(
            "/sessions/testuser/delete",
            data={},
            follow_redirects=False
        )

        assert response.status_code == 302

    def test_delete_session_not_found_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test deleting non-existent session via HTMX."""
        mock_session_service.return_value.delete_session.return_value = {
            "success": False,
            "error": "Session not found"
        }

        response = client.post(
            "/sessions/nonexistent/delete",
            data={},
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 404

    def test_delete_session_not_found_regular(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test deleting non-existent session via regular request."""
        mock_session_service.return_value.delete_session.return_value = {
            "success": False,
            "error": "Session not found"
        }

        response = client.post(
            "/sessions/nonexistent/delete",
            data={},
            follow_redirects=False
        )

        assert response.status_code == 302

    def test_delete_session_exception_htmx(
        self, client, mock_session_service, auto_mock_csrf
    ):
        """Test delete when service raises exception via HTMX."""
        mock_session_service.return_value.delete_session.side_effect = Exception("Database error")

        response = client.post(
            "/sessions/testuser/delete",
            data={},
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 500
        assert b"failed to delete" in response.data.lower()

    def test_delete_session_missing_csrf(self, client):
        """Test delete without CSRF token."""
        response = client.post("/sessions/testuser/delete")

        assert response.status_code == 403
