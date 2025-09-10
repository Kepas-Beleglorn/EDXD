import json, inspect
from pathlib import Path
from typing import Optional
from EDXD.globals import log_context, logging
from datetime import datetime
# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception as e:
        log_context(level=logging.WARN, frame=inspect.currentframe(), e=e)
        return default

def save(path: Path, data):
    try:
        logging.debug(f"{data}\n{json.dumps(data, indent=4)}")
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)

def latest_journal(folder: Path) -> Optional[Path]:
    files = sorted(folder.glob("Journal.*.log"))
    return files[-1] if files else None

def parse_utc_isoformat(timestamp: str) -> datetime:
    if timestamp is None:
        return None

    # Convert trailing 'Z' to '+00:00' for compatibility
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    return datetime.fromisoformat(timestamp)

def read_last_timestamp(journal_timestamp_file, new_timestamp):
    ensure_timestamp_file(journal_timestamp_file, new_timestamp)
    try:
        with open(journal_timestamp_file, "r") as f:
            data = json.load(f)
            return data.get("last_timestamp")
    except FileNotFoundError:
        return None
    except json.decoder.JSONDecodeError:
        return None

def update_last_timestamp(journal_timestamp_file, new_timestamp):
    data = {}
    if journal_timestamp_file.exists():
        with open(journal_timestamp_file, "r") as f:
            data = json.load(f)
    data["last_timestamp"] = new_timestamp
    with open(journal_timestamp_file, "w") as f:
        json.dump(data, f, indent=4)

def ensure_timestamp_file(journal_timestamp_file, new_timestamp):
    if not journal_timestamp_file.exists():
        # You can choose any default value for "last_timestamp"
        default_data = {"last_timestamp": new_timestamp}
        with open(journal_timestamp_file, "w") as f:
            json.dump(default_data, f, indent=2)