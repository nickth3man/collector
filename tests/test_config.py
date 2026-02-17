"""Unit tests for configuration settings."""

from __future__ import annotations

import os
from unittest import mock

from collector.config.settings import Config


class TestConfigValidationConstants:
    """Test that validation constants are defined correctly."""

    def test_constants_exist_and_have_correct_values(self) -> None:
        """Test that validation constants are defined with correct values."""
        assert Config.MIN_CONCURRENT_JOBS == 1
        assert Config.MAX_CONCURRENT_JOBS == 10
        assert Config.MIN_DISK_WARNING_MB == 100
        assert Config.DEFAULT_DISK_WARNING_MB == 1024

    def test_constants_have_correct_types(self) -> None:
        """Test that all constants are integers."""
        assert isinstance(Config.MIN_CONCURRENT_JOBS, int)
        assert isinstance(Config.MAX_CONCURRENT_JOBS, int)
        assert isinstance(Config.MIN_DISK_WARNING_MB, int)
        assert isinstance(Config.DEFAULT_DISK_WARNING_MB, int)


class TestConcurrentJobsValidation:
    """Test concurrent jobs validation uses constants."""

    def test_concurrent_jobs_below_minimum_fails(self) -> None:
        """Test that validation fails when below MIN_CONCURRENT_JOBS."""
        with mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", Config.MIN_CONCURRENT_JOBS - 1):
            errors = Config.validate()
            assert any("SCRAPER_MAX_CONCURRENT" in e and "must be between" in e for e in errors)

    def test_concurrent_jobs_at_minimum_passes(self) -> None:
        """Test that validation passes at MIN_CONCURRENT_JOBS."""
        with mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", Config.MIN_CONCURRENT_JOBS):
            errors = Config.validate()
            assert not any("SCRAPER_MAX_CONCURRENT" in e for e in errors)

    def test_concurrent_jobs_at_maximum_passes(self) -> None:
        """Test that validation passes at MAX_CONCURRENT_JOBS."""
        with mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", Config.MAX_CONCURRENT_JOBS):
            errors = Config.validate()
            assert not any("SCRAPER_MAX_CONCURRENT" in e for e in errors)

    def test_concurrent_jobs_above_maximum_fails(self) -> None:
        """Test that validation fails when above MAX_CONCURRENT_JOBS."""
        with mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", Config.MAX_CONCURRENT_JOBS + 1):
            errors = Config.validate()
            assert any("SCRAPER_MAX_CONCURRENT" in e and "must be between" in e for e in errors)

    def test_error_message_includes_constant_values(self) -> None:
        """Test that error messages include the actual constant values."""
        with mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", 0):
            errors = Config.validate()
            error_msg = next(e for e in errors if "SCRAPER_MAX_CONCURRENT" in e)
            assert str(Config.MIN_CONCURRENT_JOBS) in error_msg
            assert str(Config.MAX_CONCURRENT_JOBS) in error_msg


class TestDiskWarningValidation:
    """Test disk warning validation uses constants."""

    def test_disk_warning_below_minimum_fails(self) -> None:
        """Test that validation fails when below MIN_DISK_WARNING_MB."""
        with mock.patch.object(Config, "SCRAPER_DISK_WARN_MB", Config.MIN_DISK_WARNING_MB - 1):
            errors = Config.validate()
            assert any("SCRAPER_DISK_WARN_MB" in e and "should be at least" in e for e in errors)

    def test_disk_warning_at_minimum_passes(self) -> None:
        """Test that validation passes at MIN_DISK_WARNING_MB."""
        with mock.patch.object(Config, "SCRAPER_DISK_WARN_MB", Config.MIN_DISK_WARNING_MB):
            errors = Config.validate()
            assert not any("SCRAPER_DISK_WARN_MB" in e for e in errors)

    def test_error_message_includes_constant_value(self) -> None:
        """Test that error message includes the actual constant value."""
        with mock.patch.object(Config, "SCRAPER_DISK_WARN_MB", 50):
            errors = Config.validate()
            error_msg = next(e for e in errors if "SCRAPER_DISK_WARN_MB" in e)
            assert str(Config.MIN_DISK_WARNING_MB) in error_msg


class TestDefaultDiskWarningValue:
    """Test that default disk warning value uses the constant."""

    def test_default_value_matches_constant(self) -> None:
        """Test that SCRAPER_DISK_WARN_MB defaults to DEFAULT_DISK_WARNING_MB."""
        # Temporarily remove environment variable
        original_value = os.environ.pop("SCRAPER_DISK_WARN_MB", None)

        try:
            # Re-import to pick up default
            from importlib import reload

            import collector.config.settings

            reload(collector.config.settings)

            from collector.config.settings import Config as ConfigReloaded

            assert ConfigReloaded.SCRAPER_DISK_WARN_MB == ConfigReloaded.DEFAULT_DISK_WARNING_MB
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["SCRAPER_DISK_WARN_MB"] = original_value


class TestValidationIntegration:
    """Integration tests for validation using constants."""

    def test_validation_with_all_constants_at_boundaries(self) -> None:
        """Test validation with all settings at their constant boundaries."""
        with (
            mock.patch.object(Config, "SCRAPER_MAX_CONCURRENT", Config.MIN_CONCURRENT_JOBS),
            mock.patch.object(Config, "SCRAPER_DISK_WARN_MB", Config.MIN_DISK_WARNING_MB),
        ):
            errors = Config.validate()
            assert not any(
                "SCRAPER_MAX_CONCURRENT" in e or "SCRAPER_DISK_WARN_MB" in e for e in errors
            )

    def test_constants_maintain_logical_consistency(self) -> None:
        """Test that constants maintain logical relationships."""
        assert Config.MIN_CONCURRENT_JOBS < Config.MAX_CONCURRENT_JOBS
        assert Config.MIN_DISK_WARNING_MB > 0
        assert Config.DEFAULT_DISK_WARNING_MB >= Config.MIN_DISK_WARNING_MB
