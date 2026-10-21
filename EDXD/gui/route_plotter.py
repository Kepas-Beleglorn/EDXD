from __future__ import annotations

from dataclasses import asdict
from select import select
from threading import Thread

import wx
from datetime import datetime, UTC
from EDXD.data_handler.helper.spansh import spansh
from EDXD.data_handler.helper.spansh.spansh import SpanshRoutePlotter
from EDXD.data_handler.nav_route import NavRouteHandler, NavPoint
from EDXD.globals import DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS, DEFAULT_HEIGHT, DEFAULT_WIDTH, BASE64_CIRCLE_ORANGE, \
    BASE64_CIRCLE_BLUE, BASE64_LINE_ORANGE, BASE64_LINE_BLUE, SHIP_STATUS_FILE, SPANSH_ROUTE
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.icon_loader import get_bitmap_from_base64
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.utils.clipboard import copy_text_to_clipboard
from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import EDXD.data_handler.helper.data_helper as dh
import EDXD.data_handler.helper.galactic_navigation as gn
from EDXD.utils.int_range_validator import IntRangeValidator
from EDXD.utils.float_range_validator import FloatRangeValidator
from EDXD.data_handler.vessel_status import *
from EDXD.data_handler.helper.dotted_dictionary import *

TITLE = "Exploration itinerary"
WINID = "EXPLORATION_ITINERARY"

LABEL_FIXED_TEXT_LENGTH = 24
BTN_SIZE = wx.Size(250, -1)

ROUTE_PLOTTERS = [
    ("Galaxy Plotter", "galaxy"),
    ("Road to Riches", "riches"),
    ("Expressway to Exomastery", "exobiology"),
    ("Neutron Router", "neutron"),
]

# List of (display, value) tuples
ROUTING_OPTIONS = [
    ("Optimistic", "optimistic"),
    ("Fuel", "fuel"),
    ("Fuel Jumps", "fuel_jumps"),
    ("Guided", "guided"),
    ("Pessimistic", "pessimistic")
]

