"""API blueprint for configuration and status endpoints."""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify

from services import SessionService

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/config/status")
def config_status():
    """Get configuration status for UI."""
    try:
        session_service = SessionService()
        result = session_service.get_config_status()

        if result["success"]:
            return jsonify(
                {
                    "encryption_enabled": result["encryption_enabled"],
                    "downloads_dir": result["downloads_dir"],
                }
            )
        else:
            # Fallback to basic config if service fails
            return jsonify(
                {
                    "encryption_enabled": False,
                    "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
                }
            )
    except Exception as e:
        logger.exception("Error getting config status: %s", e)
        # Fallback to basic config
        return jsonify(
            {
                "encryption_enabled": False,
                "downloads_dir": str(current_app.config.get("SCRAPER_DOWNLOAD_DIR", "")),
            }
        )
