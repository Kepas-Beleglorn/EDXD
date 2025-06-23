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
from EDXD.body_appraiser import appraise_body

# ---------------------------------------------------------------------------
# paths (shared with other modules)
# ---------------------------------------------------------------------------
from EDXD.globals import CACHE_DIR
from EDXD.globals import logging
import inspect, functools

def log_call(level=logging.INFO):
    """Decorator that logs function name and bound arguments."""
    def decorator(fn):
        logger = logging.getLogger(fn.__module__)   # one logger per module
        sig = inspect.signature(fn)                 # capture once, not on every call

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arg_str = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            logger.log(level, "%s(%s)", fn.__name__, arg_str)
            return fn(*args, **kwargs)

        return wrapper
    return decorator

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _load(path: Path, default):
    # noinspection PyBroadException
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
    __slots__ = ("name", "landable", "biosignals", "geosignals",
                 "estimated_value", "materials",
                 "bio_found", "geo_found", "distance")

    def __init__(self,
                 materials:         Dict[str, float],
                 name:              str,
                 landable:          bool,
                 distance:          int = 0,
                 bio_found:         Dict[str, int] | None = None,
                 geo_found:         Dict[str, bool] | None = None,
                 biosignals:        int = 0,
                 geosignals:        int = 0,
                 estimated_value:   int = 0):

        self.name               = name
        self.distance           = distance
        self.landable           = landable
        self.biosignals         = biosignals
        self.geosignals         = geosignals
        self.estimated_value    = estimated_value
        self.materials          = materials
        self.bio_found          = bio_found or {}    # { biosign name -> scans_done }         e.g. {"Bacterium Bullaris":2}
        self.geo_found          = geo_found or {}    # { "volcanism-01": True … }             True once SRV scanned

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
    #@log_call()
    def reset_system(self, name: str, address: Optional[int]):
        """Clear all bodies and load cached system if available."""
        with self.lock:
            self.system_name = name
            self.system_addr = address
            self.bodies.clear()
            self.target_body = None

            cached = _load(CACHE_DIR / f"{address}.json", {})
            # Current format: { "total_bodies": int,
            #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
            if isinstance(cached, dict):
                # reload total count
                #self.total_bodies = cached.get("total_bodies", None)
                body_map = cached.get("bodies", {})
                for n, e in body_map.items():
                    distance = e.get("distance", 0)
                    land = e.get("landable", False)
                    bio = e.get("biosignals", 0)
                    geo = e.get("geosignals", 0)
                    mats = e.get("materials", {})
                    bio_dict = e.get("bio_found", {})
                    geo_dict = e.get("geo_found", {})
                    estimated_value = e.get("estimated_value", 0)
                    self.bodies[n] = Body(name=n, distance=distance, landable=land, materials=mats, biosignals=bio, geosignals=geo, bio_found=bio_dict, geo_found=geo_dict, estimated_value=estimated_value)
                logging.info(f"Cached instance: [{self.total_bodies}] {cached}")

    def update_body(self, name: str, distance: int, landable: bool, biosignals: int, geosignals: int, materials: Dict[str, float], scandata):
        with self.lock:
            b = self.bodies.get(name, Body(name=name, landable=landable, materials={}))
            b.distance = b.distance or distance
            b.landable = b.landable or landable
            b.biosignals = b.biosignals or biosignals
            b.geosignals = b.geosignals or geosignals
            b.materials.update(materials)
            if scandata is not None:
                b.estimated_value = appraise_body(body_info=scandata, just_scanned_value=False)
            self.bodies[name] = b
            self._save_cache()

    def set_target(self, body_name: str):
        with self.lock:
            self.target_body = body_name
        self._fire_target(body_name)

    # ----- cache -------------------------------------------------------------
    def _save_cache(self):
        """Persist bodies *and* total_bodies to disk."""
        if self.system_addr is None:
            return

        # Current format: { "total_bodies": int,
        #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
        data = {
            "total_bodies": self.total_bodies,
            "bodies": {
                n: {
                    "landable": b.landable,
                    "distance": b.distance,
                    "biosignals": b.biosignals,
                    "geosignals": b.geosignals,
                    "materials": b.materials,
                    "bio_found": b.bio_found,
                    "geo_found": b.geo_found,
                    "estimated_value": b.estimated_value,
                }
                for n, b in self.bodies.items()
            },
        }
        _save(CACHE_DIR / f"{self.system_addr}.json", data)
    #@log_call()
    def snapshot_total(self) -> Optional[int]:
        with self.lock:
            return self.total_bodies

    def load_cached_total_bodies(self, system_address: int = None):
        if system_address is None:
            pass
        cached = _load(CACHE_DIR / f"{self.system_addr}.json", {})
        self.total_bodies = cached.get("total_bodies", None)

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
            # noinspection PyBroadException
            try:
                evt = json.loads(self.q.get())
            except Exception:
                continue

            etype = evt.get("event")
            # ───── jump to a new system ───────────────────────────────
            # In Controller.run()
            if etype == "FSDJump":
                self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))

            elif etype in ("FSSDiscoveryScan", "FSSAllBodiesFound"):
                # Now update bodies/count
                for entry in evt.get("Bodies", []):
                    bn = entry.get("BodyName")
                    if bn and bn not in self.m.bodies:
                        self.m.bodies[bn] = Body(name=bn, landable=False, materials={})
                if evt.get("BodyCount") is not None:
                    self.m.total_bodies = evt.get("BodyCount")

            # ── on-foot DNA sample or SRV organic scan ─────────────────────
            elif etype in ("ExobiologySample", "OrganicScan"):
                body = evt.get("BodyName")  # present in Odyssey 4.0+
                genus = evt.get("Genus") or evt.get("Species")  # 4.1 uses "Species"
                if body and genus:
                    b = self.m.bodies.setdefault(body, Body(name=body, landable=False, materials={}))
                    b.bio_found[genus] = min(b.bio_found.get(genus, 0) + 1, 3)

            # ── SRV geology scan (CodexEntry, but not if IsNewDiscovery=false) ───
            elif etype == "CodexEntry" and evt.get("Category") == "$Codex_Category_Geology;":
                body = evt.get("BodyName")
                site = evt.get("Name") or evt.get("EntryID")
                if body and site:
                    b = self.m.bodies.setdefault(body, Body(name=body, landable=False, materials={}))
                    b.geo_found[site] = True

            elif etype == "Scan":
                if self.m.system_name is None:   # first scan in a fresh session
                    self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))
                distance = evt.get("DistanceFromArrivalLS")
                body_name = evt.get("BodyName")
                mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
                self.m.update_body(name=body_name, landable=evt.get("Landable", False), biosignals=0, geosignals=0, materials=mats, scandata=evt, distance=distance)

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
                    if body_name in self.m.bodies.keys():
                        self.m.update_body(name=body_name, landable=True, biosignals=cbio, geosignals=cgeo, distance=self.m.bodies[body_name].distance, materials=self.m.bodies[body_name].materials, scandata={
                            })
                    else:
                        self.m.update_body(name=body_name, landable=True, biosignals=cbio, geosignals=cgeo,
                                           distance=0,
                                           materials={}, scandata=None)

            elif etype == "SAAMaterialsFound":
                body_name = evt.get("BodyName")
                mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
                # noinspection PyArgumentList
                self.m.update_body(name=body_name, landable=True, materials=mats)
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
            # noinspection PyBroadException
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
