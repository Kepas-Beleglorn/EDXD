#!/usr/bin/env python3
import wx

from EDXD.gui.main_window import MainFrame
from EDXD.globals import CFG_FILE, RAW_MATS, DEFAULT_WORTHWHILE_THRESHOLD
from EDXD.data_handler.model import Model
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.journal_controller import JournalController
from EDXD.data_handler.status_json_watcher import StatusWatcher
from pathlib import Path
import argparse, queue
# version handling
import sys

def _from_pyproject() -> str | None:
    try:
        try:
            import tomllib  # py311+
        except ModuleNotFoundError:
            import tomli as tomllib
        pyproj = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if not pyproj.exists():
            return None
        data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        return data.get("project", {}).get("version")
    except Exception:
        return None
try:
    from EDXD._version import VERSION as __version__
except Exception:
    __version__ = "0.0.0.0"

def main():
    if "--version" in sys.argv:
        print(__version__)
        return

    import json
    app = wx.App(False)

    cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}
    ap = argparse.ArgumentParser()
    ap.add_argument("--journals", type=Path,
                    help="Path to Saved Games/Frontier Developments/Elite Dangerous")
    args = ap.parse_args()

    if args.journals:
        cfg["journal_dir"] = str(args.journals.expanduser())
        CFG_FILE.write_text(json.dumps(cfg, indent=2))
    # ensure defaults even if file is old
    journal_dir = Path(cfg.get("journal_dir", ""))
    if not journal_dir.is_dir():
        sys.exit("Run once with --journals <Saved Games …>")

    q = queue.Queue()
    model = Model()
    journal_reader = JournalReader(journal_dir, q)
    journal_reader.start()
    journal_controller = JournalController(q, model)
    journal_controller.start()

    cfg.setdefault("land", False)
    cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})
    if "worthwhile_threshold" not in cfg.keys():
        cfg["worthwhile_threshold"] = DEFAULT_WORTHWHILE_THRESHOLD

    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}
        CFG_FILE.write_text(json.dumps(data, indent=2))

    # ensure defaults even if file is old
    cfg["save"] = _save  # ← make the save-function available
    cfg["save"]()

    status_watcher = StatusWatcher(journal_dir / "Status.json", model)
    status_watcher.start()

    frame = MainFrame(model=model, prefs=cfg, journal_reader=journal_reader, journal_controller=journal_controller, status_watcher=status_watcher)
    frame.Show()

    app.MainLoop()

if __name__ == "__main__":
    main()
