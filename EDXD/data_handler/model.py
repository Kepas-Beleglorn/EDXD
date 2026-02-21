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
from dataclasses import dataclass, asdict, field
from typing import Optional, List

import EDXD.data_handler.helper.data_helper as dh
from EDXD.data_handler.helper.body_appraiser import appraise_body
from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates
from EDXD.data_handler.vessel_status import *
from EDXD.globals import BODY_ID_PREFIX

bip = BODY_ID_PREFIX

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

@dataclass
class Body:
    body_id         : str
    body_name       : str = ""
    body_type       : str = ""
    scoopable       : bool = False
    landable        : bool = False
    distance        : int = 0
    materials       : Dict[str, float] = field(default_factory=dict)
    bio_found       : Dict[str, Genus] = field(default_factory=dict)
    geo_found       : Dict[str, CodexEntry] = field(default_factory=dict)
    biosignals      : int = 0
    geosignals      : int = 0
    estimated_value : int = 0
    rings           : Dict[str, Ring] = field(default_factory=dict)
    radius          : float = 0.0
    mapped          : bool = False
    geo_complete    : bool = False
    geo_scanned     : int = 0
    bio_complete    : bool = False
    bio_scanned     : int = 0
    first_discovered: int = 0
    first_mapped    : int = 0
    first_footfalled: int = 0
    g_force         : float = 0.0
    atmosphere      : Atmosphere = None

    def __post_init__(self):
        # Ensure mutable defaults are initialized as empty dicts if None is passed
        if self.materials is None:
            self.materials = {}
        if self.bio_found is None:
            self.bio_found = {}
        if self.geo_found is None:
            self.geo_found = {}
        if self.rings is None:
            self.rings = {}

@dataclass
class Ring:
    body_id     : str
    body_name   : str = ""
    signals     : Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure mutable defaults are initialized as empty dicts if None is passed
        if self.signals is None:
            self.signals = {}

    def to_dict(self):
        return asdict(self)

@dataclass
class Genus:
    genusid            : Optional[str] = None
    localised          : Optional[str] = None
    species_localised  : Optional[str] = None
    variant_localised  : Optional[str] = None
    scanned_count      : Optional[int] = None
    min_distance       : Optional[int] = None
    pos_first          : Optional[PSPSCoordinates] = None
    pos_second         : Optional[PSPSCoordinates] = None

    def to_dict(self):
        data = asdict(self)
        if self.pos_first and hasattr(self.pos_first, "to_dict"):
            data["pos_first"] = self.pos_first.to_dict()

        if self.pos_second and hasattr(self.pos_second, "to_dict"):
            data["pos_second"] = self.pos_second.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None

        # make a shallow copy to avoid mutating the caller's dict
        d = dict(data)

        if "pos_first" in d and isinstance(d["pos_first"], dict):
            d["pos_first"] = PSPSCoordinates.from_dict(d["pos_first"])
        if "pos_second" in d and isinstance(d["pos_second"], dict):
            d["pos_second"] = PSPSCoordinates.from_dict(d["pos_second"])

        return cls(**d)

@dataclass
class CodexEntry:
    codexid     : str = None
    localised   : str = None
    is_new      : bool = None
    body_id     : str = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Atmosphere:
    type        : str = None
    composition : Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure mutable defaults are initialized as empty dicts if None is passed
        if self.composition is None:
            self.composition = {}

    def to_dict(self):
        return asdict(self)

