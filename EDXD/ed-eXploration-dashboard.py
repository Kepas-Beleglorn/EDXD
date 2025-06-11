#!/usr/bin/env python3
from pathlib import Path
import argparse, queue

from EDXD.gobal_constants import CFG_FILE
from EDXD.gui.helper.theme_handler import set_icon
from EDXD.model import Model, Tail, Controller, StatusWatcher
from EDXD.gui import MainWindow, RAW_MATS                # imports all sub-widgets

def main():
    import json, sys
    cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}
    ap = argparse.ArgumentParser()
    ap.add_argument("--journals", type=Path,
                    help="Path to Saved Games/Frontier Developments/Elite Dangerous")
    args = ap.parse_args()

    if args.journals:
        cfg["journal_dir"] = str(args.journals.expanduser())
        CFG_FILE.write_text(json.dumps(cfg, indent=2))
    # ensure defaults even if file is old
    print(CFG_FILE)
    journal_dir = Path(cfg.get("journal_dir", ""))
    if not journal_dir.is_dir():
        sys.exit("Run once with --journals <Saved Games …>")

    q     = queue.Queue()
    model = Model()
    Tail(journal_dir, q).start()
    Controller(q, model).start()

    cfg.setdefault("land", False)
    cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})
    
    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}   # drop the fn
        CFG_FILE.write_text(json.dumps(data, indent=2))
        
    # ensure defaults even if file is old
    cfg["save"] = _save               #  ← make the save-function available
    
    StatusWatcher(journal_dir / "Status.json", model).start()   # ← add this

    mw = MainWindow(model, cfg)
    set_icon(mw)
    mw.mainloop()

if __name__ == "__main__":
    main()
