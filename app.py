"""Hugging Face Space & Standard Entrypoint for QK Researcher."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.app import run_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting QK Researcher Web Server on port {port}...")
    run_server(port)
