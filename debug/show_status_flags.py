"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations

from typing import Dict
from pathlib import Path

import wx

from EDXD.globals import BTN_HEIGHT, BTN_WIDTH
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.data_handler.model import Model
from EDXD.data_handler.status_json_watcher import StatusWatcher


TITLE = "Status.json - Flags"
WINID = "STATUS_FLAGS"
FLAG_BTN_WIDTH = 250
FLAG_BTN_HEIGHT = 50

from EDXD.globals import DEFAULT_HEIGHT_MINERALS_FILTER, DEFAULT_WIDTH_MINERALS_FILTER, DEFAULT_POS_Y, DEFAULT_POS_X, RAW_MATS

# ---------------------------------------------------------------------------
class StatusFlags(DynamicDialog):
    def __init__(self, parent, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_MINERALS_FILTER,
                                      default_width=DEFAULT_WIDTH_MINERALS_FILTER, default_posx=DEFAULT_POS_X,
                                      default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.model = Model()

        self.theme = get_theme()
        self.prefs = prefs
        self.flag_button_values = [
                                "Docked, (on a landing pad)",
                                "Landed, (on planet surface)",
                                "Landing Gear Down",
                                "Shields Up",
                                "Supercruise",
                                "FlightAssist Off",
                                "Hardpoints Deployed",
                                "In Wing",
                                "LightsOn",
                                "Cargo Scoop Deployed",
                                "Silent Running,",
                                "Scooping Fuel",
                                "Srv Handbrake",
                                "Srv using Turret view",
                                "Srv Turret retracted (close to ship)",
                                "Srv DriveAssist",
                                "Fsd MassLocked",
                                "Fsd Charging",
                                "Fsd Cooldown",
                                "Low Fuel ( < 25% )",
                                "Over Heating ( > 100% )",
                                "Has Lat Long",
                                "IsInDanger",
                                "Being Interdicted",
                                "In MainShip",
                                "In Fighter",
                                "In SRV",
                                "Hud in Analysis mode",
                                "Night Vision",
                                "Altitude from Average radius",
                                "fsdJump",
                                "srvHighBeam",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN"
                            ]

        self.flag2_button_values = [
                                "OnFoot",
                                "InTaxi (or dropship/shuttle)",
                                "InMulticrew (ie in someone else's ship)",
                                "OnFootInStation",
                                "OnFootOnPlanet",
                                "AimDownSight",
                                "LowOxygen",
                                "LowHealth",
                                "Cold",
                                "Hot",
                                "VeryCold",
                                "VeryHot",
                                "Glide Mode",
                                "OnFootInHangar",
                                "OnFootSocialSpace",
                                "OnFootExterior",
                                "BreathableAtmosphere",
                                "Telepresence Multicrew",
                                "Physical Multicrew",
                                "Fsd hyperdrive charging",
                                "Supercruise Overcharge active",
                                "Supercruise Assist active",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN",
                                "UNKNOWN"
                            ]

        self.status_watcher = StatusWatcher(Path("/mnt/games/ED/journals/Frontier Developments/Elite Dangerous/Status.json"), self.model)
        self.status_watcher.start()

        # flag toggles grid
        grid = wx.FlexGridSizer(cols=4, hgap=8, vgap=4)
        self.flag_buttons = {}
        for i in range(len(self.flag_button_values)):
            btn = DynamicToggleButton(
                parent=self,
                label=f"[{i}]: {self.flag_button_values[i]}",
                is_toggled= False,
                size=wx.Size(FLAG_BTN_WIDTH, FLAG_BTN_HEIGHT)
            )
            self.flag_buttons[i] = btn
            grid.Add(btn, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)
        self.window_box.Add(grid, flag=wx.ALL, border=10)

        # spacer
        grid_spacer = wx.FlexGridSizer(cols=1, hgap=8, vgap=4)
        self.window_box.Add(grid_spacer, flag=wx.ALL, border=10)

        # flag2 toggles grid
        grid2 = wx.FlexGridSizer(cols=4, hgap=8, vgap=4)
        self.flag2_buttons = {}
        for i in range(len(self.flag2_button_values)):
            btn = DynamicToggleButton(
                parent=self,
                label=f"[{i}]: {self.flag2_button_values[i]}",
                is_toggled= False,
                size=wx.Size(FLAG_BTN_WIDTH, FLAG_BTN_HEIGHT)
            )
            self.flag2_buttons[i] = btn
            grid2.Add(btn, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)
        self.window_box.Add(grid2, flag=wx.ALL, border=10)

        self.SetSizer(self.window_box)
        self._refresh_timer = wx.CallLater(millis=500, callableObj=self.render)
        self.Fit()

    def render(self):
        if self.model.flags is not None:
            for i in range(len(self.flag_buttons)):
                new_val = (self.model.flags & pow(2, i)) != 0
                self.flag_buttons[i].SetValue(new_val)
                self.flag_buttons[i]._is_toggled = new_val
                self.flag_buttons[i].Refresh()

        if self.model.flags2 is not None:
            for i in range(len(self.flag2_buttons)):
                new_val = (self.model.flags2 & pow(2, i)) != 0
                self.flag2_buttons[i].SetValue(new_val)
                self.flag2_buttons[i]._is_toggled = new_val
                self.flag2_buttons[i].Refresh()

        self._refresh_timer = wx.CallLater(millis=500, callableObj=self.render)

    def on_close(self, event):
        app.ExitMainLoop()
        event.Skip()

if __name__ == "__main__":
    app = wx.App(False)
    frame = StatusFlags(None, {})
    frame.Show()

    app.MainLoop()
