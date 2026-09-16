import json
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pywinctl, wx

import EDXD.data_handler.helper.galactic_navigation as gn
import EDXD.data_handler.helper.data_helper as dh
from EDXD.data_handler.helper.json_helper import DotDict
from EDXD.data_handler.helper.galactic_navigation import StarPosition
from EDXD.gui.themed_msg_dialog import ThemedMessageDialog

ERR_TITLE = "Navigation error"
ERR_MSG = "Please clear the route and calculate it fresh.\nThe game does not update 'NavRoute.json' on 'Recalculate Route'."


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
        if not self.nav_route_json.exists():
            return

        raw_data = self.nav_route_json.read_text()
        if len(raw_data) == 0:
            return

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
        if not self.nav_route_json.exists():
            return

        if self.plotted_nav_route is None:
            return

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
        if self.plotted_nav_route and len(self.plotted_nav_route.nav_points) > 0 :
            try:
                return self.plotted_nav_route.nav_points[system_index]
            except IndexError as ie:
                self._show_message(ERR_TITLE, ERR_MSG, ie)
        else:
            return None

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

        try:
            for i in range(-1, -1*(self.remaining_jumps_in_route+1), -1):
                total_distance += gn.calculate_star_system_distance(points[i].star_position, points[i-1].star_position)
        except IndexError as ie:
            self._show_message(ERR_TITLE, ERR_MSG, ie)

        return total_distance

    def check_and_update_remaining_jump_count(self):
        system_remaining_jumps = self.get_system_by_index(-1*(1+self.remaining_jumps_in_route))
        if system_remaining_jumps:
            system_address_remaining_jumps = self.get_system_by_index(-1*(1+self.remaining_jumps_in_route)).system_address
            if self.current_system is None:
                self.current_system = self.plotted_nav_route.nav_points[0]
            system_address_current_system  = self.current_system.system_address

            if system_address_current_system != system_address_remaining_jumps:
                for i in range(-1, -1*len(self.plotted_nav_route.nav_points), -1):
                    if self.get_system_by_index(i).system_address == system_address_current_system:
                        self.remaining_jumps_in_route = -1*(i+1)
                        return

    def check_nav_route_consistency(self, remaining_jumps: int, target_system_address: int):
        if remaining_jumps > len(self.plotted_nav_route.nav_points):
            self._show_message(ERR_TITLE, ERR_MSG, None)
            return

        try:
            if self.get_system_by_index(-1*remaining_jumps).system_address != target_system_address:
                self._show_message(ERR_TITLE, ERR_MSG, None)
                return
        except IndexError as ie:
            self._show_message(ERR_TITLE, ERR_MSG, ie)
            return

    def _show_message(self, title: str, message: str|None, ie: IndexError|None) -> None:
        if ie is not None:
            print(f"IndexError: {ie}\n{ERR_MSG}")

        if self.is_window_visible("PLOTTED_NAV_ROUTE"):
            try:
                dlg = ThemedMessageDialog(None, message, title, False)
                dlg.ShowModal()
                dlg.Destroy()
            except Exception as ex:
                print(ex)


    def is_window_visible(self, window_title_part: str) -> bool:
        """
        Checks if a window containing 'window_title_part' in its title is currently visible.
        """
        # Get all windows with the title
        windows = pywinctl.getWindowsWithTitle(window_title_part)

        if not windows:
            return False

        # Check if at least one of them is visible
        # Note: On Linux, 'isVisible' checks if the window is mapped and not minimized
        for win in windows:
            if win.isVisible:
                return True
        return False

