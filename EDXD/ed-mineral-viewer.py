#!/usr/bin/env python3
from pathlib import Path
import argparse, queue
from model import Model, Tail, Controller
from gui import MainWindow                # imports all sub-widgets

CFG_DIR = Path.home()/".config"/"edmv"
CFG_DIR.mkdir(parents=True, exist_ok=True)
CFG_FILE = CFG_DIR/"config.json"

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

    journal_dir = Path(cfg.get("journal_dir", ""))
    if not journal_dir.is_dir():
        sys.exit("Run once with --journals <Saved Games …>")

    q     = queue.Queue()
    model = Model()
    Tail(journal_dir, q).start()
    Controller(q, model).start()

    from gui import RAW_MATS
    cfg.setdefault("land", False)
    cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})
    
    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}   # drop the fn
        CFG_FILE.write_text(json.dumps(data, indent=2))
        
    # ensure defaults even if file is old
    cfg["save"] = _save               #  ← make the save-function available
    
    from model import StatusWatcher
    StatusWatcher(journal_dir / "Status.json", model).start()   # ← add this

    MainWindow(model, cfg).mainloop()

if __name__ == "__main__":
    main()
