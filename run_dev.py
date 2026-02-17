#!/usr/bin/env python
"""Development server runner for the Flask application."""

import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent
template_dir = project_root / "templates"
static_dir = project_root / "static"

# Set the template and static directories in environment
os.environ["FLASK_TEMPLATE_FOLDER"] = str(template_dir)
os.environ["FLASK_STATIC_FOLDER"] = str(static_dir)

from collector import create_app

app = create_app()

# Ensure Flask knows where to find templates and static files
app.template_folder = str(template_dir)
app.static_folder = str(static_dir)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)