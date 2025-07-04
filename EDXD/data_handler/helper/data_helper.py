import json
import logging
from pathlib import Path
from typing import Optional
# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def load(path: Path, default):
    # noinspection PyBroadException
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def save(path: Path, data):
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logging.error(f"Writing {path}")
        logging.error(f"Data {data}")
        logging.error(f"Exception type: {type(e).__name__}")
        logging.error(f"Exception args: {e.args}")
        logging.error(f"Exception str: {str(e)}")

def latest_journal(folder: Path) -> Optional[Path]:
    files = sorted(folder.glob("Journal.*.log"))
    return files[-1] if files else None
