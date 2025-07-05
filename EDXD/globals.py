import sys
from typing import List
from pathlib import Path
import inspect, functools

def get_app_dir():
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        local_path = Path(sys.executable).parent
    else:
        local_path=Path(__file__).resolve().parent
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
            qualname = fn.__qualname__           # includes outer.<locals>.inner
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


#-----------------------------------------------------------------------
# general paths for storing data
APP_DIR = get_app_dir()
CFG_FILE = APP_DIR/"config.json"
CACHE_DIR  = APP_DIR/"system-data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
ICON_PATH = APP_DIR/"resources/edxd_128.png"  # Normalize path for OS compatibility

#-----------------------------------------------------------------------
# DEBUGGING OPTIONS
DEBUG_MODE = False
DEBUG_PATH = APP_DIR/"debug"
DEBUG_STATUS_JSON = DEBUG_MODE and False

#-----------------------------------------------------------------------
# DEBUGGING OPTIONS
DEFAULT_HEIGHT = 500
DEFAULT_WIDTH = 500

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

#-----------------------------------------------------------------------
# prefix to stringify body_id
BODY_ID_PREFIX = "body_"

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

#-----------------------------------------------------------------------
# Icons for table in main window and detail panels
ICONS = {
    "status_header":    "🎯🖱",
    "status_target":    "🎯",
    "status_selected":  "🖱",
    "scoopable":        "⛽",
    "landable":         "🛬",
    "biosigns":         "🌿",
    "geosigns":         "🌋",
    "value":            "💲",
    "checked":          "✅",
    "in_progress":      "♻️",
    "unknown":          "❓",
    "new_entry":        "🚩"
}
