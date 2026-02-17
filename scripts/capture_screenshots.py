#!/usr/bin/env python
"""Capture full-page UI screenshots for key Flask pages.

Behavior:
1. Check whether http://127.0.0.1:5000 is already running.
2. If not, start run_dev.py in the background.
3. Wait until the app is reachable.
4. Use Selenium + ChromeDriver to capture full-page screenshots.
5. Save images to docs/ui/before/ with fixed filenames.
6. Clean up WebDriver and any app process started by this script.
"""

from __future__ import annotations

import base64
import importlib
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any

BASE_URL = "http://127.0.0.1:5000"
OUTPUT_DIR = Path("docs/ui/before")

APP_START_TIMEOUT_SECONDS = 60
APP_POLL_INTERVAL_SECONDS = 1
PAGE_LOAD_TIMEOUT_SECONDS = 30
PAGE_SETTLE_SECONDS = 1

PAGES: list[tuple[str, str]] = [
    ("/", "dashboard.png"),
    ("/browse", "browse.png"),
    ("/preview", "preview.png"),
    ("/history", "history.png"),
    ("/sessions", "sessions.png"),
]


def load_selenium_runtime() -> SimpleNamespace:
    """Import Selenium modules lazily with a clear error if unavailable."""
    try:
        webdriver = importlib.import_module("selenium.webdriver")
        selenium_exceptions = importlib.import_module("selenium.common.exceptions")
        selenium_by = importlib.import_module("selenium.webdriver.common.by")
        selenium_expected_conditions = importlib.import_module(
            "selenium.webdriver.support.expected_conditions"
        )
        selenium_wait = importlib.import_module("selenium.webdriver.support.ui")
    except ModuleNotFoundError as exc:
        raise RuntimeError("Selenium is required. Install it with: uv add selenium") from exc

    return SimpleNamespace(
        webdriver=webdriver,
        TimeoutException=selenium_exceptions.TimeoutException,
        WebDriverException=selenium_exceptions.WebDriverException,
        By=selenium_by.By,
        expected_conditions=selenium_expected_conditions,
        WebDriverWait=selenium_wait.WebDriverWait,
    )


def is_url_reachable(url: str, timeout_seconds: int = 3) -> bool:
    """Return True if URL responds successfully."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            return 200 <= response.status < 400
    except urllib.error.URLError:
        return False


def get_page_access_error(url: str, timeout_seconds: int = 10) -> str | None:
    """Return an error string when page is inaccessible, otherwise None."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            if response.status >= 400:
                return f"HTTP {response.status} for {url}"
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code} for {url}"
    except urllib.error.URLError as exc:
        return f"Network error for {url}: {exc.reason}"

    return None


def start_flask_background_process() -> subprocess.Popen[bytes]:
    """Start the collector app in background."""
    env = os.environ.copy()

    command = [
        sys.executable,
        "-c",
        (
            "from collector import create_app; "
            "app = create_app(); "
            "app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)"
        ),
    ]

    if os.name == "nt":
        return subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def stop_background_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate process and child processes."""
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    try:
        process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def wait_for_app_ready(
    base_url: str, timeout_seconds: int, process: subprocess.Popen[bytes] | None = None
) -> bool:
    """Poll until app becomes reachable or timeout elapses."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            return False

        if is_url_reachable(base_url):
            return True
        time.sleep(APP_POLL_INTERVAL_SECONDS)
    return False


def build_webdriver(selenium_runtime: SimpleNamespace) -> Any:
    """Create a headless Chrome WebDriver.

    Selenium Manager (bundled with Selenium 4.6+) resolves ChromeDriver automatically.
    """
    options = selenium_runtime.webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = selenium_runtime.webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver


