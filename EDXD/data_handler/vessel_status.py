from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# paths (shared with other modules)
# ---------------------------------------------------------------------------
from EDXD.globals import logging


class ShipStatus:
    __slots__ = ("ship_type", "ship_id", "ship_name", "ship_ident", "fuel_capacity", "max_jump_range", "mass_unladen", "mass_fsd_optimal", "cargo", "cargo_capacity", "jet_cone_boost_factor", "fsd_injection_factor")

    def __init__(self,
                 ship_type              : str | None = None,
                 ship_id                : int | None = None,
                 ship_name              : str | None = None,
                 ship_ident             : str | None = None,
                 fuel_capacity          : Dict[str, FuelLevel] | None = None,
                 max_jump_range         : float | None = None,
                 mass_unladen           : float | None = None,
                 mass_fsd_optimal       : float | None = None,
                 cargo                  : int | None = None,
                 cargo_capacity         : int | None = None,
                 jet_cone_boost_factor  : float | None = None,
                 fsd_injection_factor   : float | None = None
                 ):

        self.ship_type              = ship_type
        self.ship_id                = ship_id
        self.ship_name              = ship_name
        self.ship_ident             = ship_ident
        self.fuel_capacity          = fuel_capacity or FuelLevel()
        self.max_jump_range         = max_jump_range
        self.mass_unladen           = mass_unladen
        self.mass_fsd_optimal       = mass_fsd_optimal
        self.cargo                  = cargo
        self.cargo_capacity         = cargo_capacity
        self.jet_cone_boost_factor  = jet_cone_boost_factor
        self.fsd_injection_factor   = fsd_injection_factor

    def read_from_json(self, ship_status):
        if ship_status:
            self.ship_type = ship_status.get("ship_type", None)
            self.ship_id = ship_status.get("ship_id", None)
            self.ship_name = ship_status.get("ship_name", None)
            self.ship_ident = ship_status.get("ship_ident", None)
            self.fuel_capacity = FuelLevel(ship_status.get("fuel_capacity", None).get("main", None), ship_status.get("fuel_capacity", None).get("reserve", None))
            self.max_jump_range = ship_status.get("max_jump_range", None)
            self.mass_unladen = ship_status.get("mass_unladen", None)
            self.mass_fsd_optimal = ship_status.get("mass_fsd_optimal", None)
            self.cargo = ship_status.get("cargo", None)
            self.cargo_capacity = ship_status.get("cargo_capacity", None)
            self.jet_cone_boost_factor = ship_status.get("jet_cone_boost_factor", None)
            self.fsd_injection_factor = ship_status.get("fsd_injection_factor", None)

        return self

    def to_json(self):
        data = {
            "ship_type": self.ship_type,
            "ship_id": self.ship_id,
            "ship_name": self.ship_name,
            "ship_ident": self.ship_ident,
            "fuel_capacity":
            {
                fuel_item:
                    fuel
                for fuel_item, fuel in self.fuel_capacity.to_dict().items()
            },
            "max_jump_range": self.max_jump_range,
            "mass_unladen": self.mass_unladen,
            "mass_fsd_optimal": self.mass_fsd_optimal,
            "cargo": self.cargo,
            "cargo_capacity": self.cargo_capacity,
            "jet_cone_boost_factor": self.jet_cone_boost_factor,
            "fsd_injection_factor": self.fsd_injection_factor
        }
        return data


class FuelLevel:
    __slots__ = ("main", "reserve")
    def __init__(self,
                 main       : float = None,
                 reserve    : float = None
                 ):
        self.main       = main
        self.reserve    = reserve

    def to_dict(self):
        data = {
            "main" : self.main,
            "reserve" : self.reserve
        }
        return data
