"""
model.py – core logic for ED Mineral Viewer
==========================================

* Body            – simple dataclass-style container
* Model           – thread-safe store of the current system
* JournalReader            – follows the newest Journal file in real time
* JournalController      – consumes events from JournalReader and updates Model
"""

from __future__ import annotations
import threading
import EDXD.data_handler.helper.data_helper as dh
from typing import Dict, List, Optional
from EDXD.body_appraiser import appraise_body

# ---------------------------------------------------------------------------
# paths (shared with other modules)
# ---------------------------------------------------------------------------
from EDXD.globals import CACHE_DIR
from EDXD.globals import logging, LOG_LEVEL
import inspect, functools

def log_call(level=LOG_LEVEL):
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
# simple container
# ---------------------------------------------------------------------------
class Body:
    __slots__ = ("body_id", "body_name", "body_type", "scoopable", "landable", "biosignals", "geosignals", "estimated_value", "materials", "bio_found", "geo_found", "distance", "rings")

    def __init__(self,
                 body_id:           str,
                 body_name:         str = "",
                 body_type:         str = "",
                 scoopable:         bool = False,
                 landable:          bool = False,
                 distance:          int = 0,
                 materials:         Dict[str, float] | None = None,
                 bio_found:         Dict[str, int] | None = None,
                 geo_found:         Dict[str, bool] | None = None,
                 biosignals:        int = 0,
                 geosignals:        int = 0,
                 estimated_value:   int = 0,
                 rings:             Ring = None):

        self.body_id            = body_id
        self.body_name          = body_name
        self.body_type          = body_type
        self.scoopable          = scoopable
        self.distance           = distance
        self.landable           = landable
        self.biosignals         = biosignals
        self.geosignals         = geosignals
        self.estimated_value    = estimated_value
        self.materials          = materials or {}
        self.bio_found          = bio_found or {}    # { biosign name -> scans_done }         e.g. {"Bacterium Bullaris":2}
        self.geo_found          = geo_found or {}    # { "volcanism-01": True … }             True once SRV scanned
        self.rings              = rings

