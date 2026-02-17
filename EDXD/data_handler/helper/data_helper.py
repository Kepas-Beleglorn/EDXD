import inspect
import json
import re
import wx
from datetime import datetime
from pathlib import Path
from typing import Optional

#from fontTools.ttLib.tables.C_P_A_L_ import Color

from EDXD.data_handler.vessel_status import ShipStatus
from EDXD.globals import log_context, logging


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except Exception as e:
        log_context(level=logging.WARN, frame=inspect.currentframe(), e=e)
        return default

def save(path: Path, data):
    try:
        logging.debug(f"{data}\n{json.dumps(data, indent=4)}")
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)

#133 - change sorting of journal files
def _extract_timestamp_from_filename(path: Path) -> Optional[datetime]:
    """
    Extract a datetime from filenames like:
      - Journal.2025-10-26T191647.01.log
      - Journal.201204161359.01.log
      - Journal.210102032116.01.log   (two-digit year -> expand to 2000+YY)

    Returns a datetime if parsing succeeds, otherwise None.
    """
    name = path.name
    m = re.match(r"^Journal\.([^.]+)", name)
    if not m:
        return None
    token = m.group(1)

    # 1) ISO-like with hyphens (e.g. 2025-10-26T191647 or 2025-10-26T19:16:47)
    if "-" in token:
        iso_candidates = [
            "%Y-%m-%dT%H%M%S",
            "%Y-%m-%dT%H%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H%M%S",
            "%Y-%m-%d %H%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",  # date only
        ]
        for fmt in iso_candidates:
            try:
                return datetime.strptime(token, fmt)
            except Exception:
                continue
        # Normalize time digits if necessary (e.g. 2025-10-26T191647 -> 2025-10-26T19:16:47)
        try:
            if "T" in token:
                datepart, timepart = token.split("T", 1)
            elif " " in token:
                datepart, timepart = token.split(" ", 1)
            else:
                datepart, timepart = token, ""
            time_digits = re.sub(r"\D", "", timepart)
            if len(time_digits) >= 6:
                hh = time_digits[0:2]; mm = time_digits[2:4]; ss = time_digits[4:6]
                norm = f"{datepart}T{hh}:{mm}:{ss}"
                return datetime.strptime(norm, "%Y-%m-%dT%H:%M:%S")
            elif len(time_digits) == 4:
                hh = time_digits[0:2]; mm = time_digits[2:4]
                norm = f"{datepart}T{hh}:{mm}"
                return datetime.strptime(norm, "%Y-%m-%dT%H:%M")
        except Exception:
            pass

    # 2) Pure digits: try to interpret based on length
    if token.isdigit():
        token_length = len(token)
        try:
            if token_length == 14:
                # YYYYMMDDHHMMSS
                return datetime.strptime(token, "%Y%m%d%H%M%S")
            elif token_length == 12:
                # Ambiguous: likely either YYYYMMDDHHMM or YYMMDDHHMMSS
                first4 = int(token[:4])
                if 1900 <= first4 <= 2099:
                    # treat as YYYYMMDDHHMM
                    try:
                        return datetime.strptime(token, "%Y%m%d%H%M")
                    except Exception:
                        pass
                # fallback: treat as YYMMDDHHMMSS -> expand to 2000+YY
                yy = int(token[0:2])
                year = 2000 + yy
                month = int(token[2:4])
                day = int(token[4:6])
                hour = int(token[6:8])
                minute = int(token[8:10])
                second = int(token[10:12])
                return datetime(year, month, day, hour, minute, second)
            elif token_length == 10:
                # Could be YYYYMMDDHH or YYMMDDHHMM (treat using heuristics)
                first4 = int(token[:4])
                if 1900 <= first4 <= 2099:
                    # YYYYMMDDHH
                    return datetime.strptime(token, "%Y%m%d%H")
                else:
                    # YYMMDDHHMM -> expand year
                    yy = int(token[0:2]); year = 2000 + yy
                    month = int(token[2:4]); day = int(token[4:6])
                    hour = int(token[6:8]); minute = int(token[8:10])
                    return datetime(year, month, day, hour, minute)
            elif token_length == 8:
                # YYYYMMDD
                return datetime.strptime(token, "%Y%m%d")
            elif token_length == 6:
                # YYMMDD -> expand year
                yy = int(token[0:2]); year = 2000 + yy
                month = int(token[2:4]); day = int(token[4:6])
                return datetime(year, month, day)
        except Exception:
            pass

    # nothing matched
    return None

