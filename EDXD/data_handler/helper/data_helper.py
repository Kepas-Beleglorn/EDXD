import json, inspect
from pathlib import Path
from typing import Optional
from EDXD.globals import log_context, logging
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
