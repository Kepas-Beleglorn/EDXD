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
from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates
from typing import Dict, List, Optional
from EDXD.data_handler.helper.body_appraiser import appraise_body
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

# ---------------------------------------------------------------------------
# simple container
# ---------------------------------------------------------------------------
class Body:
    __slots__ = ("body_id", "body_name", "body_type", "scoopable", "landable", "biosignals", "geosignals", "estimated_value", "materials", "bio_found", "geo_found", "distance", "rings", "radius")

    def __init__(self,
                 body_id:           str,
                 body_name:         str = "",
                 body_type:         str = "",
                 scoopable:         bool = False,
                 landable:          bool = False,
                 distance:          int = 0,
                 materials:         Dict[str, float] | None = None,
                 bio_found:         Dict[str, Genus] | None = None,
                 geo_found:         Dict[str, CodexEntry] | None = None,
                 biosignals:        int = 0,
                 geosignals:        int = 0,
                 estimated_value:   int = 0,
                 rings:             Dict[str, Ring] | None = None,
                 radius:            float = 0.0
                 ):

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
        self.rings              = rings     or {}
        self.radius             = radius

class Ring:
    __slots__ = ("body_id", "body_name", "signals")
    def __init__(self,
                 body_id:   str,
                 body_name: str = "",
                 signals:   Dict[str, int] | None = None):

        self.body_id = body_id
        self.body_name = body_name
        self.signals = signals or {}

    def to_dict(self):
        data = {
            "body_id": self.body_id,
            "body_name": self.body_name,
            "signals": self.signals
        }
        return data

"""
{
	"timestamp": "2025-06-12T16:56:11Z",
	"event": "ScanOrganic",
	"ScanType": "Log",
	"Genus": "$Codex_Ent_Fonticulus_Genus_Name;",
	"Genus_Localised": "Fonticulua",
	"Species": "$Codex_Ent_Fonticulus_02_Name;",
	"Species_Localised": "Fonticulua Campestris",
	"Variant": "$Codex_Ent_Fonticulus_02_M_Name;",
	"Variant_Localised": "Fonticulua Campestris - Amethyst",
	"SystemAddress": 40181431154417,
	"Body": 17
}
"""
class Genus:
    __slots__ = ("genusid", "localised", "species_localised", "variant_localised", "scanned_count", "min_distance")
    def __init__(self,
                 genusid            : str = None,
                 localised          : str = None,
                 species_localised  : str = None,
                 variant_localised  : str = None,
                 scanned_count      : int = None,
                 min_distance       : int = None
                 ):
        self.genusid            = genusid
        self.localised          = localised
        self.species_localised  = species_localised
        self.variant_localised  = variant_localised
        self.scanned_count      = scanned_count
        self.min_distance       = min_distance

    def to_dict(self):
        data = {
            "genusid"           : self.genusid,
            "localised"         : self.localised,
            "species_localised" : self.species_localised,
            "variant_localised" : self.variant_localised,
            "scanned_count"     : self.scanned_count,
            "min_distance"      : self.min_distance
        }
        return data

"""
{ "timestamp":"2025-06-12T18:37:58Z", "event":"CodexEntry", "EntryID":1400158, 
"Name":"$Codex_Ent_IceFumarole_WaterGeysers_Name;", "Name_Localised":"Water Ice Fumarole", 
"SubCategory":"$Codex_SubCategory_Geology_and_Anomalies;", "SubCategory_Localised":"Geology and anomalies", 
"Category":"$Codex_Category_Biology;", "Category_Localised":"Biological and Geological", 
"Region":"$Codex_RegionName_9;", "Region_Localised":"Inner Scutum-Centaurus Arm", "System":"Prua Phoe FX-H b28-18", 
"SystemAddress":40181431154417, "BodyID":15, "Latitude":-66.832031, "Longitude":42.411892, "IsNewEntry":true }
"""
class CodexEntry:
    __slots__ = ("codexid", "localised", "is_new", "body_id")
    def __init__(self,
                 codexid    : str = None,
                 localised  : str = None,
                 is_new     : bool = None,
                 body_id    : str = None
                 ):
        self.codexid    = codexid
        self.localised  = localised
        self.is_new     = is_new
        self.body_id    = body_id

    def to_dict(self):
        data = {
            "codexid"   : self.codexid,
            "localised" : self.localised,
            "is_new"    : self.is_new,
            "body_id"   : self.body_id
        }
        return data



