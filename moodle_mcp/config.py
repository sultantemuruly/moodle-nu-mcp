from pathlib import Path

BASE_URL = "https://moodle.nu.edu.kz"
# Outside the repo so the session cookies can never be committed.
STATE_PATH = Path.home() / ".config" / "moodle-mcp" / "storage_state.json"
DOWNLOAD_DIR = Path.home() / "Moodle"
