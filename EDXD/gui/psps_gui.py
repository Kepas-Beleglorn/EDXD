
from __future__ import annotations

from typing import Optional

import wx

from EDXD.data_handler.model import Body
from EDXD.data_handler.planetary_surface_positioning_system import PSPS, PSPSCoordinates
from EDXD.globals import DEFAULT_WIDTH_PSPS, DEFAULT_HEIGHT_PSPS, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.psps_gui_buttons import PSPSButtons

TITLE = "Planetary Surface Positioning System"
WINID = "PSPS"

class PositionTracker(DynamicDialog):
    def __init__(self, parent, title=TITLE, win_id=WINID):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT_PSPS, default_width=DEFAULT_WIDTH_PSPS,
                                      default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.psps = None
        self.pinned_position = None
        self.current_position = None

        self.theme = get_theme()

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # body name
        self.lbl_body = wx.StaticText(parent=self)
        self._update_body()
        self.window_box.Add(self.lbl_body, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # Add options panel (mineral filter, landable, and maybe more in the future
        self.buttons = PSPSButtons(parent=self)
        self.window_box.Add(self.buttons, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN)

        # current position
        self.txt_current_position = wx.TextCtrl(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        init_widget(self.txt_current_position, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)
        self.txt_current_position.SetEditable(False)
        self.window_box.Add(self.txt_current_position, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # pinned position
        self.txt_pinned_position = wx.TextCtrl(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        init_widget(self.txt_pinned_position, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)
        self.txt_pinned_position.SetEditable(False)
        self.window_box.Add(self.txt_pinned_position, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # distance to target
        self.txt_distance_to_target = wx.TextCtrl(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        init_widget(self.txt_distance_to_target, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)
        self.txt_distance_to_target.SetEditable(False)
        self.window_box.Add(self.txt_distance_to_target, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        self.SetSizer(self.window_box)

        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], current_position: Optional[PSPSCoordinates], current_heading: Optional[int]) -> None:
        self.lbl_body.SetLabelText(text=body.body_name if body else "")
        self.txt_pinned_position.Clear()
        self.txt_current_position.Clear()
        self.txt_distance_to_target.Clear()

        if body and current_position:
            self.current_position = current_position
            self.psps = PSPS(self.pinned_position, body.radius)
            current_ok: bool = False
            pinned_ok: bool = False
            if self.current_position.latitude and self.current_position.longitude:
                self.txt_current_position.SetValue(f"{ICONS['status_target']} Lat: {self.current_position.latitude:.5f}° :: Long: {self.current_position.longitude:.5f}°")
                current_ok = True
            else:
                self.current_position = None
                self.pinned_position = None
                self.txt_current_position.Clear()
                self.txt_pinned_position.Clear()
                self.txt_distance_to_target.Clear()

            if current_ok and self.pinned_position and self.pinned_position.latitude and self.pinned_position.longitude:
                self.txt_pinned_position.SetValue(f"{ICONS['pinned']} Lat: {self.pinned_position.latitude:.5f}° :: Long: {self.pinned_position.longitude:.5f}°")
                pinned_ok = True
            if current_ok and pinned_ok:
                formatted_distance = self.psps.get_distance(current_coordinates=self.current_position, target_coordinates=self.pinned_position)
                bearing_indicator = self.psps.get_relative_bearing(self.current_position, current_heading=current_heading)
                self.txt_distance_to_target.SetValue(f"Distance: {bearing_indicator} {formatted_distance}")
        else:
            self.txt_pinned_position.Clear()
            self.txt_current_position.Clear()
            self.txt_distance_to_target.Clear()
            self.current_position = None
            self.pinned_position = None
            self.psps = None

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
