#!/usr/bin/env python3
import wx

from EDXD.gui.main_window import MainFrame
from EDXD.globals import CFG_FILE, RAW_MATS
from EDXD.model import Model, Tail, Controller, StatusWatcher
from pathlib import Path
import argparse, queue


def main():
    import json, sys
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
    Tail(journal_dir, q).start()
    Controller(q, model).start()

    cfg.setdefault("land", False)
    cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})

    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}
        CFG_FILE.write_text(json.dumps(data, indent=2))

    # ensure defaults even if file is old
    cfg["save"] = _save  # ← make the save-function available

    StatusWatcher(journal_dir / "Status.json", model).start()

    frame = MainFrame(model=model, prefs=cfg)
    frame.Show()

    app.MainLoop()

if __name__ == "__main__":
    main()
