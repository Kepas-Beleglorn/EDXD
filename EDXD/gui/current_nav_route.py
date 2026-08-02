from __future__ import annotations

import wx

from EDXD.data_handler.helper import galactic_navigation
from EDXD.data_handler.nav_route import NavRouteHandler, NavPoint
from EDXD.globals import DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS, DEFAULT_WORTHWHILE_THRESHOLD, DEFAULT_HEIGHT_CURRENT_NAV_ROUTE, DEFAULT_WIDTH_CURRENT_NAV_ROUTE
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.utils.clipboard import copy_text_to_clipboard
from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import EDXD.data_handler.helper.data_helper as dh
import EDXD.data_handler.helper.galactic_navigation as gn
import EDXD.data_handler.helper.technical2humanreadable as t2h

TITLE = "Currently plotted route"
WINID = "PLOTTED_NAV_ROUTE"

class PlottedNavRoute(DynamicDialog):
    def __init__(self, parent, title=TITLE, win_id=WINID, is_hidden: bool = True):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT_CURRENT_NAV_ROUTE, default_width=DEFAULT_WIDTH_CURRENT_NAV_ROUTE, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True, vertical_scroll=True, horizontal_scroll=False)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.theme = get_theme()
        self.parent = parent
        self.body = None
        self.plotted_route: NavRouteHandler|None = None

        self.theme = get_theme()

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # (collapsible) panels with details
        # general data
        self.general_panel = CollapsiblePanel(parent=self.scroll_container, columns=2, label="General", show_toggle_bar=False)
        self.window_box.Add(self.general_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.general_panel.Hide()

        # route visualisation
        self.route_panel = CollapsiblePanel(parent=self.scroll_container, columns=6, label="Route", show_toggle_bar=False)
        self.window_box.Add(self.route_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.route_panel.Hide()

        self.finalize_layout()
        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, plotted_route: NavRouteHandler):
        # reset
        self.general_panel.reset_table()
        self.route_panel.reset_table()

        if plotted_route is None:
            self.general_panel.Hide()
            self.route_panel.Hide()
        else:
            self.plotted_route =  plotted_route
            self._update_general()
            self._update_route()

        if not self.IsShown():
            self.Show()

    # --------------------------------------------------------------
    def _on_show(self, event):
        """First time the window becomes visible."""
        self._ready = True
        event.Skip()


    @staticmethod
    def _plain_name_from_label(raw: str) -> str:
        if not raw:
            return raw
        if " (" in raw:
            raw = raw.split(" (", 1)[0]
        if " - " in raw:
            raw = raw.split(" - ", 1)[0]
        return raw.strip()

    def _on_name_label_double_click(self, evt: wx.Event):
        name = None
        if getattr(self, "body", None):
            name = getattr(self.body, "name", None) or getattr(self.body, "body_name", None)

        if not name and getattr(self, "name_label", None):
            raw = self.lbl_body.GetLabel()
            name = self._plain_name_from_label(raw)

        if name:
            copy_text_to_clipboard(name)
        evt.Skip()

    def _update_general(self):
        if self.plotted_route is None:
            self.general_panel.Hide()
            return

        if not self.general_panel.IsShown():
            self.general_panel.Show()

        final_destination = "Currently no plotted route..."
        if self.plotted_route.plotted_nav_route and len(self.plotted_route.plotted_nav_route.nav_points) > 0:
            final_destination = f"Final destination: {self.plotted_route.get_final_destination().star_system}"

        lbl_final_destination =  self.general_panel.add_table_item(f"{final_destination}")
        theme = wx.Font(self.theme["font_bold"])
        theme.SetPointSize(12)
        lbl_final_destination.SetFont(theme)
        self.general_panel.add_table_item("")

        if self.plotted_route.current_system:
            total_distance = self.plotted_route.get_total_route_distance()
            remaining_distance = gn.calculate_star_system_distance(self.plotted_route.current_system.star_position, self.plotted_route.get_final_destination().star_position)

            lbl_distance = self.general_panel.add_table_item(f"{' '*6}{remaining_distance:.2f} Ly of {total_distance:.2f} Ly remaining")
            lbl_distance.SetFont(self.theme["font_bold"])
            self.general_panel.add_table_item("")

        if self.general_panel.IsShown():
            # Force a layout update
            self.general_panel.force_render()

    def _update_route(self):
        if self.plotted_route is None:
            self.route_panel.Hide()
            return

        if not self.route_panel.IsShown():
            self.route_panel.Show()

        min = -1 * self.plotted_route.amount_of_passed_systems_to_show
        max = self.plotted_route.amount_of_upcoming_systems_to_show

        min = min - self.plotted_route.remaining_jumps_in_route
        max = -1 * (self.plotted_route.remaining_jumps_in_route - max)

        small_font = wx.Font(self.theme["font"])
        small_font.SetPointSize(9)

        tall_font = wx.Font(self.theme["font_bold"])
        tall_font.SetPointSize(16)

        system: NavPoint|None = None
        next_system: NavPoint|None = None

        fixed_height = 20

        for i in  range(min, max, 1):
            if abs(i) > len(self.plotted_route.plotted_nav_route.nav_points) :
                continue

            if len(self.plotted_route.plotted_nav_route.nav_points) - abs(i) < 0:
                print(f"DEBUG[items-abs(i)  <  0]: {len(self.plotted_route.plotted_nav_route.nav_points)} = {abs(i) - len(self.plotted_route.plotted_nav_route.nav_points)} - {abs(i)}")
                continue

            system = self.plotted_route.get_system_by_index(i)
            next_system = self.plotted_route.get_system_by_index(i + 1)
            system_type = ""
            system_feature = ""
            system_name = ""
            distance_next_jump = 0.0
            system_indicator = "O"
            has_jet_cone = False
            if system:
                system_type = system.star_class
                if system_type and system_type != "":
                    if system_type[0] in ("K", "G", "B", "F", "O", "A", "M"):
                        system_feature = ICONS["scoopable"]
                    if system_type[0] in ("N", "D", "T"):
                        has_jet_cone = True
                        system_indicator = "🔵"
                    else:
                        system_indicator = "🟠"
                system_name = system.star_system
                if next_system:
                    distance_next_jump = gn.calculate_star_system_distance(next_system.star_position, system.star_position)

                lbl_system_indicator = self.route_panel.add_table_item(f"{system_indicator}", align=wx.ALIGN_CENTER, line_height=fixed_height)
                self.route_panel.add_table_item(f"", line_height=fixed_height)
                lbl_star_feature = self.route_panel.add_table_item(f"{' '*5}{system_feature}", align=wx.ALIGN_BOTTOM, line_height=fixed_height)
                lbl_star_feature.SetFont(small_font)
                lbl_star_class = self.route_panel.add_table_item(f"[{system_type}]{' '*2}", align=wx.ALIGN_RIGHT, line_height=fixed_height)
                lbl_system = self.route_panel.add_table_item(f"{system_name}", line_height=fixed_height)
                self.route_panel.add_table_item(f"", line_height=fixed_height)

                if abs(i) > abs(max - 1) and abs(i) <= len(self.plotted_route.plotted_nav_route.nav_points):
                    lbl_distance_indicator = self.route_panel.add_table_item(f"|", align=wx.ALIGN_CENTER, line_height=fixed_height)
                    lbl_distance_indicator.SetFont(tall_font)
                    lbl_distance = self.route_panel.add_table_item(f"{' '*2}{distance_next_jump:.2f} Ly", align=wx.ALIGN_CENTER_VERTICAL, line_height=fixed_height)
                    lbl_distance.SetFont(small_font)
                    self.route_panel.add_table_item(f"", line_height=fixed_height)
                    self.route_panel.add_table_item(f"", line_height=fixed_height)
                    self.route_panel.add_table_item(f"", line_height=fixed_height)
                    self.route_panel.add_table_item(f"", line_height=fixed_height)

        if self.route_panel.IsShown():
            # Force a layout update
            self.route_panel.force_render()

    @staticmethod
    def _set_g_force_colour(label: wx.StaticText = None, g_force: float = 0.0):
        if label is None:
            return
        label.SetForegroundColour(dh.get_colour_gradient_from_gravity(g_force))

    @staticmethod
    def _set_temperature_colour(label: wx.StaticText = None, temperature: float = 0.0):
        if label is None:
            return
        label.SetForegroundColour(dh.get_colour_gradient_from_temperature(temperature))

    @staticmethod
    def _set_distance_color(label: wx.StaticText = None, range_min: float = 0.0, range_current: float = 0.0):
        if label is None:
            return

        if range_current * 1000 > range_min:
            label.SetForegroundColour(wx.GREEN)
        else:
            label.SetForegroundColour(wx.RED)
