
from __future__ import annotations

from typing import Optional, Dict

import wx

from EDXD.data_handler.model import Body
from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates, PSPS
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.utils.clipboard import copy_text_to_clipboard

TITLE = "BODY DETAILS"
WINID = "BODY_DETAILS"

class BodyDetails(DynamicDialog):
    def __init__(self, parent, title, win_id):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
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

        # body details
        self.txt_body_details = wx.TextCtrl(parent=self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        init_widget(self.txt_body_details, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)
        self.txt_body_details.SetEditable(False)
        self.window_box.Add(self.txt_body_details, 1, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        self.SetSizer(self.window_box)

        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], filters: Dict[str, bool], current_position: PSPSCoordinates, current_heading: float):
        self.lbl_body.SetLabelText(text=body.body_name if body else "")
        self.txt_body_details.Clear()
        self.body = body

        if self.body:

            psps = PSPS(current_position, self.body.radius)

            for mat, pct in sorted(self.body.materials.items(),
                                   key=lambda kv: kv[1],
                                   reverse=True):
                if filters.get(mat, True):
                    self.txt_body_details.AppendText(f"{mat.title():<12} {pct:5.1f}%\n")

            # ── Biosignals progress lines ───────────────────────────────
            if self.body.biosignals:
                self.txt_body_details.AppendText(f"\n{ICONS['biosigns']}{' '*2}Bio-signals ({self.body.biosignals}):\n")
                if self.body.bio_found:
                    for species, genus in self.body.bio_found.items():
                        done = int(genus.scanned_count if genus.scanned_count else 0)
                        bio_name = genus.variant_localised or genus.species_localised or genus.localised
                        bio_range = genus.min_distance

                        range_one = None
                        range_two = None
                        bearing_one = None
                        bearing_two = None
                        pos_first = PSPSCoordinates.from_dict(genus.pos_first)
                        pos_second = PSPSCoordinates.from_dict(genus.pos_second)

                        if done in [1, 2] and pos_first is not None:
                            range_raw = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_first, raw=True)
                            range_one = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_first)
                            if (range_raw*1000) < bio_range:
                                bearing_one = psps.get_relative_bearing(current_coordinates=current_position, target_coordinates=pos_first, current_heading=current_heading)
                            else:
                                bearing_one = ICONS['checked']
                        if done == 2 and pos_first is not None and pos_second is not None:
                            range_raw = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_second, raw=True)
                            range_two = psps.get_distance(current_coordinates=current_position, target_coordinates=pos_second)
                            if (range_raw*1000) < bio_range:
                                bearing_two = psps.get_relative_bearing(current_coordinates=current_position, target_coordinates=pos_second, current_heading=current_heading)
                            else:
                                bearing_two = ICONS['checked']

                        if done >= 3:
                            self.txt_body_details.AppendText(f"{' '*2}{ICONS['checked']}{' '*2}{bio_name}\n")
                        elif 0 < done < 3:
                            self.txt_body_details.AppendText(f"{' '*2}{ICONS['in_progress']}{' '*2}{bio_name}{' '*2}({done}/3){' '*2}({bio_range}m)")
                            if done in [1, 2]:
                                self.txt_body_details.AppendText(f"{' '*2}{bearing_one} {range_one}")
                            if done == 2:
                                self.txt_body_details.AppendText(f"{' '*2}{bearing_two} {range_two}")
                            self.txt_body_details.AppendText(f"\n")
                        else:
                            self.txt_body_details.AppendText(f"{' '*2}{ICONS['unknown']}{' '*2}{bio_name}\n")

            # ── Geology progress lines ─────────────────────────────────
            if self.body.geosignals:
                self.txt_body_details.AppendText(f"\n{ICONS['geosigns']}{' '*2}Geo-signals:")

                done = len(self.body.geo_found) if self.body.geo_found is not None else 0
                if 0 < done < self.body.geosignals:
                    self.txt_body_details.AppendText(f"{' '*2}{done}/{self.body.geosignals}{' '*2}{ICONS['in_progress']}\n")
                elif done == self.body.geosignals:
                    self.txt_body_details.AppendText(f"{' '*2}{done}/{self.body.geosignals}{' '*2}{ICONS['checked']}\n")
                else:
                    self.txt_body_details.AppendText(f"{' '*2}(?)/{self.body.geosignals}{' '*2}{ICONS['geosigns']}\n")

                for signal, geo in self.body.geo_found.items():
                    geo_name = geo.localised
                    if geo.is_new:
                        self.txt_body_details.AppendText(f"{ICONS['new_entry']:>4}{ICONS['geosigns']:>4}{' '*4}{geo_name}\n")
                    else:
                        self.txt_body_details.AppendText(f"{ICONS['geosigns']:>13}{' '*4}{geo_name}\n")

        else:
            self.txt_body_details.Clear()

        if not self.txt_body_details.GetValue().strip():
            self.txt_body_details.SetValue("—")

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

    def _plain_name_from_label(self, raw: str) -> str:
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