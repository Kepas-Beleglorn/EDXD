"""
model.py – core logic for ED Mineral Viewer
==========================================

* Body            – simple dataclass-style container
* Model           – thread-safe store of the current system
* Tail            – follows the newest Journal file in real time
* Controller      – consumes events from Tail and updates Model
"""

from __future__ import annotations
import json, threading, time, queue
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# paths (shared with other modules)
# ---------------------------------------------------------------------------
DATA_DIR   = Path(__file__).resolve().parent
CACHE_DIR  = DATA_DIR / "system-data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)        # ensure directory exists

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def _save(path: Path, data):
    path.write_text(json.dumps(data, indent=2))

def latest_journal(folder: Path) -> Optional[Path]:
    files = sorted(folder.glob("Journal.*.log"))
    return files[-1] if files else None

# ---------------------------------------------------------------------------
# simple container
# ---------------------------------------------------------------------------
class Body:
    __slots__ = ("name", "landable", "biosignals", "geosignals", "scan_value", "mapped_value", "materials")

    def __init__(self, name: str,
                 landable: bool,
                 materials: Dict[str, float],
                 biosignals: int = 0,
                 geosignals: int = 0,
                 scan_value: int = 0,
                 mapped_value: int = 0):
        self.name           = name
        self.landable       = landable
        self.biosignals     = biosignals
        self.geosignals     = geosignals
        self.scan_value     = scan_value
        self.mapped_value   = mapped_value
        self.materials      = materials

# ---------------------------------------------------------------------------
# thread-safe data model
# ---------------------------------------------------------------------------
class Model:
    """Keeps the bodies of the *current* system; notifies target listeners."""

    def __init__(self):
        self.lock          = threading.Lock()
        self.system_name   : Optional[str]         = None
        self.system_addr   : Optional[int]         = None
        self.bodies        : Dict[str, Body]       = {}
        self.target_body   : Optional[str]         = None
        self.total_bodies  : Optional[int]         = None
        self._target_cbs   : List = []             # listeners

    # ----- snapshot helpers --------------------------------------------------
    def snapshot_bodies(self) -> Dict[str, Body]:
        with self.lock:
            return dict(self.bodies)

    def snapshot_target(self) -> Optional[Body]:
        with self.lock:
            return self.bodies.get(self.target_body)

    # ----- listeners ---------------------------------------------------------
    def register_target_listener(self, cb):
        """cb(body_name:str) → None"""
        self._target_cbs.append(cb)

    def _fire_target(self, name: str):
        for cb in self._target_cbs:
            cb(name)

    # ----- mutators ----------------------------------------------------------
    def reset_system(self, name: str, address: Optional[int]):
        """Clear all bodies and load cache for the new system (if any)."""
        with self.lock:
            self.system_name   = name
            self.system_addr   = address
            self.bodies.clear()
            self.target_body   = None
            self.total_bodies = None

            cached = _load(CACHE_DIR / f"{address}.json", {})
            # tolerate both legacy list (pre-cache-format) and new dict
            if isinstance(cached, list):
                for n in cached:
                    self.bodies[n] = Body(n, False, {})
            elif isinstance(cached, dict):
                for n, e in cached.items():
                    land = e.get("landable", False) if isinstance(e, dict) else False
                    bio = e.get("biosignals", False) if isinstance(e, dict) else False
                    geo = e.get("geosignals", False) if isinstance(e, dict) else False
                    mats = e.get("materials", {})   if isinstance(e, dict) else {}
                    self.bodies[n] = Body(n, land, mats, bio, geo)

    def update_body(self, name: str, landable: bool, biosignals: int, geosignals: int, materials: Dict[str, float]):
        with self.lock:
            b = self.bodies.get(name, Body(name, landable, {}))
            b.landable = b.landable or landable
            b.biosignals = b.biosignals or biosignals
            b.geosignals = b.geosignals or geosignals
            b.materials.update(materials)
            self.bodies[name] = b
            self._save_cache()

    def set_target(self, body_name: str):
        with self.lock:
            self.target_body = body_name
        self._fire_target(body_name)

    # ----- cache -------------------------------------------------------------
    def _save_cache(self):
        if self.system_addr is None:
            return
        _save(
            CACHE_DIR / f"{self.system_addr}.json",
            {n: {"landable": b.landable, "biosignals": b.biosignals, "geosignals": b.geosignals, "materials": b.materials}
             for n, b in self.bodies.items()},
        )

    def snapshot_total(self) -> Optional[int]:
        with self.lock:
            return self.total_bodies

