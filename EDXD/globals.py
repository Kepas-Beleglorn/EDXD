import sys
from typing import List
from pathlib import Path

def get_app_dir():
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        local_path = Path(sys.executable).parent
    else:
        local_path=Path(__file__).resolve().parent
    return local_path


import logging
from datetime import timezone, datetime

# 1️⃣ Configure the root logger once, ideally at program start
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S%z",          # ISO-ish, includes timezone offset
)

#-----------------------------------------------------------------------
# general paths for storing data
APP_DIR = get_app_dir()
CFG_FILE = APP_DIR/"config.json"
CACHE_DIR  = APP_DIR/"system-data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
ICON_PATH = APP_DIR/"resources/edxd_16.png"  # Normalize path for OS compatibility

DEFAULT_HEIGHT = 500
DEFAULT_WIDTH = 500

MIN_HEIGHT = 100
MIN_WIDTH = 200

DEFAULT_POS_X = 500
DEFAULT_POS_Y = 500

RESIZE_MARGIN = 5

#-----------------------------------------------------------------------
# symbol lookup for display in table_view.py
SYMBOL = {
    "antimony":   "Sb", "arsenic":    "As", "boron":     "B",  "cadmium": "Cd",
    "carbon":     "C",  "chromium":   "Cr", "germanium": "Ge", "iron": "Fe",
    "lead":       "Pb", "manganese":  "Mn", "mercury":   "Hg", "molybdenum": "Mo",
    "nickel":     "Ni", "niobium":    "Nb", "phosphorus":"P",  "polonium": "Po",
    "rhenium":    "Re", "ruthenium":  "Ru", "selenium":  "Se", "sulphur": "S",
    "technetium":"Tc", "tellurium":  "Te", "tin":       "Sn","tungsten":"W",
    "vanadium":   "V",  "yttrium":    "Y",  "zinc":      "Zn","zirconium":"Zr",
}

#-----------------------------------------------------------------------
# master material list – relevant for set_mineral_filter.py
RAW_MATS: List[str] = sorted([
    "antimony",  "arsenic",   "boron",  "cadmium",
    "carbon",    "chromium",  "germanium", "iron",
    "lead",      "manganese", "mercury", "molybdenum",
    "nickel",    "niobium",   "phosphorus", "polonium",
    "rhenium",   "ruthenium", "selenium",   "sulphur",
    "technetium","tellurium", "tin",    "tungsten",
    "vanadium",  "yttrium",   "zinc", "zirconium",
])