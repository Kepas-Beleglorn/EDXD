import json
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
    path.write_text(json.dumps(data, indent=2))

def latest_journal(folder: Path) -> Optional[Path]:
    files = sorted(folder.glob("Journal.*.log"))
    return files[-1] if files else None
