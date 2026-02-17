"""Entry point for running the collector package as a module."""

from __future__ import annotations

from collector import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
