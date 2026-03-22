
from __future__ import annotations

from typing import Optional, Dict

import wx

from EDXD.data_handler.model import Body, Atmosphere
from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates, PSPS
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.utils.clipboard import copy_text_to_clipboard
from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import EDXD.data_handler.helper.data_helper as dh
import EDXD.data_handler.helper.bio_helper as bh

TITLE = "BODY DETAILS"
WINID = "BODY_DETAILS"

class BodyDetails(DynamicDialog):
    def __init__(self, parent, title, win_id, is_hidden: bool = True):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.body = None

        self.theme = get_theme()

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # body name
        self.lbl_body = wx.StaticText(parent=self)
        self._update_body()
        self.window_box.Add(self.lbl_body, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # bind double click event for body label
        if getattr(self, "lbl_body", None):
            self.lbl_body.Bind(wx.EVT_LEFT_DCLICK, self._on_name_label_double_click)

        # collapsible panels with details
        # general data
        self.general_panel = CollapsiblePanel(parent=self, columns=2, label="General")
        self.window_box.Add(self.general_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.general_panel.Hide()

        # atmosphere data
        self.atmosphere_panel = CollapsiblePanel(parent=self, columns=3, label="Atmosphere")
        self.window_box.Add(self.atmosphere_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.atmosphere_panel.Hide()

        # minerals found
        self.mat_panel = CollapsiblePanel(parent=self, columns=3, label="Materials")
        self.window_box.Add(self.mat_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.mat_panel.Hide()

        # bio signals
        self.bio_panel = CollapsiblePanel(parent=self, columns=5, label="Biological signals")
        self.window_box.Add(self.bio_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.bio_panel.Hide()

        # geo signals
        self.geo_panel = CollapsiblePanel(parent=self, columns=1, label="Geological signals")
        self.window_box.Add(self.geo_panel, 0, wx.EXPAND, RESIZE_MARGIN)
        self.geo_panel.Hide()

        self.SetSizer(self.window_box)

        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], filters: Dict[str, bool], current_position: PSPSCoordinates, current_heading: float):
        self.lbl_body.SetLabelText(text=body.body_name if body else "")
        # reset
        self.general_panel.reset_table()
        self.atmosphere_panel.reset_table()
        self.mat_panel.reset_table()
        self.bio_panel.reset_table()
        self.geo_panel.reset_table()
        self.body = body

        if self.body is None:
            self.general_panel.Hide()
            self.atmosphere_panel.Hide()
            self.mat_panel.Hide()
            self.bio_panel.Hide()
            self.geo_panel.Hide()
        else:
            psps = PSPS(current_position, self.body.radius)
            self._update_general()
            self._update_atmosphere()
            self._update_materials(filters)
            self._update_bio_signals(psps=psps, current_heading=current_heading, current_position=current_position)
            self._update_geo_signals()

        if not self.IsShown():
            self.Show()

    # --------------------------------------------------------------
    def _on_show(self, event):
        """First time the window becomes visible."""
        self._ready = True
        event.Skip()

    def _update_body(self, title: str = ""):
        init_widget(widget=self.lbl_body, title=title)
        font = self.lbl_body.GetFont()
        font.PointSize += 2
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.lbl_body.SetFont(font)

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
        if self.body is None or self.body.body_name == "":
            self.general_panel.Hide()
            return

        if not self.general_panel.IsShown():
            self.general_panel.Show()

        self.general_panel.add_table_item("Type")
        self.general_panel.add_table_item(f"  {self.body.body_type}")
        self.general_panel.add_table_item("Mapped value")
        self.general_panel.add_table_item(f"  {self.body.estimated_value:,} Cr")
        self.general_panel.add_table_item("Distance")
        self.general_panel.add_table_item(f"  {self.body.distance:,.0f} Ls")
        if self.body.g_force is not None and self.body.g_force > 0:
            self.general_panel.add_table_item("Gravity")
            self._set_g_force_colour(self.general_panel.add_table_item(f"  {dh.format_gravity(self.body.g_force)}"), self.body.g_force)

        if self.body.mean_temp is not None:
            self.general_panel.add_table_item("Surface Temperature")
            self._set_temperature_colour(self.general_panel.add_table_item(f"  {dh.format_temperature(self.body.mean_temp, self.body.landable)}"), self.body.mean_temp)

        if self.body.volcanism is not None and self.body.volcanism != "":
            self.general_panel.add_table_item("Volcanism")
            self.general_panel.add_table_item(f"  {self.body.volcanism}")

        if self.body.present_life is not None and self.body.present_life != "":
            self.general_panel.add_table_item("Life")
            self.general_panel.add_table_item(f"  {self.body.present_life}")

        if self.body.luminosity is not None and self.body.luminosity != "":
            self.general_panel.add_table_item("Luminosity")
            self.general_panel.add_table_item(f"  {self.body.luminosity} ({self.body.raw_luminosity})")

        if self.general_panel.IsShown():
            # Force a layout update
            self.general_panel.force_render()

    def _update_atmosphere(self):
        atmosphere = self.body.atmosphere
        if atmosphere is None:
            self.atmosphere_panel.Hide()
            return

        atmos_type = None
        atmos_comp = None
        if isinstance(atmosphere, dict):
            atmos_comp = atmosphere.get("composition", None)
            atmos_type = atmosphere.get("type")

        if isinstance(atmosphere, Atmosphere):
            atmos_comp = atmosphere.composition
            atmos_type = atmosphere.type

        if atmos_comp is None or len(atmos_comp) == 0:
            self.atmosphere_panel.Hide()
            return

        if atmos_type is not None and atmos_type != "None":
            self.atmosphere_panel.header_label.SetLabel(f"Atmosphere: {dh.add_spaces_to_camel_case(atmos_type)}")
        else:
            self.atmosphere_panel.header_label.SetLabel(f"Atmosphere ({self.body.body_type})")

        for mat, pct in sorted(atmos_comp.items(),
                              key=lambda kv: kv[1],
                              reverse=True):
            self.atmosphere_panel.add_table_item(label_text=f"{mat.title():<12}")
            self.atmosphere_panel.add_table_item(label_text=f"{pct:5.1f}%", align=wx.ALIGN_RIGHT)
            self.atmosphere_panel.add_table_item("")

        if not self.atmosphere_panel.IsShown():
            self.atmosphere_panel.Show()
            # Force a layout update
            self.atmosphere_panel.force_render()

    def _update_materials(self, filters: Dict[str, bool]):
        show_mats = False
        for mat, pct in sorted(self.body.materials.items(),
                               key=lambda kv: kv[1],
                               reverse=True):
            if filters.get(mat, True):
                show_mats = True
                self.mat_panel.add_table_item(label_text=f"{mat.title():<12}")
                self.mat_panel.add_table_item(label_text=f"{pct:5.1f}%", align=wx.ALIGN_RIGHT)
                self.mat_panel.add_table_item("")

        if show_mats and not self.mat_panel.IsShown():
            self.mat_panel.Show()
        elif not show_mats:
            self.mat_panel.Hide()

        if self.mat_panel.IsShown():
            # Force a layout update
            self.mat_panel.force_render()

    def _update_geo_signals(self):
        if self.body is None or self.body.geosignals == 0:
            self.geo_panel.Hide()
            return

        if not self.geo_panel.IsShown():
            self.geo_panel.Show()

        geo_header: str = f"{ICONS['geosigns']}{' ' * 2}Geo-signals:"

        done = len(self.body.geo_found) if self.body.geo_found is not None else 0
        if 0 < done < self.body.geosignals:
            geo_header += f"{' ' * 2}({done}/{self.body.geosignals}{' ' * 2}{ICONS['in_progress']})"
        elif done == self.body.geosignals:
            geo_header += f"{' ' * 2}({done}/{self.body.geosignals}{' ' * 2}{ICONS['checked']})"
        else:
            geo_header += f"{' ' * 2}(?/{self.body.geosignals}{' ' * 2}{ICONS['geosigns']})"

        self.geo_panel.header_label.SetLabel(geo_header)

        for signal, geo in self.body.geo_found.items():
            geo_name = geo.localised
            if geo.is_new:
                self.geo_panel.add_table_item(f"{ICONS['new_entry']:>4}{ICONS['geosigns']:>4}{' ' * 4}{geo_name}")
            else:
                self.geo_panel.add_table_item(f"{ICONS['geosigns']:>13}{' ' * 4}{geo_name}")

        if self.geo_panel.IsShown():
            # Force a layout update
            self.geo_panel.force_render()

    def _update_bio_signals(self, psps: PSPS, current_position: PSPSCoordinates, current_heading: float):
        if self.body is None or self.body.biosignals == 0:
            self.bio_panel.Hide()
            return

        if not self.bio_panel.IsShown():
            self.bio_panel.Show()

        bio_header: str = f"{ICONS['biosigns']}{' ' * 2}Bio-signals:"

        if 0 < self.body.bio_scanned < self.body.biosignals:
            bio_header += f"{' ' * 2}({self.body.bio_scanned}/{self.body.biosignals}){' ' * 2}{ICONS['in_progress']}"
        elif self.body.bio_scanned == self.body.biosignals:
            bio_header += f"{' ' * 2}({self.body.bio_scanned}/{self.body.biosignals}){' ' * 2}{ICONS['checked']}"
        else:
            bio_header += f"{' ' * 2}({self.body.bio_scanned}/{self.body.biosignals}){' ' * 2}{ICONS['biosigns']}"

        self.bio_panel.header_label.SetLabel(bio_header)

        for species, genus in self.body.bio_found.items():
            # prepare data -------------------------------------------------------------------
            done = int(genus.scanned_count if genus.scanned_count else 0)
            bio_name = genus.variant_localised or genus.species_localised or genus.localised
            bio_range = genus.min_distance

            range_raw_one = 0
            range_raw_two = 0
            range_one = None
            range_two = None
            bearing_one = None
            bearing_two = None
            pos_first = PSPSCoordinates.from_dict(genus.pos_first)
            pos_second = PSPSCoordinates.from_dict(genus.pos_second)

            if done in [1, 2] and pos_first is not None:
                range_raw_one = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_first,
                                              raw=True)
                range_one = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_first)
                bearing_one = psps.get_relative_bearing(current_coordinates=current_position,
                                                        target_coordinates=pos_first,
                                                        current_heading=current_heading)
            if done == 2 and pos_first is not None and pos_second is not None:
                range_raw_two = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_second,
                                              raw=True)
                range_two = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_second)
                bearing_two = psps.get_relative_bearing(current_coordinates=current_position,
                                                        target_coordinates=pos_second,
                                                        current_heading=current_heading)

            # line per genus
            if done >= 3:
                self.bio_panel.add_table_item(f"{ICONS['checked']}")
            elif 0 < done < 3:
                self.bio_panel.add_table_item(f"{ICONS['in_progress']}")
            else:
                self.bio_panel.add_table_item(f"{ICONS['unknown']}")

            self.bio_panel.add_table_item(f"{bio_name}")
            self.bio_panel.add_table_item(f"{' ' * 2}({done}/3)")
            genus_name = genus.species_localised
            if (genus_name is None or genus_name == "") and genus.variant_localised is not None:
                genus_name = genus.variant_localised.split(" - ")[0]
            scan_value = bh.get_genus_value(genus_name)
            scan_value_str: str = ""
            if scan_value is not None and scan_value > 0:
                scan_value_str = f"{' ' * 2}{scan_value:,} Cr"
            self.bio_panel.add_table_item(label_text=f"{' ' * 2}{scan_value_str}", align=wx.ALIGN_RIGHT)
            self.bio_panel.add_table_item("")

            # if currently in progress, add bearings to already scanned
            if done in [1, 2]:
                self.bio_panel.add_table_item("")
                self.bio_panel.add_table_item(f"min. {bio_range}m")
                self.bio_panel.add_table_item(f"{bearing_one}")
                lbl_range_1 = self.bio_panel.add_table_item(f"{range_one}")
                self._set_distance_color(label=lbl_range_1, range_min=bio_range, range_current=range_raw_one)
                self.bio_panel.add_table_item("")

            if done == 2:
                self.bio_panel.add_table_item("")
                self.bio_panel.add_table_item("")
                self.bio_panel.add_table_item(f"{bearing_two}")
                lbl_range_2 = self.bio_panel.add_table_item(f"{range_two}")
                self._set_distance_color(label=lbl_range_2, range_min=bio_range, range_current=range_raw_two)
                self.bio_panel.add_table_item("")

        if self.geo_panel.IsShown():
            # Force a layout update
            self.geo_panel.force_render()

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
