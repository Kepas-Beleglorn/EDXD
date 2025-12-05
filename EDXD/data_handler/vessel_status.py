from __future__ import annotations

import functools
import inspect
from typing import Dict

# ---------------------------------------------------------------------------
# paths (shared with other modules)
# ---------------------------------------------------------------------------
from EDXD.globals import logging, LOG_LEVEL


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


class ShipStatus:
    __slots__ = ("ship_type", "ship_id", "ship_name", "ship_ident", "fuel_capacity", "jet_cone_boost_factor", "fsd_injection_factor")

    def __init__(self,
                 ship_type              : str = None,
                 ship_id                : int = None,
                 ship_name              : str = None,
                 ship_ident             : str = None,
                 fuel_capacity          : Dict[str, FuelLevel] | None = None,
                 jet_cone_boost_factor  : float = None,
                 fsd_injection_factor   : float = None
                 ):

        self.ship_type              = ship_type
        self.ship_id                = ship_id
        self.ship_name              = ship_name
        self.ship_ident             = ship_ident
        self.fuel_capacity          = fuel_capacity or FuelLevel()
        self.jet_cone_boost_factor  = jet_cone_boost_factor
        self.fsd_injection_factor   = fsd_injection_factor

    def read_from_json(self, ship_status):
        if ship_status:
            self.ship_type = ship_status.get("ship_type", None)
            self.ship_id = ship_status.get("ship_id", None)
            self.ship_name = ship_status.get("ship_name", None)
            self.ship_ident = ship_status.get("ship_ident", None)
            self.fuel_capacity = FuelLevel(ship_status.get("fuel_capacity", None).get("main", None), ship_status.get("fuel_capacity", None).get("reserve", None))

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
