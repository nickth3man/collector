#!/usr/bin/env python
"""Capture post-redesign UI screenshots to docs/ui/after/."""

from __future__ import annotations

from pathlib import Path

import capture_screenshots as base_capture

base_capture.OUTPUT_DIR = Path("docs/ui/after")


if __name__ == "__main__":
    raise SystemExit(base_capture.main())
