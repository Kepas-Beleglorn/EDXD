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
# simple container
# ---------------------------------------------------------------------------
class Body:
    __slots__ = ("name", "body_type", "scoopable", "landable", "biosignals", "geosignals",
                 "estimated_value", "materials",
                 "bio_found", "geo_found", "distance")

    def __init__(self,
                 materials:         Dict[str, float],
                 name:              str,
                 body_type:         str = "",
                 scoopable:         bool = False,
                 landable:          bool = False,
                 distance:          int = 0,
                 bio_found:         Dict[str, int] | None = None,
                 geo_found:         Dict[str, bool] | None = None,
                 biosignals:        int = 0,
                 geosignals:        int = 0,
                 estimated_value:   int = 0):

        self.name               = name
        self.body_type          = body_type
        self.scoopable          = scoopable
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
        self.just_jumped   : bool = True

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
            self.just_jumped = True

            cached = dh.load(CACHE_DIR / f"{address}.json", {})
            # Current format: { "total_bodies": int,
            #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
            if isinstance(cached, dict):
                # reload total count
                #self.total_bodies = cached.get("total_bodies", None)
                body_map = cached.get("bodies", {})
                for body_name, body_properties in body_map.items():
                    body_type = body_properties.get("body_type", "")
                    scoopable = body_properties.get("scoopable", False)
                    distance = body_properties.get("distance", 0)
                    land = body_properties.get("landable", False)
                    bio = body_properties.get("biosignals", 0)
                    geo = body_properties.get("geosignals", 0)
                    mats = body_properties.get("materials", {})
                    bio_dict = body_properties.get("bio_found", {})
                    geo_dict = body_properties.get("geo_found", {})
                    estimated_value = body_properties.get("estimated_value", 0)
                    self.bodies[body_name] = Body(name=body_name, body_type=body_type, scoopable=scoopable, distance=distance, landable=land, materials=mats, biosignals=bio, geosignals=geo, bio_found=bio_dict, geo_found=geo_dict, estimated_value=estimated_value)

    def update_body(self, systemaddress: int, name: str, body_type: str = "", scoopable: bool = False, distance: int = 0, landable: bool = False, biosignals: int = 0, geosignals: int = 0, materials: Dict[str, float] = None, scandata = None, bio_found = None, geo_found = None):
        with self.lock:
            #if self.system_addr is None:
            self.system_addr = systemaddress
            body = self.bodies.get(name, Body(name=name, body_type=body_type, landable=landable, materials={}))
            body.body_type = body_type
            body.scoopable = scoopable
            body.distance = body.distance or distance
            body.landable = body.landable or landable
            body.biosignals = body.biosignals or biosignals
            body.geosignals = body.geosignals or geosignals
            body.bio_found = body.bio_found or bio_found
            body.geo_found = body.geo_found or geo_found
            if materials is not None:
                body.materials.update(materials)
            if scandata is not None:
                body.estimated_value = appraise_body(body_info=scandata, just_scanned_value=False)
            self.bodies[name] = body
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
                bodyname: {
                    "body_type": body.body_type,
                    "scoopable": body.scoopable,
                    "landable": body.landable,
                    "distance": body.distance,
                    "biosignals": body.biosignals,
                    "geosignals": body.geosignals,
                    "materials": body.materials,
                    "bio_found": body.bio_found,
                    "geo_found": body.geo_found,
                    "estimated_value": body.estimated_value,
                }
                for bodyname, body in self.bodies.items()
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