# ---------------------------------------------------------------------------
# thread-safe data model
# ---------------------------------------------------------------------------
class Model:
    """Keeps the bodies of the *current* system; notifies target listeners."""

    def __init__(self):
        self.lock               = threading.Lock()
        self.system_name        : Optional[str]         = None
        self.system_addr        : Optional[int]         = None
        self.bodies             : Dict[str, Body]       = {}
        self.target_body_id     : Optional[str]         = None
        self.total_bodies       : Optional[int]         = None
        self._target_cbs        : List = []             # listeners
        self.just_jumped        : bool = True
        self.current_position   : Optional[PSPSCoordinates] = None
        self.current_heading    : Optional[int] = None


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

        if isinstance(cached, dict):
            # reload total count
            if self.total_bodies is None:
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
                rings_dict      = body_properties.get("rings", {})
                radius          = body_properties.get("radius", 0.0)

                # Convert all dicts to their respective objects
                bio_found = {k: Genus(**v) if isinstance(v, dict) else v for k, v in bio_dict.items()}
                geo_found = {k: CodexEntry(**v) if isinstance(v, dict) else v for k, v in geo_dict.items()}
                rings_found = {k: Ring(**v) if isinstance(v, dict) else v for k, v in rings_dict.items()}


                self.bodies[body_id] = Body(
                    body_id=body_id,
                    body_name=body_name,
                    body_type=body_type,
                    scoopable=scoopable,
                    distance=distance,
                    landable=landable,
                    materials=mats,
                    biosignals=bio_count,
                    geosignals=geo_count,
                    bio_found=bio_found,
                    geo_found=geo_found,
                    estimated_value=estimated_value,
                    rings=rings_found,
                    radius=radius
                )

    #@log_call(logging.DEBUG)
    def update_body(self, systemaddress: int, body_id: str, body_name: str = None, body_type: str = None, scoopable: bool = None, distance: int = None, landable: bool = None,
                    biosignals: int = None, geosignals: int = None, materials: Dict[str, float] = None, scandata = None,
                    bio_found: Dict[str, Genus] = None, geo_found: Dict[str, CodexEntry] = None, rings: Dict[str, Ring] = None, total_bodies: int = None, radius: float = 0.0):
        with self.lock:
            self.system_addr = systemaddress
            tmp_total_bodies = total_bodies or self.total_bodies

            if self.total_bodies is None:
                self.total_bodies = tmp_total_bodies
            if body_id is not None:
                body = self.bodies.get(body_id, Body(body_id=body_id))
                body.body_name  = body_name     or body.body_name   or ""
                body.body_type  = body_type     or body.body_type   or ""
                body.scoopable  = scoopable     or body.scoopable   or False
                body.distance   = distance      or body.distance    or 0
                body.landable   = landable      or body.landable    or False
                body.biosignals = biosignals    or body.biosignals  or 0
                body.geosignals = geosignals    or body.geosignals  or 0
                body.bio_found  = bio_found     or body.bio_found   or {}
                body.geo_found  = geo_found     or body.geo_found   or {}
                body.rings      = rings         or body.rings       or {}
                body.radius     = radius        or body.radius
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
                    "radius"            : body.radius,
                    "distance"          : body.distance,
                    "biosignals"        : body.biosignals,
                    "geosignals"        : body.geosignals,
                    "materials"         : body.materials,
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
