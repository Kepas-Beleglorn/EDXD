from __future__ import annotations

from dataclasses import asdict
from select import select
from threading import Thread

import wx
from  EDXD.data_handler.helper.spansh.spansh import SpanshHelper
from datetime import datetime, UTC
from EDXD.data_handler.helper.spansh import spansh
from EDXD.data_handler.helper.spansh.ship_modules import ShipFSDModules
from EDXD.data_handler.helper.spansh.spansh import SpanshRoutePlotter
from EDXD.data_handler.nav_route import NavRouteHandler, NavPoint
from EDXD.globals import DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS, DEFAULT_HEIGHT_SPANSH, DEFAULT_WIDTH_SPANSH, BASE64_CIRCLE_ORANGE, \
    BASE64_CIRCLE_BLUE, BASE64_LINE_ORANGE, BASE64_LINE_BLUE, SHIP_STATUS_FILE, SPANSH_ROUTE, SLEF_PATH, SPANSH_ACTIVE_ROUTE
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.icon_loader import get_bitmap_from_base64
from EDXD.gui.helper.theme_handler import get_theme, apply_theme
from EDXD.gui.helper.themed_slider import ThemedSlider
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

SLIDER_FIXED_HEIGHT = 24
BTN_SIZE = wx.Size(250, 38)