class Ring:
    __slots__ = ("body_id", "body_name", "signals")
    def __init__(self,
                 body_id:   str,
                 body_name: str = "",
                 signals:   Dict[str, int] | None = None):

        self.body_id = body_id
        self.body_name = body_name
        self.signals = signals or {}


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
        self.target_body_id: Optional[str]         = None
        self.total_bodies  : Optional[int]         = None
        self._target_cbs   : List = []             # listeners
        self.just_jumped   : bool = True

    # ----- snapshot helpers --------------------------------------------------
    def snapshot_bodies(self) -> Dict[str, Body]:
        with self.lock:
            return dict(self.bodies)

    def snapshot_target(self) -> Optional[Body]:
        with self.lock:
            return self.bodies.get(self.target_body_id)

    # ----- listeners ---------------------------------------------------------
    def register_target_listener(self, cb):
        """cb(body_name:str) → None"""
        self._target_cbs.append(cb)

    def _fire_target(self, body_id: str):
        if body_id == -1:
            return
        for cb in self._target_cbs:
            cb(body_id)

    # ----- mutators ----------------------------------------------------------
    #@log_call()
    def reset_system(self, system_name: str, address: Optional[int]):
        """Clear all bodies and load cached system if available."""
        with self.lock:
            self.system_name = system_name
            self.system_addr = address
            self.bodies.clear()
            self.target_body_id = None
            self.just_jumped = True

            self.read_data_from_cache(address=address)

    def read_data_from_cache(self, address: int):
        cached = dh.load(CACHE_DIR / f"{address}.json", {})
        # Current format: { "total_bodies": int,
        #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
        if isinstance(cached, dict):
            # reload total count
            #self.system_name = cached.get("system_name", "")
            self.total_bodies = cached.get("total_bodies", None)
            body_map = cached.get("bodies", {})
            for body_id, body_properties in body_map.items():
                body_name       = body_properties.get("body_name", "")
                body_type       = body_properties.get("body_type", "")
                scoopable       = body_properties.get("scoopable", False)
                distance        = body_properties.get("distance", 0)
                landable        = body_properties.get("landable", False)
                bio_count       = body_properties.get("biosignals", 0)
                geo_count       = body_properties.get("geosignals", 0)
                mats            = body_properties.get("materials", {})
                bio_dict        = body_properties.get("bio_found", {})
                geo_dict        = body_properties.get("geo_found", {})
                estimated_value = body_properties.get("estimated_value", 0)
                rings           = body_properties.get("rings", {})

                self.bodies[str(body_id)] = Body(
                    body_id=str(body_id),
                    body_name=body_name,
                    body_type=body_type,
                    scoopable=scoopable,
                    distance=distance,
                    landable=landable,
                    materials=mats,
                    biosignals=bio_count,
                    geosignals=geo_count,
                    bio_found=bio_dict,
                    geo_found=geo_dict,
                    estimated_value=estimated_value,
                    rings=rings
                )

    @log_call(logging.DEBUG)
    def update_body(self, systemaddress: int, body_id: str, body_name: str = None, body_type: str = None, scoopable: bool = None, distance: int = None, landable: bool = None,
                    biosignals: int = None, geosignals: int = None, materials: Dict[str, float] = None, scandata = None,
                    bio_found = None, geo_found = None, rings: Dict[str, int] = None):
        with self.lock:
            self.system_addr = systemaddress
            tmp_total_bodies = self.total_bodies
            self.read_data_from_cache(address=self.system_addr)
            if self.total_bodies is None:
                self.total_bodies = tmp_total_bodies
            body = self.bodies.get(body_id, Body(body_id=body_id))
            body.body_name = body.body_name or body_name or ""
            body.body_type = body.body_type or body_type or ""
            body.scoopable = body.scoopable or scoopable or False
            body.distance = body.distance or distance or -1
            body.landable = body.landable or landable or False
            body.biosignals = body.biosignals or biosignals or 0
            body.geosignals = body.geosignals or geosignals or 0
            body.bio_found = body.bio_found or bio_found or {}
            body.geo_found = body.geo_found or geo_found or {}
            body.rings = body.rings or rings
            if materials is not None:
                body.materials.update(materials)
            if scandata is not None:
                body.estimated_value = appraise_body(body_info=scandata, just_scanned_value=False)
            self.bodies[body_id] = body
            self._save_cache()

    def set_target(self, body_id: str):
        with self.lock:
            self.target_body_id = body_id
        self._fire_target(body_id)

    def set_target_by_name(self, target_name: str):
        body_id = -1
        with self.lock:
            # get body ID by name
            for body, body_data in self.bodies.items():
                if body_data.body_name == target_name:
                    body_id = str(body)

        self._fire_target(body_id)


    # ----- cache -------------------------------------------------------------
    def _save_cache(self):
        """Persist bodies *and* total_bodies to disk."""
        if self.system_addr is None:
            return

        # Current format: { "total_bodies": int,
        #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
        data = {
            "system_name"   : self.system_name,
            "total_bodies"  : self.total_bodies,
            "bodies"        : {
                str(body_id): {
                    "body_name"         : body.body_name,
                    "body_type"         : body.body_type,
                    "scoopable"         : body.scoopable,
                    "landable"          : body.landable,
                    "distance"          : body.distance,
                    "biosignals"        : body.biosignals,
                    "geosignals"        : body.geosignals,
                    "materials"         : body.materials,
                    "bio_found"         : body.bio_found,
                    "geo_found"         : body.geo_found,
                    "estimated_value"   : body.estimated_value,
                    "rings"             : body.rings,
                }
                for body_id, body in self.bodies.items()
            },
        }
        dh.save(CACHE_DIR / f"{self.system_addr}.json", data)
    #@log_call()
    def snapshot_total(self) -> Optional[int]:
        with self.lock:
            return self.total_bodies

    def load_cached_total_bodies(self, system_address: int = None):
        if system_address is None:
            pass
        cached = dh.load(CACHE_DIR / f"{self.system_addr}.json", {})
        self.total_bodies = cached.get("total_bodies", None)