def get_gravity_from_mass_and_radius(solar_masses: float = 0.0, earth_masses: float = 0.0, radius: float = 0.0) -> float:
    mass = 0
    if solar_masses:
        mass = solar_masses * 1.989 * pow(10, 30)
    if earth_masses:
        mass = earth_masses * 5.972 * pow(10, 24)
    g_base = 6.67430 * pow(10, -11)
    return float(((g_base * mass) / pow(radius, 2))/ 9.80665)

def format_gravity(g_force):
    if abs(g_force) < 1000:
        return f"{g_force:,.2f} g"
    else:
        return f"{g_force:.2e} g"

def get_color_gradient_from_gravity(gravity: float = 0) -> wx.Colour:
    if gravity == 0:
        return wx.Colour(20, 20, 20)

    if 0 < gravity <= 0.8:
        return wx.Colour(150, 255, 150)

    if 0.8 < gravity <= 2.0:
        return wx.Colour(0, 200, 0)

    if 2.0 < gravity <= 2.7:
        return wx.Colour(255, 190, 25)

    if 2.7 < gravity <= 4.0:
        return wx.Colour(255, 150, 25)

    if 4.0 < gravity <= 6.0:
        return wx.Colour(255, 50, 0)

    if 6.0 < gravity <= 20:
        return wx.Colour(200, 0, 0)

    if 20 < gravity:
        return wx.Colour(220, 0, 255)

    return wx.Colour(0, 0, 255)

def latest_journal(folder: Path) -> Optional[Path]:
    """
    Return the chronologically latest Journal.*.log in `folder` based on the timestamp encoded
    in the filename (not filesystem mtime). Supports multiple filename timestamp formats
    including two-digit-year forms (which are interpreted as 2000+YY).
    """
    files = list(folder.glob("Journal.*.log"))
    if not files:
        return None

    parsed = []
    for f in files:
        ts = _extract_timestamp_from_filename(f)
        if ts is None:
            logging.debug(f"Could not parse timestamp from journal filename: {f.name}")
            continue
        parsed.append((ts, f))

    if not parsed:
        # fallback to lexical sort (original behavior)
        files_sorted = sorted(files)
        return files_sorted[-1] if files_sorted else None

    # sort by timestamp and return the latest
    parsed.sort(key=lambda x: x[0])
    return parsed[-1][1]

def parse_utc_isoformat(timestamp: str) -> datetime:
    if timestamp is None:
        return None

    # Convert trailing 'Z' to '+00:00' for compatibility
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    return datetime.fromisoformat(timestamp)

def read_last_timestamp(journal_timestamp_file, new_timestamp):
    ensure_timestamp_file(journal_timestamp_file, new_timestamp)
    try:
        with open(journal_timestamp_file, "r") as f:
            data = json.load(f)
            return data.get("last_timestamp")
    except FileNotFoundError:
        return None
    except json.decoder.JSONDecodeError:
        return None

def update_last_timestamp(journal_timestamp_file, new_timestamp):
    data = {}
    if journal_timestamp_file.exists():
        with open(journal_timestamp_file, "r") as f:
            data = json.load(f)
    data["last_timestamp"] = new_timestamp
    with open(journal_timestamp_file, "w") as f:
        json.dump(data, f, indent=4)

def ensure_timestamp_file(journal_timestamp_file, new_timestamp):
    if not journal_timestamp_file.exists():
        # You can choose any default value for "last_timestamp"
        default_data = {"last_timestamp": new_timestamp}
        with open(journal_timestamp_file, "w") as f:
            json.dump(default_data, f, indent=2)

def read_ship_status(ship_status_file, ship_status):
    ensure_ship_status_file(ship_status_file, ship_status)
    try:
        with open(ship_status_file, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return None
    except json.decoder.JSONDecodeError:
        return None

def update_ship_status(ship_status_file, ship_status: ShipStatus):
    if ship_status_file.exists():
        with open(ship_status_file, "w") as f:
            json.dump(ship_status.to_json(), f, indent=4)

def ensure_ship_status_file(ship_status_file, ship_status):
    if not ship_status_file.exists():
        # You can choose any default value for "last_timestamp"
        default_data = ship_status
        with open(ship_status_file, "w") as f:
            json.dump(default_data, f, indent=2)