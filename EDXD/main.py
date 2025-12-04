#!/usr/bin/env python3
import argparse
import queue
# version handling
import sys
from pathlib import Path

import wx

from EDXD.data_handler.journal_controller import JournalController
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.model import Model
from EDXD.data_handler.status_json_watcher import StatusWatcher
from EDXD.globals import CFG_FILE, RAW_MATS, DEFAULT_WORTHWHILE_THRESHOLD, DEFAULT_FUEL_LOW_THRESHOLD
from EDXD.gui.main_window import MainFrame


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

# Safely import the runtime font utilities (optional — no hard failure if absent)
try:
    from EDXD.gui.helper import font_utils as _font_utils
except Exception:
    _font_utils = None

from EDXD.edxd_single_instance import SingleInstance
from typing import Optional
_instance: Optional[SingleInstance] = None

def main():
    if "--version" in sys.argv:
        print(__version__)
        return

    # check if another instance of EDXD is already running (working from v0.6.0.0)
    global _instance
    _instance = SingleInstance()
    _instance.acquire_or_exit()

    import json
    app = wx.App(False)
    app.SetAppName("EDXD")
    app.SetVendorName("EDXD")

    # Register embedded fonts for the running process (if the helper is present).
    # This should run before any controls/windows are created so font discovery/fallback works.
    try:
        if _font_utils is not None:
            _font_utils.register_embedded_fonts()
    except Exception:
        # keep startup robust — don't crash if font registration fails
        import logging
        logging.getLogger(__name__).exception("Embedded font registration failed")

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

    if "fuel_low_threshold" not in cfg.keys():
        cfg["fuel_low_threshold"] = DEFAULT_FUEL_LOW_THRESHOLD

    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}
        CFG_FILE.write_text(json.dumps(data, indent=2))

    # ensure defaults even if file is old
    cfg["save"] = _save  # ← make the save-function available
    cfg["save"]()

    status_watcher = StatusWatcher(journal_dir / "Status.json", model)
    status_watcher.start()

    frame = MainFrame(model=model, prefs=cfg, journal_reader=journal_reader, journal_controller=journal_controller, status_watcher=status_watcher)

    # Try to apply the app font/theme using the font_utils helper (if available).
    # This is optional: if font_utils implements apply_app_fonts or set helpers, use them.
    try:
        if _font_utils is not None:
            # If your font_utils provides apply_app_fonts, this will set fonts recursively.
            apply_fn = getattr(_font_utils, "apply_app_fonts", None)
            if callable(apply_fn):
                apply_fn(frame, text_face="Noto Sans", emoji_face="Noto Color Emoji", base_size=10)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Applying app fonts failed")

    frame.Show()

    app.MainLoop()

if __name__ == "__main__":
    main()
