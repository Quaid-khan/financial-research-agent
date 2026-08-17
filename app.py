"""QK Researcher Main Entrypoint."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import web.app as web_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"Starting QK Researcher Web UI on port {port}...")
    web_app.run_web_server(port=port)
