"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations

import wx

from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "Status Flags"
WINID = "STATUS_FLAGS"
FLAG_BTN_WIDTH = 270
FLAG_BTN_HEIGHT = 45

from EDXD.globals import DEFAULT_HEIGHT_MINERALS_FILTER, DEFAULT_WIDTH_MINERALS_FILTER, DEFAULT_POS_Y, DEFAULT_POS_X

# ---------------------------------------------------------------------------
class StatusFlags(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_MINERALS_FILTER,
                                      default_width=DEFAULT_WIDTH_MINERALS_FILTER, default_posx=DEFAULT_POS_X,
                                      default_posy=DEFAULT_POS_Y)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.parent = parent
        self.debug_mode = parent.prefs.get(WINID).get("DEBUG", False)
        self.theme = get_theme()
        self.flag_button_values = [
                                "Docked, (on a landing pad)",
                                "Landed, (on planet surface)",
                                "Landing Gear Down",
                                "Shields Up",
                                "Supercruise",
                                "Flight Assist Off",
                                "Hardpoints Deployed",
                                "In Wing",
                                "Lights On",
                                "Cargo Scoop Deployed",
                                "Silent Running,",
                                "Scooping Fuel",
                                "SRV Handbrake",
                                "SRV Turret View",
                                "SRV Turret Retracted (close to ship)",
                                "SRV Drive Assist",
                                "Fsd Mass Locked",
                                "Fsd Charging",
                                "Fsd Cooldown",
                                "Low Fuel ( < 25% )",
                                "Over Heating ( > 100% )",
                                "Has Lat Long",
                                "Is In Danger",
                                "Being Interdicted",
                                "In Main Ship",
                                "In Fighter",
                                "In SRV",
                                "HUD In Analysis Mode",
                                "Night Vision",
                                "Altitude From Average Radius",
                                "FSD Jump",
                                "SRV High Beam",
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
                                "On Foot",
                                "In Taxi (or dropship/shuttle)",
                                "In Multicrew (ie. in someone else's ship)",
                                "On Foot In Station",
                                "On Foot On Planet",
                                "Aim Down Sight",
                                "Low Oxygen",
                                "Low Health",
                                "Cold",
                                "Hot",
                                "Very Cold",
                                "Very Hot",
                                "Glide Mode",
                                "On Foot In Hangar",
                                "On Foot In Social Space",
                                "On Foot Exterior",
                                "Breathable Atmosphere",
                                "Telepresence Multicrew",
                                "Physical Multicrew",
                                "FSD Hyperdrive Charging",
                                "Supercruise Overcharge Active",
                                "Supercruise Assist Active",
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

        # flag toggles grid
        grid = wx.FlexGridSizer(cols=4, hgap=8, vgap=4)
        self.flag_buttons = {}
        for i in range(len(self.flag_button_values)):
            if self.debug_mode:
                label = f"[{i}]: {self.flag_button_values[i]}"
            else:
                label = f"{self.flag_button_values[i]}"
                if label == "UNKNOWN":
                    break
            btn = DynamicToggleButton(
                parent=self,
                label=label,
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
            if self.debug_mode:
                label = f"[{i}]: {self.flag2_button_values[i]}"
            else:
                label = f"{self.flag2_button_values[i]}"
                if label == "UNKNOWN":
                    break
            btn = DynamicToggleButton(
                parent=self,
                label=label,
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
        if self.parent.model.flags is not None:
            for i in range(len(self.flag_buttons)):
                new_val = (self.parent.model.flags & pow(2, i)) != 0
                self.flag_buttons[i].SetValue(new_val)
                self.flag_buttons[i]._is_toggled = new_val
                self.flag_buttons[i].Refresh()

        if self.parent.model.flags2 is not None:
            for i in range(len(self.flag2_buttons)):
                new_val = (self.parent.model.flags2 & pow(2, i)) != 0
                self.flag2_buttons[i].SetValue(new_val)
                self.flag2_buttons[i]._is_toggled = new_val
                self.flag2_buttons[i].Refresh()

        self._refresh_timer = wx.CallLater(millis=500, callableObj=self.render)
