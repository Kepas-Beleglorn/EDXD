import functools
import inspect
import sys
from pathlib import Path
from typing import List


def get_app_dir():
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        local_path = Path(sys.executable).parent
    else:
        local_path = Path(__file__).resolve().parent
    return local_path

import logging

LOG_LEVEL = logging.ERROR

# 1️⃣ Configure the root logger once, ideally at program start
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # No .%f here!
)

def log_call(level=logging.INFO):
    """Logs qualified name plus bound arguments, even for inner functions."""
    def deco(fn):
        logger = logging.getLogger(fn.__module__)
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arglist = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            qualname = fn.__qualname__  # includes outer.<locals>.inner
            logger.log(level, "%s(%s)", qualname, arglist)
            return fn(*args, **kwargs)

        return wrapper

    return deco

def log_context(frame, e, level=logging.DEBUG):
    class_name = inspect.getmodule(frame).__name__
    func_name = frame.f_code.co_name
    arg_info = inspect.getargvalues(frame)
    logging.log(level, f"{'_' * 10}")
    logging.log(level, f"Exception in {class_name}.{func_name} with arguments {arg_info.locals}")
    logging.log(level, f"Exception type: {type(e).__name__}")
    logging.log(level, f"Exception args: {e.args}")
    logging.log(level, f"Exception str: {str(e)}")

# -----------------------------------------------------------------------
# general paths for storing data
APP_DIR = get_app_dir()
# CFG_FILE = APP_DIR / "config.json"
# CACHE_DIR = APP_DIR / "system-data"
CFG_FILE_PATH =  Path("config/") 
CFG_FILE_PATH.mkdir(parents=True, exist_ok=True)
CFG_FILE = CFG_FILE_PATH / "config.json"
# CFG_FILE.touch(exist_ok=True)
CACHE_DIR = Path("cache/")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
# ICON_PATH = APP_DIR/"resources/edxd_128.png"  # Normalize path for OS compatibility
ICON_PNG_B64 = """
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
""".strip()
JOURNAL_TIMESTAMP_FILE = APP_DIR / "edxd_timestamp.json"
SHIP_STATUS_FILE = APP_DIR / "edxd_ship_status.json"

# -----------------------------------------------------------------------
# DEBUGGING OPTIONS
DEBUG_MODE = False
DEBUG_PATH = APP_DIR / "debug"
DEBUG_STATUS_JSON = DEBUG_MODE and True

# -----------------------------------------------------------------------
# ABOUT INFO
APP_TITLE = "EDXD - ED eXploration Dashboard"
GIT_OWNER = "Kepas-Beleglorn"
GIT_REPO = "EDXD"

# -----------------------------------------------------------------------
# DEBUGGING OPTIONS
DEFAULT_HEIGHT = 500
DEFAULT_WIDTH = 500
DEFAULT_HEIGHT_MAIN = 1000
DEFAULT_WIDTH_MAIN = 1500
DEFAULT_HEIGHT_JH = 250
DEFAULT_WIDTH_JH = 800
DEFAULT_HEIGHT_PSPS = 200
DEFAULT_WIDTH_PSPS = 500
DEFAULT_HEIGHT_ABOUT = 322
DEFAULT_WIDTH_ABOUT = 388
DEFAULT_HEIGHT_MINERALS_FILTER = 330
DEFAULT_WIDTH_MINERALS_FILTER = 524
DEFAULT_HEIGHT_PSPS_MANUAL_COORDINATES = 200
DEFAULT_WIDTH_PSPS_MANUAL_COORDINATES = 500
DEFAULT_HEIGHT_ENGINE_STATUS = 280
DEFAULT_WIDTH_ENGINE_STATUS = 400

MIN_HEIGHT = 100
MIN_WIDTH = 200

DEFAULT_POS_X = 500
DEFAULT_POS_Y = 500

RESIZE_MARGIN = 5
SIZE_CTRL_BUTTONS = 24
SIZE_APP_ICON = 20

BTN_HEIGHT = 32
BTN_WIDTH = 192
BTN_MARGIN = 1

DEFAULT_WORTHWHILE_THRESHOLD = 1000000
DEFAULT_FUEL_LOW_THRESHOLD = 10

# -----------------------------------------------------------------------
# prefix to stringify body_id
BODY_ID_PREFIX = "body_"

# ----------------------------------------------------------------------
# vessel identifiers
VESSEL_SHIP = "ship"
VESSEL_SLF = "fighter"
VESSEL_SRV = "SRV"
VESSEL_EV = "EV suit"

# -----------------------------------------------------------------------
# symbol lookup for display in table_view.py
SYMBOL = {
    "antimony": "Sb", "arsenic": "As", "boron": "B", "cadmium": "Cd",
    "carbon": "C", "chromium": "Cr", "germanium": "Ge", "iron": "Fe",
    "lead": "Pb", "manganese": "Mn", "mercury": "Hg", "molybdenum": "Mo",
    "nickel": "Ni", "niobium": "Nb", "phosphorus": "P", "polonium": "Po",
    "rhenium": "Re", "ruthenium": "Ru", "selenium": "Se", "sulphur": "S",
    "technetium": "Tc", "tellurium": "Te", "tin": "Sn", "tungsten": "W",
    "vanadium": "V", "yttrium": "Y", "zinc": "Zn", "zirconium": "Zr",
}

# -----------------------------------------------------------------------
# master material list – relevant for set_mineral_filter.py
RAW_MATS: List[str] = sorted([
    "antimony", "arsenic", "boron", "cadmium",
    "carbon", "chromium", "germanium", "iron",
    "lead", "manganese", "mercury", "molybdenum",
    "nickel", "niobium", "phosphorus", "polonium",
    "rhenium", "ruthenium", "selenium", "sulphur",
    "technetium", "tellurium", "tin", "tungsten",
    "vanadium", "yttrium", "zinc", "zirconium",
])

# -----------------------------------------------------------------------
# Icons for table in main window and detail panels
ICONS = {
    "status_header"         : "🎯🖱",
    "status_target"         : "🎯",
    "status_selected"       : "🖱",
    "scoopable"             : "⛽",
    "landable"              : "🛬",
    "biosigns"              : "🌿",
    "geosigns"              : "🌋",
    "value"                 : "💲",
    "checked"               : "✅",
    "in_progress"           : "♻️",
    "unknown"               : "❓",
    "new_entry"             : "🚩",
    "pinned"                : "📍",
    "worthwhile"            : "💰",
    "mapped"                : "🌐",
    "first_discovered"      : "🥇",
    "first_mapped"          : "🥇",
    "first_footfalled"      : "🥇",
    "previous_discovered"   : "🌑",
    "previous_mapped"       : "🌑",
    "previous_footfalled"   : "🗿",
    "col_first_discovered"  : "🔭",
    "col_first_mapped"      : "🛰️",
    "col_first_footfalled"  : "🕺🏽"
}

# -----------------------------------------------------------------------
# Icons for bearing indicator
def direction_indicator(relative_bearing: float) -> str:
    arrows = [
        "⇑",  # 0°
        "⇗",  # 45°
        "⇒",  # 90°
        "⇘",  # 135°
        "⇓",  # 180°
        "⇙",  # 225°
        "⇐",  # 270°
        "⇖",  # 315°
    ]
    index = int((relative_bearing + 22.5) % 360 // 45)
    return arrows[index]