# ---------------------------------------------------------------------------
# tailer thread – reads the newest Journal file
# ---------------------------------------------------------------------------
class Tail(threading.Thread):
    def __init__(self, folder: Path, out_queue: "queue.Queue[str]"):
        super().__init__(daemon=True)
        self.folder = folder
        self.queue  = out_queue
        self.fp     = None
        self.cur    = None

    def run(self):
        while True:
            if self.fp is None:
                self.cur = latest_journal(self.folder)
                if not self.cur:
                    time.sleep(1)
                    continue
                self.fp = self.cur.open("r", encoding="utf-8")   # start at top

            line = self.fp.readline()
            if line:
                self.queue.put(line)
            else:
                lat = latest_journal(self.folder)
                if lat and lat != self.cur:
                    self.fp.close()
                    self.cur = lat
                    self.fp  = self.cur.open("r", encoding="utf-8")
                else:
                    time.sleep(0.2)

# ---------------------------------------------------------------------------
# controller thread – turns Journal lines into Model updates
# ---------------------------------------------------------------------------
class Controller(threading.Thread):
    def __init__(self, q: "queue.Queue[str]", model: Model):
        super().__init__(daemon=True)
        self.q = q
        self.m = model

    def run(self):
        while True:
            try:
                evt = json.loads(self.q.get())
            except Exception:
                continue

            etype = evt.get("event")

            # ───── jump to a new system ───────────────────────────────
            if etype == "FSDJump":
                self.m.reset_system(evt.get("StarSystem"),
                                    evt.get("SystemAddress"))
                # keep going; there may be Scan events in the same tick

            if etype in ("FSSDiscoveryScan", "FSSAllBodiesFound"):
                self.m.reset_system(evt.get("SystemName"), evt.get("SystemAddress"))
                # immediately create a Body(name, False, {}) for every discovered bodyName
                # so the table shows a row for every body (star, planet, moon, belt…)
                for entry in evt.get("Bodies", []):
                    bn = entry.get("BodyName")
                    if bn and bn not in self.m.bodies:
                        # create with default zero‐values; material % empty
                        self.m.bodies[bn] = Body(bn, False, {})
                self.m.total_bodies = evt.get("BodyCount")

            elif etype == "Scan":
                if self.m.system_name is None:   # first scan in a fresh session
                    self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))

                body_name = evt.get("BodyName")
                mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
                self.m.update_body(body_name, evt.get("Landable", False), 0, 0, mats)

            elif etype == "FSSBodySignals":
                body_name = evt.get("BodyName")
                for signal in evt.get("Signals", []):
                    cbio = 0
                    cgeo = 0
                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        cbio = signal.get("Count")
                        #self.m.bodies[body_name].biosignals = signal.get("Count")
                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        cgeo = signal.get("Count")
                    self.m.update_body(body_name, True, cbio, cgeo, {})

            elif etype == "SAAMaterialsFound":
                body_name = evt.get("BodyName")
                mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
                self.m.update_body(body_name, True, mats)
                self.m.set_target(body_name)

            # --- in-game target changed -----------------------------------
            elif etype in ("FSDTarget", "Target", "SAATarget", "SupercruiseTarget"):
                name = evt.get("Name") or evt.get("BodyName")
                if name:
                    self.m.set_target(name)

# ---------------------------------------------------------------------------
# StatusWatcher – polls Status.json for Destination.Name
# ---------------------------------------------------------------------------
class StatusWatcher(threading.Thread):
    def __init__(self, status_file: Path, model: Model, poll=0.5):
        super().__init__(daemon=True)
        self.path   = status_file
        self.model  = model
        self.poll   = poll
        self.last   = None           # last Destination.Name we saw

    def run(self):
        while True:
            try:
                data = json.loads(self.path.read_text())
                dest = data.get("Destination", {})
                name = dest.get("Name")
                if name and name != self.last:
                    self.last = name
                    self.model.set_target(name)
            except Exception:
                pass            # ignore read/JSON errors
            time.sleep(self.poll)
