#!/usr/bin/env python
"""Capture post-redesign UI screenshots to docs/ui/after/."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure sibling scripts are importable when run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capture_screenshots as base_capture  # noqa: E402


if __name__ == "__main__":
    base_capture.OUTPUT_DIR = Path("docs/ui/after")
    raise SystemExit(base_capture.main())