# ---------------------------------------------------------------------------
# thread-safe data model
# ---------------------------------------------------------------------------
class Model:
    """Keeps the bodies of the *current* system; notifies target listeners."""
    def __init__(self):
        self.lock               = threading.Lock()
        self.system_name        : Optional[str]             = None
        self.system_addr        : Optional[int]             = None
        self.bodies             : Dict[str, Body]           = {}
        self.target_body_id     : Optional[str]             = None
        self.selected_body_id   : Optional[str]             = None
        self.total_bodies       : Optional[int]             = None
        self._target_cbs        : List                      = [] # listeners
        self.current_position   : Optional[PSPSCoordinates] = None
        self.current_heading    : Optional[int]             = None
        self.ship_status        : Optional[ShipStatus]      = None
        self.fuel_level         : Optional[FuelLevel]       = None
        self.current_vessel     : Optional[str]             = None
        self.flags              : Optional[int]             = None
        self.flags2             : Optional[int]             = None

    # ----- listeners ---------------------------------------------------------
    def register_target_listener(self, cb):
        """cb(body_name:str) → None"""
        self._target_cbs.append(cb)

    def _fire_target(self, body_id: str):
        if body_id is None:
            return
        for cb in self._target_cbs:
            cb(body_id)

    # ----- mutators ----------------------------------------------------------
    #@log_call()
    def reset_system(self, system_name: str, address: Optional[int]):
        tmp_selected_body_id = self.selected_body_id
        """Clear all bodies and load cached system if available."""
        with self.lock:
            self.system_name = system_name
            self.system_addr = address
            self.bodies.clear()
            self.target_body_id = None
            self.selected_body_id = None

            self.read_data_from_cache(address=address)

            self.selected_body_id = tmp_selected_body_id

    def read_data_from_cache(self, address: int):
        cached = dh.load(CACHE_DIR / f"{address}.json", {})

        if isinstance(cached, dict):
            # reload total count
            if self.total_bodies is None:
                self.total_bodies = cached.get("total_bodies", None)
            body_map = cached.get("bodies", {})
            for body_id, body_properties in body_map.items():
                body_name           = body_properties.get("body_name", "")
                body_type           = body_properties.get("body_type", "")
                scoopable           = body_properties.get("scoopable", False)
                distance            = body_properties.get("distance", 0)
                landable            = body_properties.get("landable", False)
                g_force             = body_properties.get("g_force", 0.0)
                bio_count           = body_properties.get("biosignals", 0)
                geo_count           = body_properties.get("geosignals", 0)
                mats                = body_properties.get("materials", {})
                bio_dict            = body_properties.get("bio_found", {})
                geo_dict            = body_properties.get("geo_found", {})
                estimated_value     = body_properties.get("estimated_value", 0)
                rings_dict          = body_properties.get("rings", {})
                radius              = body_properties.get("radius", 0.0)
                mapped              = body_properties.get("mapped", False)
                geo_complete        = body_properties.get("geo_complete", False)
                geo_scanned         = body_properties.get("geo_scanned", 0)
                bio_complete        = body_properties.get("bio_complete", False)
                bio_scanned         = body_properties.get("bio_scanned", 0)
                first_discovered    = body_properties.get("first_discovered", 0)
                first_mapped        = body_properties.get("first_mapped", 0)
                first_footfalled    = body_properties.get("first_footfalled", 0)
                atmosphere          = body_properties.get("atmosphere", None)

                bio_found = {k: Genus.from_dict(v) if isinstance(v, dict) else v for k, v in bio_dict.items()}
                geo_found = {k: CodexEntry(**v) if isinstance(v, dict) else v for k, v in geo_dict.items()}
                rings_found = {k: Ring(**v) if isinstance(v, dict) else v for k, v in rings_dict.items()}

                self.bodies[body_id] = Body(
                    body_id=body_id,
                    body_name=body_name,
                    body_type=body_type,
                    scoopable=scoopable,
                    distance=distance,
                    landable=landable,
                    g_force=g_force,
                    materials=mats,
                    biosignals=bio_count,
                    geosignals=geo_count,
                    bio_found=bio_found,
                    geo_found=geo_found,
                    estimated_value=estimated_value,
                    rings=rings_found,
                    radius=radius,
                    mapped=mapped,
                    geo_complete=geo_complete,
                    geo_scanned=geo_scanned,
                    bio_complete=bio_complete,
                    bio_scanned=bio_scanned,
                    first_discovered=first_discovered,
                    first_mapped=first_mapped,
                    first_footfalled=first_footfalled,
                    atmosphere=atmosphere
                )

    def update_body(self, systemaddress: int, body_id: str, body_name: str = None, body_type: str = None, scoopable: bool = None, distance: int = None, landable: bool = None,
                    biosignals: int = None, geosignals: int = None, materials: Dict[str, float] = None, scandata = None,
                    bio_found: Dict[str, Genus] = None, geo_found: Dict[str, CodexEntry] = None, rings: Dict[str, Ring] = None, total_bodies: int = None, radius: float = 0.0, mapped: bool = False,
                    geo_complete: bool = False, geo_scanned: int = 0, bio_complete: bool = False, bio_scanned: int = 0,
                    first_discovered: int = 0, first_mapped: int = 0, first_footfalled: int = 0, g_force: float = 0.0, atmosphere: Atmosphere = None):
        with self.lock:
            self.system_addr = systemaddress
            tmp_total_bodies = total_bodies or self.total_bodies

            if self.total_bodies is None:
                self.total_bodies = tmp_total_bodies
            if body_id is not None:
                body = self.bodies.get(body_id, Body(body_id=body_id))
                body.body_name          = body_name         or body.body_name           or ""
                body.body_type          = body_type         or body.body_type           or ""
                body.scoopable          = scoopable         or body.scoopable           or False
                body.distance           = distance          or body.distance            or 0
                body.landable           = landable          or body.landable            or False
                body.g_force            = g_force           or body.g_force             or 0
                body.biosignals         = biosignals        or body.biosignals          or 0
                body.geosignals         = geosignals        or body.geosignals          or 0
                body.bio_found          = bio_found         or body.bio_found           or {}
                body.geo_found          = geo_found         or body.geo_found           or {}
                body.rings              = rings             or body.rings               or {}
                body.radius             = radius            or body.radius              or 0
                body.mapped             = mapped            or body.mapped              or False
                body.geo_complete       = geo_complete      or body.geo_complete        or False
                body.geo_scanned        = geo_scanned       or body.geo_scanned         or 0
                body.bio_complete       = bio_complete      or body.bio_complete        or False
                body.bio_scanned        = bio_scanned       or body.bio_scanned         or 0
                body.first_discovered   = first_discovered  or body.first_discovered    or 0
                body.first_mapped       = first_mapped      or body.first_mapped        or 0
                body.first_footfalled   = first_footfalled  or body.first_footfalled    or 0
                body.atmosphere         = atmosphere        or body.atmosphere          or None

                if materials is not None:
                    body.materials.update(materials)
                if scandata is not None and scandata.get("event") == "Scan" and scandata.get("ScanType") in {"AutoScan", "Detailed"}:
                    body.estimated_value = appraise_body(body_info=scandata, just_scanned_value=False)

                self.bodies[body_id] = body
            self._save_cache()

    def update_body_count(self, systemaddress: int, total_bodies: int = None):
        with self.lock:
            self.system_addr = systemaddress
            tmp_total_bodies = total_bodies or self.total_bodies

            if self.total_bodies is None:
                self.total_bodies = tmp_total_bodies
            self._save_cache()

    def set_target(self, body_id: str):
        with self.lock:
            self.target_body_id = body_id
        self._fire_target(body_id)

    def set_position(self, latitude: float, longitude: float, heading: int):
        with self.lock:
            self.current_position = PSPSCoordinates(latitude, longitude)
            self.current_heading = heading

    # ----- cache -------------------------------------------------------------
    def _save_cache(self):
        """Persist bodies *and* total_bodies to disk."""
        if self.system_addr is None:
            return

        # Current format: { "total_bodies": int,
        #                   "bodies": { name: {landable:…, biosignals:…, geosignals:…, materials:…}, … } }
        data = {
            "system_addr"   : self.system_addr,
            "system_name"   : self.system_name,
            "total_bodies"  : self.total_bodies,
            "bodies"        : {
                body_id: {
                    "body_name"         : body.body_name,
                    "body_type"         : body.body_type,
                    "scoopable"         : body.scoopable,
                    "landable"          : body.landable,
                    "g_force"           : body.g_force,
                    "radius"            : body.radius,
                    "mapped"            : body.mapped,
                    "distance"          : body.distance,
                    "biosignals"        : body.biosignals,
                    "bio_scanned"       : body.bio_scanned,
                    "bio_complete"      : body.bio_complete,
                    "geosignals"        : body.geosignals,
                    "geo_scanned"       : body.geo_scanned,
                    "geo_complete"      : body.geo_complete,
                    "materials"         : body.materials,
                    "first_discovered"  : body.first_discovered,
                    "first_mapped"      : body.first_mapped,
                    "first_footfalled"  : body.first_footfalled,
                    "bio_found"         : {
                        genusid:
                            genus.to_dict()
                        for genusid, genus in body.bio_found.items()
                    },
                    "geo_found"         : {
                        geoid:
                            geo.to_dict()
                        for geoid, geo in body.geo_found.items()
                    },
                    "estimated_value"   : body.estimated_value,
                    "rings"             : {
                        ringid:
                            ring.to_dict()
                        for ringid, ring in body.rings.items()
                    },
                    "atmosphere"        : body.atmosphere.to_dict() if hasattr(body.atmosphere, 'to_dict') else body.atmosphere,
                }
                for body_id, body in self.bodies.items()
            },
        }
        dh.save(CACHE_DIR / f"{self.system_addr}.json", data)

    def load_cached_total_bodies(self, system_address: int = None):
        if system_address is None:
            pass
        cached = dh.load(CACHE_DIR / f"{self.system_addr}.json", {})
        self.total_bodies = cached.get("total_bodies", None)

    # ----- snapshot helpers --------------------------------------------------

    def snapshot_bodies(self) -> Dict[str, Body]:
        with self.lock:
            return dict(self.bodies)

    def snapshot_target(self) -> Optional[Body]:
        with self.lock:
            return self.bodies.get(self.target_body_id)

    def snapshot_position(self) -> PSPSCoordinates:
        with self.lock:
            return self.current_position

    def snapshot_total(self) -> Optional[int]:
        with self.lock:
            return self.total_bodies
