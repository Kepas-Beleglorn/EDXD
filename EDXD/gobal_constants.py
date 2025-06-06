from pathlib import Path
from typing import List
import os

#-----------------------------------------------------------------------
# general paths for storing data
APP_DIR = Path(__file__).resolve().parent
CFG_FILE = APP_DIR/"config.json"
CACHE_DIR  = APP_DIR / "system-data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

#-----------------------------------------------------------------------
# Data for theme_handler
# Centralized theme colors
BG = "#121212"      # background
FG = "#ff9a00"      # orange foreground/text
ACC = "#ff9a33"     # accent (same as FG)
HBG = "#433322"     # hover background
BDC = "#aa7700"     # border color for buttons

ICON_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'edxd_16.png'))  # Normalize path for OS compatibility

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