ROUTE_PLOTTERS = [
    ("Galaxy Plotter", "galaxy"),
    ("Road to Riches", "riches"),
    ("Expressway to Exomastery", "exobiology"),
    ("Ammonia World Route", "ammonia"),
    ("Earth-like World Route", "earth"),
    ("Rocky body / High metal content world Route", "rocky")
#    ("Neutron Router", "neutron"),
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
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT_SPANSH, default_width=DEFAULT_WIDTH_SPANSH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True, vertical_scroll=True, horizontal_scroll=False)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.sh = SpanshHelper()
        self.theme = get_theme()
        self.itinerary = None
        self.copied_system_name: str = ""

        self.parent = parent

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
        self._last_route_for_selected_plotter: Path = Path(str(SPANSH_ROUTE).replace("XXX", self.selected_plotter))
        dh.update_spansh_active_plotted_route(SPANSH_ACTIVE_ROUTE, str(self._last_route_for_selected_plotter))

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

    def _on_routing_loaded(self, algo_value):

        # Find the corresponding value
        display_value = next(
            (display for display, value in ROUTING_OPTIONS if value == algo_value),
            None
        )
        self.cmb_routing_algorithm.SetValue(display_value)
        self.routing_algo = algo_value

    def _on_plotter_changed(self, event):
        selected_display = self.cmb_selected_plotter.GetValue()
        # Find the corresponding value
        selected_value = next(
            (value for display, value in ROUTE_PLOTTERS if display == selected_display),
            None
        )
        self.selected_plotter = selected_value
        self._last_route_for_selected_plotter: Path = Path(str(SPANSH_ROUTE).replace("XXX", self.selected_plotter))
        self._update_parameter()
        self.nav_route = None
        self.render()
        dh.update_spansh_active_plotted_route(SPANSH_ACTIVE_ROUTE, str(self._last_route_for_selected_plotter))

    def  _on_load_route(self, event):
        self.lbl_job_status.SetLabel("")
        self.lbl_loading_status.SetLabel("")
        path = self._last_route_for_selected_plotter
        if not path.exists():
            self.lbl_loading_status.SetLabel(f"No previous route found for \n{self.cmb_selected_plotter.GetValue()}.")
            self.lbl_loading_status.Update()
            return

        self._loading_precalculated_route = True
        self.lbl_loading_status.SetLabel(f"Loading last route for \n{self.cmb_selected_plotter.GetValue()}...")
        self.lbl_loading_status.Update()
        self._load_parameters_from_file(path)
        self.Update()
        self.nav_route = NavRouteHandler(
            self._last_route_for_selected_plotter,
            amount_of_upcoming_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_upcoming_systems_to_show"]),
            amount_of_passed_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_passed_systems_to_show"]),
            progress_cb=self._on_parse_progress
        )
        self.nav_route.clear_plotted_route()
        self.nav_route.load_plotted_route()
        self._check_waypoint()
        self.render()
        self.lbl_loading_status.SetLabel("Previous route loaded.")
        self.lbl_loading_status.Update()

    def _load_parameters_from_file(self, json_file: Path):
        if not json_file.exists():
            return

        raw_data = json_file.read_text()
        if len(raw_data) == 0:
            return

        data = DotDict(json.loads(raw_data))

        if hasattr(data, "parameters") and data.parameters:
            match self.selected_plotter:
                case "galaxy":
                    if hasattr(data.parameters, "source_system"): self.txt_source_system.SetValue(data.parameters.source_system)
                    if hasattr(data.parameters, "destination_system"): self.txt_destination_system.SetValue(data.parameters.destination_system)
                    if hasattr(data.parameters, "cargo"): self.txt_cargo.SetValue(str(data.parameters.cargo))
                    if hasattr(data.parameters, "reserve_size"): self.txt_reserve_fuel.SetValue(str(data.parameters.reserve_size))
                    if hasattr(data.parameters, "is_supercharged"):
                        toggled = data.parameters.is_supercharged
                        self.btn_already_supercharged._is_toggled = toggled
                        self.btn_already_supercharged.SetValue(toggled)
                    if hasattr(data.parameters, "use_supercharge"):
                        toggled = data.parameters.use_supercharge
                        self.btn_use_supercharged._is_toggled = toggled
                        self.btn_use_supercharged.SetValue(toggled)
                    if hasattr(data.parameters, "use_injections"):
                        toggled = data.parameters.use_injections
                        self.btn_use_fsd_injections_always._is_toggled = toggled
                        self.btn_use_fsd_injections_always.SetValue(toggled)
                    if hasattr(data.parameters, "use_injections_when_required"):
                        toggled = data.parameters.use_injections_when_required
                        self.btn_use_fsd_injections_when_required._is_toggled = toggled
                        self.btn_use_fsd_injections_when_required.SetValue(toggled)
                    if hasattr(data.parameters, "exclude_secondary"):
                        toggled = data.parameters.exclude_secondary
                        self.btn_exclude_secondary_stars._is_toggled = toggled
                        self.btn_exclude_secondary_stars.SetValue(toggled)
                    if hasattr(data.parameters, "refuel_every_scoopable"):
                        toggled = (data.parameters.refuel_every_scoopable == 1)
                        self.btn_refuel_every_scoopable._is_toggled = toggled
                        self.btn_refuel_every_scoopable.SetValue(toggled)
                    if hasattr(data.parameters, "algorithm"): self._on_routing_loaded(data.parameters.algorithm)

                case _:
                    if hasattr(data.parameters, "source"): self.txt_source_system.SetValue(data.parameters.source)
                    if hasattr(data.parameters, "destination"): self.txt_destination_system.SetValue(data.parameters.destination)
                    else: self.txt_destination_system.Clear()
                    if hasattr(data.parameters, "range"): self.txt_jump_range.SetValue(data.parameters.range)
                    if hasattr(data.parameters, "radius"): self.txt_stray_radius.SetValue(data.parameters.radius)
                    if hasattr(data.parameters, "max_results"): self.txt_max_systems.SetValue(data.parameters.max_results)
                    if hasattr(data.parameters, "use_mapping_value") and hasattr(self, "btn_use_mapping_value"):
                        toggled = (int(data.parameters.use_mapping_value) == 1)
                        self.btn_use_mapping_value._is_toggled = toggled
                        self.btn_use_mapping_value.SetValue(toggled)
                    if hasattr(data.parameters, "avoid_thargoids"):
                        toggled = (int(data.parameters.avoid_thargoids) == 1)
                        self.btn_avoid_thargoids._is_toggled = toggled
                        self.btn_avoid_thargoids.SetValue(toggled)
                    if hasattr(data.parameters, "loop"):
                        toggled = (int(data.parameters.loop) == 1)
                        self.btn_loop_route._is_toggled = toggled
                        self.btn_loop_route.SetValue(toggled)
                    if hasattr(data.parameters, "min_value") and hasattr(self, "spin_min_scan_value") and hasattr(self, "sld_min_scan_value"):
                        self.spin_min_scan_value.SetValue(int(data.parameters.min_value))
                        self.sld_min_scan_value.SetValue(int(data.parameters.min_value))
                    if hasattr(data.parameters, "max_distance"):
                        self.spin_max_distance_to_arrival.SetValue(int(data.parameters.max_distance))
                        self.sld_max_distance_to_arrival.SetValue(int(data.parameters.max_distance))

    def  _on_calculate_route(self, event):
        spansh = SpanshRoutePlotter()
        self.lbl_job_status.SetLabel("")
        self.lbl_loading_status.SetLabel("")
        self.nav_route  = None
        self.render()
        self.job_id: str | None = None

        match self.selected_plotter:
            case "galaxy":
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
            case "riches":
                self.job_id: str | None = spansh.road_to_riches(
                    source_system_name=self.txt_source_system.GetValue(),
                    destination_system_name=self.txt_destination_system.GetValue(),
                    jump_range=float(self.txt_jump_range.GetValue()),
                    stray_radius=int(self.txt_stray_radius.GetValue()),
                    max_systems=int(self.txt_max_systems.GetValue()),
                    use_mapped_value=self.btn_use_mapping_value.GetValue(),
                    avoid_thargoids=self.btn_avoid_thargoids.GetValue(),
                    loop_back=self.btn_loop_route.GetValue(),
                    max_distance_from_arrival=self.spin_max_distance_to_arrival.GetValue(),
                    min_scan_value=self.spin_min_scan_value.GetValue(),
                    riches_mode=self.selected_plotter)

            case "exobiology":
                self.job_id: str | None = spansh.exobiology(
                    source_system_name=self.txt_source_system.GetValue(),
                    destination_system_name=self.txt_destination_system.GetValue(),
                    jump_range=float(self.txt_jump_range.GetValue()),
                    stray_radius=int(self.txt_stray_radius.GetValue()),
                    max_systems=int(self.txt_max_systems.GetValue()),
                    avoid_thargoids=self.btn_avoid_thargoids.GetValue(),
                    loop_back=self.btn_loop_route.GetValue(),
                    max_distance_from_arrival=self.spin_max_distance_to_arrival.GetValue(),
                    min_scan_value=self.spin_min_scan_value.GetValue())
            case "neutron":
                pass
            case _:
                self.job_id: str | None = spansh.road_to_riches(
                    source_system_name=self.txt_source_system.GetValue(),
                    destination_system_name=self.txt_destination_system.GetValue(),
                    jump_range=float(self.txt_jump_range.GetValue()),
                    stray_radius=int(self.txt_stray_radius.GetValue()),
                    max_systems=int(self.txt_max_systems.GetValue()),
                    avoid_thargoids=self.btn_avoid_thargoids.GetValue(),
                    loop_back=self.btn_loop_route.GetValue(),
                    max_distance_from_arrival=self.spin_max_distance_to_arrival.GetValue(),
                    riches_mode=self.selected_plotter)

        job_dict: DotDict = create_dot_dict_from_string(str(self.job_id))
        if hasattr(job_dict, "error"):
            self.lbl_job_status.SetLabel(f"Plotting failed.\n{job_dict.error}")
        else:
            # Start the background worker; it updates the label while polling
            self.worker = PlotterWorker(
                self.job_id,
                on_progress=self.update_status,
                on_done=self.on_plot_done,
            )
            self.worker.start()

    def update_status(self, state: str, status: str, duration: str):
        # Called on the MAIN thread via wx.CallAfter — safe to touch widgets
        self.lbl_job_status.SetLabel(f"Plotting…\n{duration}")

    def on_plot_done(self, result: DotDict | None):
        self.nav_route  = None
        self._loading_precalculated_route = False
        if result:
            if not hasattr(result, "error"):
                self.itinerary: DotDict = DotDict(result)
                self.itinerary.timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

                # Enrich jumps with StarClass before persisting
                self._enrich_route_with_star_classes(self.itinerary.jumps)

                save_dotdict_to_json(self.itinerary, str(self._last_route_for_selected_plotter))

                self.nav_route = NavRouteHandler(
                    self._last_route_for_selected_plotter,
                    amount_of_upcoming_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_upcoming_systems_to_show"]),
                    amount_of_passed_systems_to_show=int(self.parent.parent.prefs["amount_of_plotted_passed_systems_to_show"]),
                    progress_cb=self._on_parse_progress
                )
                self.nav_route.clear_plotted_route()
                self.nav_route.load_plotted_route()
                self.lbl_job_status.SetLabel("Route ready!")
                self._check_waypoint(self.nav_route.plotted_nav_route.nav_points[0])
            else:
                self.lbl_job_status.SetLabel(f"Plotting failed.\n{result.error}")
        else:
            self.lbl_job_status.SetLabel(f"Plotting failed.")
        self.render()

    def _enrich_route_with_star_classes(self, route_data: list) -> None:
        """Looks up missing StarClass values and writes them back into the raw jump dicts."""
        total = len(route_data)
        for i, jump in enumerate(route_data, start=1):
            # Already cached? Skip.
            if jump.get("StarClass"):
                continue

            system_id = jump.get("id64")
            if system_id is None:
                continue

            star_class = self.sh.get_star_class_from_spansh(system_id=system_id)
            if star_class:
                jump["StarClass"] = star_class

            self._on_parse_progress(i, total)

    def _on_parse_progress(self, done: int, total: int):
        if self._loading_precalculated_route:
            self.lbl_loading_status.SetLabel(f"Preparing waypoints… \nSystems {done}/{total}")
            self.lbl_loading_status.Update()
        else:
            self.lbl_job_status.SetLabel(f"Preparing waypoints… \nSystems {done}/{total}")
            self.lbl_job_status.Update()

    def _update_plotter_select(self):
        if not self.plotter_select_panel.IsShown():
            self.plotter_select_panel.Show()

        self.plotter_select_panel.add_table_item_label(label_text=f"Selected plotter", align=wx.ALIGN_BOTTOM, width=150)

        # Extract display texts for the dropdown
        display_texts = [opt[0] for opt in ROUTE_PLOTTERS]

        # Create combobox
        self.cmb_selected_plotter = wx.ComboBox(choices=display_texts, style=wx.CB_READONLY, parent=self.plotter_select_panel.content) #, size=BTN_SIZE)
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

        current_jump_range: str = str(round(self._calculate_current_jump_range(), 2))

        match self.selected_plotter:
            case "galaxy":
                self.parameter_panel.add_table_item_label("")

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

            case "neutron":
                pass

            case _:
                self.parameter_panel.add_table_item_label(" 🛈", align=wx.ALIGN_CENTER_VERTICAL).SetToolTip("Leave destination blank in order to create a circular tour starting at your source system and returning there at the end.")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label(label_text=f"Jump range (LY, default current)", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_jump_range = self.parameter_panel.add_table_item_textbox()
                self.txt_jump_range.SetValidator(FloatRangeValidator(min_val=1, max_val=100, allow_empty=False))
                self.txt_jump_range.SetValue(current_jump_range)
                self.parameter_panel.add_table_item_label(" 🛈", align=wx.ALIGN_CENTER_VERTICAL).SetToolTip("Jump range of your ship.")

                self.parameter_panel.add_table_item_label(label_text=f"Radius (LY)", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_stray_radius = self.parameter_panel.add_table_item_textbox()
                self.txt_stray_radius.SetValidator(FloatRangeValidator(min_val=1, max_val=100, allow_empty=False))
                self.txt_stray_radius.SetValue(str(25))
                self.parameter_panel.add_table_item_label(" 🛈", align=wx.ALIGN_CENTER_VERTICAL).SetToolTip(
                    "This is the distance in LY around which the plotter will look for valuable worlds for you to visit. A value of 25 LY tends to give a nice balance for A to B routes keeping the number of jumps reasonably low whilst still giving a nice payout. For circular routes (leaving destination blank) you will probably want to increase this to 100-500 LY.")

                self.parameter_panel.add_table_item_label(label_text=f"Maximum systems", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.txt_max_systems = self.parameter_panel.add_table_item_textbox()
                self.txt_max_systems.SetValidator(FloatRangeValidator(min_val=1, max_val=100, allow_empty=False))
                self.txt_max_systems.SetValue(str(100))
                self.parameter_panel.add_table_item_label(" 🛈", align=wx.ALIGN_CENTER_VERTICAL).SetToolTip(
                    "This is maximum number of systems that the plotter will route you through, lower this for a shorter trip.")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                if self.selected_plotter == "riches":
                    self.btn_use_mapping_value = DynamicToggleButton(
                        label="Use mapping value 🛈",
                        parent=self.parameter_panel.content,
                        is_toggled=True,
                        size=BTN_SIZE
                    )
                    self.parameter_panel.add_table_item_toggle_button(self.btn_use_mapping_value)
                    self.btn_use_mapping_value.SetToolTip("Use the mapping value rather than the scan value.")

                self.btn_avoid_thargoids = DynamicToggleButton(
                    label="Avoid Thargoids 🛈",
                    parent=self.parameter_panel.content,
                    is_toggled=True,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_avoid_thargoids)
                self.btn_avoid_thargoids.SetToolTip("Avoid systems that are at war with or controlled by the Thargoids.")
                if self.selected_plotter == "riches":
                    self.parameter_panel.add_table_item_label("")

                self.btn_loop_route = DynamicToggleButton(
                    label="Loop 🛈",
                    parent=self.parameter_panel.content,
                    is_toggled = False if self.selected_plotter == "riches" else True,
                    size=BTN_SIZE
                )
                self.parameter_panel.add_table_item_toggle_button(self.btn_loop_route)
                self.btn_loop_route.SetToolTip("Force the route to return to the starting system.")
                if self.selected_plotter == "riches":
                    self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")

                self.parameter_panel.add_table_item_label("Maximum distance to arrival", align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                self.parameter_panel.add_table_item_label("")
                self.parameter_panel.add_table_item_label("")
                self.spin_max_distance_to_arrival = wx.SpinCtrl(parent=self.parameter_panel.content, min=1, max=1000000, initial=50000, size=wx.Size(BTN_SIZE.width, -1))
                self.sld_max_distance_to_arrival = ThemedSlider(parent=self.parameter_panel.content, value=50000, min_val=1, max_val=1000000, size=(BTN_SIZE.width, SLIDER_FIXED_HEIGHT), scale="symlog")
                self.parameter_panel.add_table_item_generic(self.spin_max_distance_to_arrival)
                self.parameter_panel.add_table_item_generic(self.sld_max_distance_to_arrival)
                self.parameter_panel.add_table_item_label("")
                self._link_spin_slider(self.spin_max_distance_to_arrival, self.sld_max_distance_to_arrival)

                if self.selected_plotter in ("riches", "exobiology"):
                    label_text = ""
                    match self.selected_plotter:
                        case "riches":
                            label_text = "Minimum scan salue"
                        case "exobiology":
                            label_text = "Minimum landmark Value"

                    self.parameter_panel.add_table_item_label(label_text, align=wx.ALIGN_BOTTOM, width=BTN_SIZE.width)
                    self.parameter_panel.add_table_item_label("")
                    self.parameter_panel.add_table_item_label("")
                    self.spin_min_scan_value = wx.SpinCtrl(parent=self.parameter_panel.content, min=1, max=1000000, initial=100000, size=wx.Size(BTN_SIZE.width, -1))
                    self.sld_min_scan_value = ThemedSlider(parent=self.parameter_panel.content, value=100000, min_val=1, max_val=1000000, size=(BTN_SIZE.width, SLIDER_FIXED_HEIGHT), scale="symlog")
                    self.parameter_panel.add_table_item_generic(self.spin_min_scan_value)
                    self.parameter_panel.add_table_item_generic(self.sld_min_scan_value)
                    self.parameter_panel.add_table_item_label("")
                    self._link_spin_slider(self.spin_min_scan_value, self.sld_min_scan_value)

        self.parameter_panel.add_table_item_label("")
        self.parameter_panel.add_table_item_label("")
        self.parameter_panel.add_table_item_label("")

        self.btn_calculate_route = DynamicButton(parent=self.parameter_panel.content, label="Calculate route", size=BTN_SIZE)
        self.btn_calculate_route.Bind(wx.EVT_BUTTON, self._on_calculate_route)
        self.parameter_panel.add_table_item_generic(self.btn_calculate_route)
        self.btn_load_route = DynamicButton(parent=self.parameter_panel.content, label="Load last route 🛈", size=BTN_SIZE)
        self.btn_load_route.SetToolTip(
            "Loads the last route that has been plotted with the currently selected plotter. If you're already en-route your last visited waypoint will be highlighted and the next system is copied to the clipboard.")
        self.btn_load_route.Bind(wx.EVT_BUTTON, self._on_load_route)
        self.parameter_panel.add_table_item_generic(self.btn_load_route)
        self.parameter_panel.add_table_item_label("")

        self.lbl_job_status = self.parameter_panel.add_table_item_label(label_text="", align=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, line_height=int(BTN_SIZE.height*2), width=BTN_SIZE.width)
        self.lbl_loading_status = self.parameter_panel.add_table_item_label(label_text="", align=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, line_height=int(BTN_SIZE.height*2), width=BTN_SIZE.width)
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
        remaining_jumps_offset = 1

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
                    if system_type == "":
                        system_type = " ? "
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

                    if abs(i) > self.nav_route.remaining_jumps_in_route + remaining_jumps_offset:
                        lbl_1_system_indicator.SetForegroundColour(passed_colour)
                        lbl_2_space.SetForegroundColour(passed_colour)
                        lbl_3_star_feature.SetForegroundColour(passed_colour)
                        lbl_4_star_class.SetForegroundColour(passed_colour)
                        lbl_5_system.SetForegroundColour(passed_colour)
                        lbl_6_space.SetForegroundColour(passed_colour)

                    if abs(i) == self.nav_route.remaining_jumps_in_route + remaining_jumps_offset:
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
        spansh_route_data: DotDict = load_json_as_dotdict(str(self._last_route_for_selected_plotter))
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
        last_waypoint = None
        if hasattr(spansh_route_data, "last_waypoint"):
            last_waypoint: NavPoint = from_dotdict(NavPoint, spansh_route_data.last_waypoint)

        for system in spansh_route_data.jumps:
            # If we've reached a waypoint, copy the next name to the clipboard
            if do_copy_to_clipboard:
                if self.copied_system_name != system.name:
                    self.copied_system_name = system.name
                    copy_text_to_clipboard(system.name)
                    do_copy_to_clipboard = False
                break

            # check if we reached a waypoint
            if int(system.id64) == current_system_address:
                # try updating system again
                if not hasattr(system, "StarClass") or system.StarClass == "":
                    star_class = self.sh.get_star_class_from_spansh(system_id=current_system_address)
                    if star_class:
                        system["StarClass"] = star_class
                        save_dotdict_to_json(spansh_route_data, str(self._last_route_for_selected_plotter))
                self.nav_route.current_system = current_system
                if not last_waypoint or int(system.id64) != int(last_waypoint.system_address):
                    self._save_last_waypoint_system(spansh_route_data, current_system)
                do_copy_to_clipboard = True

        if not do_copy_to_clipboard and hasattr(spansh_route_data, "last_waypoint"):
            last_waypoint: NavPoint = from_dotdict(NavPoint, spansh_route_data.last_waypoint)
            self.nav_route.current_system = last_waypoint
            for system in spansh_route_data.jumps:
                if do_copy_to_clipboard:
                    if self.copied_system_name != system.name:
                        self.copied_system_name = system.name
                        copy_text_to_clipboard(system.name)
                        return True
                    else:
                        return False

                # check if we reached a waypoint
                if int(system.id64) == int(last_waypoint.system_address):
                    do_copy_to_clipboard = True

        return do_copy_to_clipboard

    def _on_close(self,event):
        self._timer.Stop()
        event.Skip()

    def _link_spin_slider(self, spin: wx.SpinCtrl, slider: ThemedSlider):
        spin.Bind(wx.EVT_SPINCTRL, lambda evt: self._on_spin(evt, slider))
        slider.Bind(wx.EVT_SLIDER, lambda evt: self._on_slider(evt, spin))

    def _on_spin(self, event, slider: ThemedSlider):
        slider.SetValue(event.EventObject.GetValue())

    def _on_slider(self, event, spin: wx.SpinCtrl):
        spin.SetValue(event.EventObject.GetValue())

    def _save_last_waypoint_system(self, spansh_route_data: DotDict, current_system: NavPoint):
        spansh_route_data.last_waypoint = DotDict(asdict(current_system))
        save_dotdict_to_json(spansh_route_data, str(self._last_route_for_selected_plotter))

    def _calculate_current_jump_range(self):
        jump_range: float = 0.0
        try:
            ship_loadout = load_json_as_dotdict(SLEF_PATH)
            sfsdm: ShipFSDModules = ShipFSDModules()

            fsd_optimal_mass: float = self.ship_status.mass_fsd_optimal
            max_fuel_per_jump = sfsdm.get_max_fuel_per_jump(ship_loadout)

            mass_unladen: float = self.ship_status.mass_unladen
            cargo: int = self.ship_status.cargo

            fuel_main: float = self.ship_status.fuel_capacity.main
            fuel_reserve: float = self.ship_status.fuel_capacity.reserve

            max_jump_range: float = self.ship_status.max_jump_range

            fuel_multiplier = sfsdm.get_fuel_multiplier(ship_loadout)
            fuel_power = sfsdm.get_fuel_power(ship_loadout)
            fsd_boost = sfsdm.get_jump_boost(ship_loadout)

            # Fuel the FSD can actually use for one jump (capped at max fuel per jump)
            jump_fuel: float = min(fuel_main + fuel_reserve, max_fuel_per_jump)

            # Total mass the FSD has to move (hull + main fuel + cargo, NO reserve tank)
            jump_mass: float = mass_unladen + fuel_main + fuel_reserve + cargo

            # Frontier's hyperspace fuel equation, inverted, plus Guardian booster flat bonus
            jump_range: float = (
                    (fsd_optimal_mass / jump_mass)
                    * (jump_fuel / fuel_multiplier) ** (1.0 / fuel_power)
                    + fsd_boost
            )

        except Exception as e:
            print(f"Calculate current jump range: {e}")
            jump_range = max_jump_range or 0.0

        return jump_range


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
