import json
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import EDXD.data_handler.helper.galactic_navigation as gn
import EDXD.data_handler.helper.data_helper as dh
from EDXD.data_handler.helper.json_helper import DotDict
from EDXD.data_handler.helper.galactic_navigation import StarPosition


@dataclass
class NavPoint:
    star_system: str
    system_address: int
    star_class: str
    star_position: StarPosition

@dataclass
class PlottedNavRoute:
    timestamp: Optional[datetime]
    nav_points: List[NavPoint]

class NavRouteHandler:
    def __init__(self, nav_route_json: Path, amount_of_upcoming_systems_to_show: int, amount_of_passed_systems_to_show: int):
        self.nav_route_json: Path = nav_route_json
        self.plotted_nav_route: Optional[PlottedNavRoute] = None
        self.remaining_jumps_in_route: int = 0
        self.amount_of_upcoming_systems_to_show: int = amount_of_upcoming_systems_to_show
        self.amount_of_passed_systems_to_show: int = amount_of_passed_systems_to_show
        self.current_system: Optional[NavPoint] = None

    def _parse_star_position(self, pos_data: List[float]) -> StarPosition:
        """Converts a list of 3 floats into a StarPosition dataclass."""
        return StarPosition(x=pos_data[0], y=pos_data[1], z=pos_data[2])

    def _parse_nav_points(self, route_data: List[dict]) -> List[NavPoint]:
        """Iterates through the raw route list and builds NavPoint instances."""
        systems = []
        for system in route_data:
            # Handle DotDict or standard dict access safely
            pos = self._parse_star_position(system.StarPos if isinstance(system, DotDict) else system['StarPos'])

            nav_point = NavPoint(
                star_system=system.StarSystem if isinstance(system, DotDict) else system['StarSystem'],
                system_address=system.SystemAddress if isinstance(system, DotDict) else system['SystemAddress'],
                star_class=system.StarClass if isinstance(system, DotDict) else system['StarClass'],
                star_position=pos
            )
            systems.append(nav_point)
        return systems

    def load_plotted_route(self):
        raw_data = self.nav_route_json.read_text()
        data = DotDict(json.loads(raw_data))

        # Parse the timestamp
        timestamp = dh.parse_utc_isoformat(data.timestamp) if data.timestamp else None

        # Parse the list of route points into proper dataclass instances
        nav_points = self._parse_nav_points(data.Route)

        self.plotted_nav_route = PlottedNavRoute(
            timestamp=timestamp,
            nav_points=nav_points
        )

        # Update helper attributes if needed
        if nav_points:
            self.remaining_jumps_in_route = len(nav_points) - 1

    def clear_plotted_route(self):
        self.plotted_nav_route = None
        self.remaining_jumps_in_route = 0

    def set_current_system_from_journal_data(self, evt):
        system_address = evt.get("SystemAddress")
        self.current_system = None
        if self.remaining_jumps_in_route < len(self.plotted_nav_route.nav_points):
            index = -1 * self.remaining_jumps_in_route
            if self.plotted_nav_route.nav_points[index].system_address == system_address:
                self.current_system = self.plotted_nav_route.nav_points[index]

        if self.current_system is None:
            system_name = evt.get("StarSystem")
            pos = self._parse_star_position(evt.get("StarPos"))

            self.current_system = NavPoint(
                    star_system=system_name,
                    system_address=system_address,
                    star_class="",
                    star_position=pos
                )

    def get_system_by_index(self, system_index: int) -> NavPoint|None:
        return self.plotted_nav_route.nav_points[system_index]

    def get_next_system(self, remaining_jumps_in_route: int|None) -> NavPoint|None:
        """Calculates the next system to show."""
        if not self.plotted_nav_route or len(self.plotted_nav_route.nav_points) < 1:
            return None

        if remaining_jumps_in_route:
            self.remaining_jumps_in_route = remaining_jumps_in_route
        elif self.current_system:
            i = 0
            for system in self.plotted_nav_route.nav_points:
                if system.system_address == self.current_system.system_address:
                    self.remaining_jumps_in_route = len(self.plotted_nav_route.nav_points) - (i + 1)
                    break
                i += 1
        else:
            return None

        system_index = -1 * self.remaining_jumps_in_route

        return self.plotted_nav_route.nav_points[system_index]

    def get_final_destination(self) -> NavPoint|None:
        if not self.plotted_nav_route or len(self.plotted_nav_route.nav_points) < 1:
            return None

        return self.plotted_nav_route.nav_points[-1]

    def get_total_route_distance(self) -> float:
        """Calculates the total jump distance of the entire loaded route."""
        if not self.plotted_nav_route or len(self.plotted_nav_route.nav_points) < 1:
            return 0.0

        total_distance = 0.0
        points = self.plotted_nav_route.nav_points

        for i in range(len(points) - 1):
            total_distance += gn.calculate_star_system_distance(points[i].star_position, points[i + 1].star_position)

        return total_distance

    def get_remaining_route_distance(self) -> float:
        """Calculates the total jump distance of the entire loaded route."""
        if not self.plotted_nav_route or len(self.plotted_nav_route.nav_points) < 2:
            return 0.0

        total_distance = 0.0
        points = self.plotted_nav_route.nav_points

        for i in range(-1, -1*(self.remaining_jumps_in_route+1), -1):
            total_distance += gn.calculate_star_system_distance(points[i].star_position, points[i-1].star_position)

        return total_distance

    def check_and_update_remaining_jump_count(self):
        system_address_remaining_jumps = self.get_system_by_index(-1*(1+self.remaining_jumps_in_route)).system_address
        if self.current_system is None:
            self.current_system = self.plotted_nav_route.nav_points[0]
        system_address_current_system  = self.current_system.system_address

        if system_address_current_system != system_address_remaining_jumps:
            for i in range(-1, -1*len(self.plotted_nav_route.nav_points), -1):
                if self.get_system_by_index(i).system_address == system_address_current_system:
                    self.remaining_jumps_in_route = -1*(i+1)
                    return