def wait_for_page_ready(driver: Any, selenium_runtime: SimpleNamespace) -> None:
    """Wait for DOM ready and body presence."""
    selenium_runtime.WebDriverWait(driver, PAGE_LOAD_TIMEOUT_SECONDS).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    selenium_runtime.WebDriverWait(driver, PAGE_LOAD_TIMEOUT_SECONDS).until(
        selenium_runtime.expected_conditions.presence_of_element_located(
            (selenium_runtime.By.TAG_NAME, "body")
        )
    )
    time.sleep(PAGE_SETTLE_SECONDS)


def save_full_page_screenshot(driver: Any, output_path: Path) -> None:
    """Capture full-page screenshot using Chrome DevTools Protocol with fallback."""
    try:
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        content_size = metrics.get("contentSize", {})
        width = max(int(content_size.get("width", 1920)), 1920)
        height = max(int(content_size.get("height", 1080)), 1080)

        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "mobile": False,
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
            },
        )

        screenshot_b64 = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "captureBeyondViewport": True,
                "fromSurface": True,
            },
        )["data"]
        output_path.write_bytes(base64.b64decode(screenshot_b64))
    except Exception as exc:
        # Fallback for environments where CDP capture is unavailable.
        total_width = int(
            driver.execute_script(
                "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, 1920);"
            )
        )
        total_height = int(
            driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1080);"
            )
        )
        driver.set_window_size(total_width, total_height)
        ok = driver.save_screenshot(str(output_path))
        if not ok:
            raise RuntimeError(f"Failed to save screenshot: {output_path}") from exc
    finally:
        try:
            driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        except Exception:
            pass
        driver.set_window_size(1920, 1080)


def capture_pages(driver: Any, selenium_runtime: SimpleNamespace) -> tuple[list[str], list[str]]:
    """Capture screenshots for all configured pages.

    Returns:
        (errors, warnings)
        - errors: screenshot capture failures
        - warnings: page accessibility issues (e.g., HTTP 404), screenshot still attempted
    """
    errors: list[str] = []
    warnings: list[str] = []

    for route, filename in PAGES:
        url = f"{BASE_URL}{route}"
        output_path = OUTPUT_DIR / filename

        access_error = get_page_access_error(url)
        if access_error is not None:
            warnings.append(access_error)

        try:
            driver.get(url)
            wait_for_page_ready(driver, selenium_runtime)
            save_full_page_screenshot(driver, output_path)
            print(f"Saved screenshot: {output_path}")
        except (
            RuntimeError,
            selenium_runtime.TimeoutException,
            selenium_runtime.WebDriverException,
            OSError,
        ) as exc:
            message = f"{url} -> {exc}"
            errors.append(message)
            print(f"Error capturing {url}: {exc}", file=sys.stderr)

    return errors, warnings


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    selenium_runtime: SimpleNamespace | None = None
    app_process: subprocess.Popen[bytes] | None = None
    app_started_by_script = False
    driver: Any = None

    try:
        selenium_runtime = load_selenium_runtime()

        if is_url_reachable(BASE_URL):
            print("Flask app already running at http://127.0.0.1:5000")
        else:
            print("Flask app not running; starting collector in background...")
            app_process = start_flask_background_process()
            app_started_by_script = True

            if not wait_for_app_ready(BASE_URL, APP_START_TIMEOUT_SECONDS, process=app_process):
                if app_process.poll() is not None:
                    raise RuntimeError(
                        f"Flask process exited early with code {app_process.returncode}."
                    )
                raise RuntimeError("Timed out waiting for Flask app to become ready.")

            print("Flask app is ready.")

        driver = build_webdriver(selenium_runtime)
        errors, warnings = capture_pages(driver, selenium_runtime)

        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        if errors:
            detail = "\n".join(f"- {err}" for err in errors)
            raise RuntimeError(f"Failed to capture one or more pages:\n{detail}")

        print("Successfully captured all screenshots.")
        return 0

    except Exception as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            driver.quit()

        if app_started_by_script and app_process is not None:
            stop_background_process(app_process)
            print("Stopped background Flask process.")


if __name__ == "__main__":
    raise SystemExit(main())