class ExplorationItinerary(DynamicDialog):
    def __init__(self, parent, title=TITLE, win_id=WINID, is_hidden: bool = True):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True, vertical_scroll=True, horizontal_scroll=False)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.theme = get_theme()
        self.itinerary = None
        self.copied_system_name: str = ""

        self.parent = parent
        self.ship_status = parent.parent.journal_controller.ship_status
        if self.ship_status is None:
            self.ship_status = ShipStatus()
        self.ship_status = self.ship_status.read_from_json(dh.read_ship_status(SHIP_STATUS_FILE, self.ship_status))
        self.body = None
        self.nav_route: NavRouteHandler | None = None

        self.theme = get_theme()

        self.BMP_CIRCLE_ORANGE = get_bitmap_from_base64(BASE64_CIRCLE_ORANGE, 20)
        self.BMP_CIRCLE_BLUE = get_bitmap_from_base64(BASE64_CIRCLE_BLUE, 20)
        self.BMP_LINE_ORANGE = get_bitmap_from_base64(BASE64_LINE_ORANGE, 20)
        self.BMP_LINE_BLUE = get_bitmap_from_base64(BASE64_LINE_BLUE, 20)

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # (collapsible) panels with details
        # select route plotter
        self.plotter_select_panel = CollapsiblePanel(parent=self.scroll_container, columns=3, label="Select Plotter", show_toggle_bar=False)
        self.window_box.Add(self.plotter_select_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.plotter_select_panel.Hide()

        # spansh parameters
        self.parameter_panel = CollapsiblePanel(parent=self.scroll_container, columns=3, label="Route parameters", show_toggle_bar=True)
        self.window_box.Add(self.parameter_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.parameter_panel.Hide()

        # general data
        self.general_panel = CollapsiblePanel(parent=self.scroll_container, columns=2, label="General", show_toggle_bar=False)
        self.window_box.Add(self.general_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.general_panel.Hide()

        # route visualisation
        self.route_panel = CollapsiblePanel(parent=self.scroll_container, columns=6, label="Route", show_toggle_bar=False)
        self.window_box.Add(self.route_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.route_panel.Hide()

        self.routing_algo = "optimistic"
        self.selected_plotter = "galaxy"

        self.finalize_layout()
        self._update_plotter_select()
        self._update_parameter()

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)

        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    def _on_timer(self, event):
        if self._check_waypoint():
            self.general_panel.reset_table()
            self.route_panel.reset_table()
            self._update_general()
            self._update_route()

    def render(self):
        self.general_panel.reset_table()
        self.route_panel.reset_table()

        if self.nav_route is None:
            if self._timer.IsRunning():
                self._timer.Stop()
            self.general_panel.Hide()
            self.route_panel.Hide()
        else:
            if not self._timer.IsRunning():
                self._timer.Start(1000)  # 1000 ms = 1 second
            self._update_route()
            self._update_general()

        if not self.IsShown():
            self.Show()

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
        # Retrieve the label that triggered the event
        label = evt.GetEventObject()

        if not name and label:
            raw = label.GetLabelText()
            name = self._plain_name_from_label(raw)

        if name:
            copy_text_to_clipboard(name)

        evt.Skip()

    def _on_routing_changed(self, event):
        selected_display = self.cmb_routing_algorithm.GetValue()
        # Find the corresponding value
        selected_value = next(
            (value for display, value in ROUTING_OPTIONS if display == selected_display),
            None
        )
        self.routing_algo = selected_value

    def _on_plotter_changed(self, event):
        selected_display = self.cmb_selected_plotter.GetValue()
        # Find the corresponding value
        selected_value = next(
            (value for display, value in ROUTE_PLOTTERS if display == selected_display),
            None
        )
        self.selected_plotter = selected_value
        self._update_parameter()

    def  _on_load_route(self, event):
        path = Path(SPANSH_ROUTE)
        if not path.exists():
            self.lbl_job_status.SetLabel("  No previous route found.")
            return

        self.nav_route = NavRouteHandler(
            SPANSH_ROUTE,
            amount_of_upcoming_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_upcoming_systems_to_show"]),
            amount_of_passed_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_passed_systems_to_show"])
        )
        self.nav_route.clear_plotted_route()
        self.nav_route.load_plotted_route()
        self._check_waypoint()
        self.render()

    def  _on_calculate_route(self, event):
        spansh = SpanshRoutePlotter()

        self.nav_route  = None
        self.render()

        # ToDo: implement switch according to selected plotter
        self.job_id: str | None = spansh.galaxy_plotter(
            source_system_name=self.txt_source_system.GetValue(),
            destination_system_name=self.txt_destination_system.GetValue(),
            cargo=int(self.txt_cargo.GetValue()),
            reserve_fuel=int(self.txt_reserve_fuel.GetValue()),
            already_supercharged=bool(self.btn_already_supercharged.GetValue()),
            use_supercharge=bool(self.btn_use_supercharged.GetValue()),
            fsd_inject_always=bool(self.btn_use_fsd_injections_always.GetValue()),
            fsd_inject_when_required=bool(self.btn_use_fsd_injections_when_required.GetValue()),
            exclude_secondary=bool(self.btn_exclude_secondary_stars.GetValue()),
            refuel_every_scoopable=bool(self.btn_refuel_every_scoopable.GetValue()),
            algorithm=self.routing_algo)

        # Start the background worker; it updates the label while polling
        self.worker = PlotterWorker(
            self.job_id,
            on_progress=self.update_status,
            on_done=self.on_plot_done,
        )
        self.worker.start()

    def update_status(self, state: str, status: str, duration: str):
        # Called on the MAIN thread via wx.CallAfter — safe to touch widgets
        self.lbl_job_status.SetLabel(f"  Plotting… {duration}")

    def on_plot_done(self, result: DotDict | None):
        self.nav_route  = None
        if result:
            self.lbl_job_status.SetLabel("  Route ready!")
            self.itinerary: DotDict = result
            self.itinerary.timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

            save_dotdict_to_json(self.itinerary, SPANSH_ROUTE)

            self.nav_route = NavRouteHandler(
                SPANSH_ROUTE,
                amount_of_upcoming_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_upcoming_systems_to_show"]),
                amount_of_passed_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_passed_systems_to_show"])
            )
            self.nav_route.clear_plotted_route()
            self.nav_route.load_plotted_route()
            self._check_waypoint(self.nav_route.plotted_nav_route.nav_points[0])
        else:
            self.lbl_job_status.SetLabel("  Plotting failed.")

        self.render()

    def _update_plotter_select(self):
        if not self.plotter_select_panel.IsShown():
            self.plotter_select_panel.Show()

        self.plotter_select_panel.add_table_item_label(label_text=f"Selected plotter", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)

        # Extract display texts for the dropdown
        display_texts = [opt[0] for opt in ROUTE_PLOTTERS]

        # Create combobox
        self.cmb_selected_plotter = wx.ComboBox(choices=display_texts, style=wx.CB_READONLY, parent=self.plotter_select_panel.content, size=BTN_SIZE)
        self.cmb_selected_plotter.SetValue(display_texts[0])  # Set default
        self.cmb_selected_plotter.Bind(wx.EVT_LEFT_DOWN, lambda e: None)

        # Bind event to handle selection
        self.cmb_selected_plotter.Bind(wx.EVT_COMBOBOX, self._on_plotter_changed)

        self.plotter_select_panel.add_table_item_generic(self.cmb_selected_plotter)
        self.plotter_select_panel.add_table_item_label("")

    def _update_parameter(self):
        if not self.parameter_panel.IsShown():
            self.parameter_panel.Show()

        self.parameter_panel.reset_table()

        self.parameter_panel.add_table_item_label(label_text=f"Source System", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
        self.txt_source_system = self.parameter_panel.add_table_item_textbox()
        self.parameter_panel.add_table_item_label("")

        self.parameter_panel.add_table_item_label(label_text=f"Destination System", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
        self.txt_destination_system = self.parameter_panel.add_table_item_textbox(width=BTN_SIZE.width)
        self.parameter_panel.add_table_item_label("")

        match self.selected_plotter:
            case "galaxy":
                self.parameter_panel.add_table_item_label(label_text=f"Cargo", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_cargo = self.parameter_panel.add_table_item_textbox()
                self.txt_cargo.SetValidator(IntRangeValidator(min_val=0, max_val=self.ship_status.cargo_capacity, allow_empty=False))
                self.txt_cargo.SetValue(str(self.ship_status.cargo))
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label(label_text=f"Reserve fuel", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_reserve_fuel = self.parameter_panel.add_table_item_textbox()
                self.txt_reserve_fuel.SetValidator(IntRangeValidator(min_val=0, max_val=self.ship_status.fuel_capacity.main, allow_empty=False))
                self.txt_reserve_fuel.SetValue("0")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.btn_already_supercharged = DynamicToggleButton(
                    label="Already supercharged",
                    parent=self.parameter_panel.content,
                    is_toggled=self.ship_status.jet_cone_boost_factor is not None,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_already_supercharged)

                self.btn_use_supercharged = DynamicToggleButton(
                    label="Use supercharge",
                    parent=self.parameter_panel.content,
                    is_toggled=True,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_use_supercharged)
                self.parameter_panel.add_table_item_label("")

                self.btn_use_fsd_injections_always = DynamicToggleButton(
                    label="Use FSD injections always",
                    parent=self.parameter_panel.content,
                    is_toggled=False,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_use_fsd_injections_always)

                self.btn_use_fsd_injections_when_required = DynamicToggleButton(
                    label="Use FSD injections when required",
                    parent=self.parameter_panel.content,
                    is_toggled=False,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_use_fsd_injections_when_required)
                self.parameter_panel.add_table_item_label("")

                self.btn_exclude_secondary_stars = DynamicToggleButton(
                    label="Exclude secondary stars",
                    parent=self.parameter_panel.content,
                    is_toggled=False,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_exclude_secondary_stars)

                self.btn_refuel_every_scoopable = DynamicToggleButton(
                    label="Refuel  every scoopable",
                    parent=self.parameter_panel.content,
                    is_toggled=True,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_refuel_every_scoopable)
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label(label_text=f"Routing algorithm", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)

                # Extract display texts for the dropdown
                display_texts = [opt[0] for opt in ROUTING_OPTIONS]

                # Create combobox
                self.cmb_routing_algorithm = wx.ComboBox(choices=display_texts, style=wx.CB_READONLY, parent=self.parameter_panel.content, size=BTN_SIZE)
                self.cmb_routing_algorithm.SetValue(display_texts[0])  # Set default
                self.cmb_routing_algorithm.Bind(wx.EVT_LEFT_DOWN, lambda e: None)

                # Bind event to handle selection
                self.cmb_routing_algorithm.Bind(wx.EVT_COMBOBOX, self._on_routing_changed)

                self.parameter_panel.add_table_item_generic(self.cmb_routing_algorithm)
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
            case  "riches":
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label(label_text=f"Leave destination blank in order to create a circular tour starting at your source system and returning there at the end.", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width, line_height=80)
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label(label_text=f"Max. Jump Range (LY)", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_jump_range = self.parameter_panel.add_table_item_textbox()
                self.txt_jump_range.SetValidator(FloatRangeValidator(min_val=0, max_val=self.ship_status.max_jump_range, allow_empty=False))
                self.txt_jump_range.SetValue(str(self.ship_status.max_jump_range))
                self.parameter_panel.add_table_item_label("")

        self.btn_calculate_route = DynamicButton(parent=self.parameter_panel.content, label="Calculate route", size=BTN_SIZE)
        self.btn_calculate_route.Bind(wx.EVT_BUTTON, self._on_calculate_route)
        self.parameter_panel.add_table_item_generic(self.btn_calculate_route)

        self.lbl_job_status = self.parameter_panel.add_table_item_label(label_text="", align=wx.ALIGN_BOTTOM)
        self.parameter_panel.add_table_item_label("")

        self.btn_load_route = DynamicButton(parent=self.parameter_panel.content, label="Load last route", size=BTN_SIZE)
        self.btn_load_route.Bind(wx.EVT_BUTTON, self._on_load_route)
        self.parameter_panel.add_table_item_generic(self.btn_load_route)
        self.parameter_panel.add_table_item_label("")
        self.parameter_panel.add_table_item_label("")

        self.parameter_panel.add_table_item_label("")
        self.parameter_panel.add_table_item_label("")
        self.parameter_panel.add_table_item_label("")

        if self.parameter_panel.IsShown():
            # Force a layout update
            self.parameter_panel.force_render()

    def _update_general(self):
        if self.nav_route is None or self.nav_route.plotted_nav_route is None or len(self.nav_route.plotted_nav_route.nav_points) < 1:
            self.general_panel.Hide()
            return

        if not self.general_panel.IsShown():
            self.general_panel.Show()

        final_destination = "Currently no plotted route..."
        if self.nav_route.plotted_nav_route and len(self.nav_route.plotted_nav_route.nav_points) > 0:
            final_destination = f"Final destination: {self.nav_route.get_final_destination().star_system}"

        lbl_final_destination = self.general_panel.add_table_item_label(f"{final_destination}")
        theme = wx.Font(self.theme["font_bold"])
        theme.SetPointSize(12)
        lbl_final_destination.SetFont(theme)
        self.general_panel.add_table_item_label("")

        if self.nav_route.current_system:
            total_distance = self.nav_route.get_total_route_distance()
            remaining_distance = self.nav_route.get_remaining_route_distance()

            lbl_distance = self.general_panel.add_table_item_label(f"{' ' * 6}{remaining_distance:,.2f} Ly of {total_distance:,.2f} Ly ({self.nav_route.remaining_jumps_in_route - 1} jumps) remaining")
            self.general_panel.add_table_item_label("")
            self.general_panel.add_table_item_label("", line_height=20)

        if self.general_panel.IsShown():
            # Force a layout update
            self.general_panel.force_render()

    def _update_route(self):
        if self.nav_route is None or self.nav_route.plotted_nav_route is None or len(self.nav_route.plotted_nav_route.nav_points) < 1:
            self.route_panel.Hide()
            return

        if not self.route_panel.IsShown():
            self.route_panel.Show()

        self.nav_route.check_and_update_remaining_jump_count()

        min = -1 * (self.nav_route.amount_of_passed_systems_to_show + 1)
        max = self.nav_route.amount_of_upcoming_systems_to_show

        if max > self.nav_route.remaining_jumps_in_route:
            max = self.nav_route.remaining_jumps_in_route

        min = min - self.nav_route.remaining_jumps_in_route
        max = -1 * (self.nav_route.remaining_jumps_in_route - max)

        small_font = wx.Font(self.theme["font"])
        small_font.SetPointSize(9)

        tall_font = wx.Font(self.theme["font_bold"])
        tall_font.SetPointSize(16)

        passed_colour = self.theme["foreground_less"]
        current_bg_colour = self.theme["background_hover"]
        jet_cone_colour = wx.Colour(0, 165, 255)

        final_destination_address = self.nav_route.get_final_destination().system_address

        system: NavPoint | None = None
        next_system: NavPoint | None = None

        fixed_height = 20

        if self.nav_route.plotted_nav_route:
            for i in range(min, max, 1):
                if i == 0:
                    break

                if abs(i) > len(self.nav_route.plotted_nav_route.nav_points):
                    continue

                if len(self.nav_route.plotted_nav_route.nav_points) - abs(i) < 0:
                    print(f"DEBUG[items-abs(i)  <  0]: {len(self.nav_route.plotted_nav_route.nav_points)} = {abs(i) - len(self.nav_route.plotted_nav_route.nav_points)} - {abs(i)}")
                    continue

                system = self.nav_route.get_system_by_index(i)
                next_system = self.nav_route.get_system_by_index(i + 1)
                system_type = ""
                system_feature = ""
                system_name = ""
                distance_next_jump = 0.0
                has_jet_cone = False
                system_indicator = self.BMP_CIRCLE_ORANGE
                distance_indicator = self.BMP_LINE_ORANGE

                if system:
                    system_type = system.star_class
                    if system_type and system_type != "":
                        if system_type[0] in ("K", "G", "B", "F", "O", "A", "M"):
                            system_feature = ICONS["scoopable"]
                        if system_type[0] in ("N", "D"):
                            has_jet_cone = True
                            system_indicator = self.BMP_CIRCLE_BLUE
                            distance_indicator = self.BMP_LINE_BLUE

                    system_name = system.star_system
                    system_address = system.system_address

                    if next_system:
                        distance_next_jump = gn.calculate_star_system_distance(next_system.star_position, system.star_position)

                    lbl_1_system_indicator = self.route_panel.add_table_item_bitmap(system_indicator, 20)
                    lbl_2_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)
                    if final_destination_address == system_address:
                        lbl_2_space.SetLabelText(f"{' ' * 5}{ICONS["final"]}")
                    lbl_3_star_feature = self.route_panel.add_table_item_label(f"{' ' * 5}{system_feature}{'  ' * 2}", line_height=fixed_height)
                    lbl_4_star_class = self.route_panel.add_table_item_label(f"[{system_type}]", line_height=fixed_height)
                    lbl_5_system = self.route_panel.add_table_item_label(f"{' ' * 2}{system_name}", line_height=fixed_height)
                    lbl_5_system.Bind(wx.EVT_LEFT_DCLICK, self._on_name_label_double_click)
                    lbl_6_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)

                    if has_jet_cone:
                        lbl_1_system_indicator.SetForegroundColour(jet_cone_colour)
                        lbl_2_space.SetForegroundColour(jet_cone_colour)
                        lbl_3_star_feature.SetForegroundColour(jet_cone_colour)
                        lbl_4_star_class.SetForegroundColour(jet_cone_colour)
                        lbl_5_system.SetForegroundColour(jet_cone_colour)
                        lbl_6_space.SetForegroundColour(jet_cone_colour)

                    if abs(i) > self.nav_route.remaining_jumps_in_route + 1:
                        lbl_1_system_indicator.SetForegroundColour(passed_colour)
                        lbl_2_space.SetForegroundColour(passed_colour)
                        lbl_3_star_feature.SetForegroundColour(passed_colour)
                        lbl_4_star_class.SetForegroundColour(passed_colour)
                        lbl_5_system.SetForegroundColour(passed_colour)
                        lbl_6_space.SetForegroundColour(passed_colour)

                    if abs(i) == self.nav_route.remaining_jumps_in_route + 1:
                        lbl_4_star_class.SetFont(wx.Font(self.theme["font_bold"]))
                        lbl_5_system.SetFont(wx.Font(self.theme["font_bold"]))

                        lbl_1_system_indicator.SetBackgroundColour(current_bg_colour)
                        lbl_2_space.SetBackgroundColour(current_bg_colour)
                        lbl_3_star_feature.SetBackgroundColour(current_bg_colour)
                        lbl_4_star_class.SetBackgroundColour(current_bg_colour)
                        lbl_5_system.SetBackgroundColour(current_bg_colour)
                        lbl_6_space.SetBackgroundColour(current_bg_colour)

                    if abs(i) > abs(max - 1) and abs(i) <= len(self.nav_route.plotted_nav_route.nav_points):
                        lbl_1_distance_indicator = self.route_panel.add_table_item_bitmap(distance_indicator, line_height=fixed_height)
                        lbl_2_distance = self.route_panel.add_table_item_label(f"{' ' * 2}{distance_next_jump:.2f} Ly", align=wx.ALIGN_CENTER_VERTICAL, line_height=fixed_height)
                        lbl_2_distance.SetFont(small_font)
                        lbl_3_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)
                        lbl_4_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)
                        lbl_5_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)
                        lbl_6_space = self.route_panel.add_table_item_label(f"", line_height=fixed_height)

        if self.route_panel.IsShown():
            # Force a layout update
            self.route_panel.force_render()

    def _check_waypoint(self, current_waypoint: NavPoint | None = None) -> bool:
        spansh_route_data: DotDict = load_json_as_dotdict(SPANSH_ROUTE)
        current_system: NavPoint
        if hasattr(spansh_route_data, "current_system"):
            current_system: NavPoint = from_dotdict(NavPoint, spansh_route_data.current_system)
        else:
            if current_waypoint is None:
                return False
            else:
                current_system = current_waypoint

        current_system_address: int = current_system.system_address

        do_copy_to_clipboard: bool = False

        for system in spansh_route_data.jumps:
            # If we've reached a waypoint, copy the next name to the clipboard
            if do_copy_to_clipboard:
                if self.copied_system_name != system.name:
                    self.copied_system_name = system.name
                    copy_text_to_clipboard(system.name)
                    return True
                else:
                    return False

            # check if we reached a waypoint
            if system.id64 == current_system_address:
                self.nav_route.current_system = current_system
                self._save_last_waypoint_system(spansh_route_data, current_system)
                do_copy_to_clipboard = True

        return False

    def _on_close(self,event):
        self._timer.Stop()
        event.Skip()

    @staticmethod
    def _save_last_waypoint_system(spansh_route_data: DotDict, current_system: NavPoint):
        spansh_route_data.last_waypoint = DotDict(asdict(current_system))
        save_dotdict_to_json(spansh_route_data, SPANSH_ROUTE)

class PlotterWorker(Thread):
    """Runs get_itinerary off the main thread and delivers the result back via wx.CallAfter."""
    def __init__(self, job_id: str | None, on_progress, on_done):
        super().__init__(daemon=True)
        self.job_id = job_id
        self.on_progress = on_progress   # callable(state, status, duration)
        self.on_done = on_done           # callable(result: DotDict | None)

    def run(self):
        # get_itinerary calls on_progress from this thread; we must marshal
        # those to the GUI thread with wx.CallAfter, so wrap them here.
        def gui_progress(state, status, duration):
            wx.CallAfter(self.on_progress, state, status, duration)

        result = spansh.get_itinerary(self.job_id, progress_callback=gui_progress)

        # Deliver the final result back onto the main thread
        wx.CallAfter(self.on_done, result)