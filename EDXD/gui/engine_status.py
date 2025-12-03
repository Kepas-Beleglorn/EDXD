from __future__ import annotations

import wx
from wx import Size

from EDXD.globals import BTN_HEIGHT, DEFAULT_FUEL_LOW_THRESHOLD
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.fuel_gauge import FuelGauge
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "Engine status"
WINID = "ENGINE_STATUS"

from EDXD.globals import DEFAULT_HEIGHT_ENGINE_STATUS, DEFAULT_WIDTH_ENGINE_STATUS, DEFAULT_POS_Y, DEFAULT_POS_X, VESSEL_SLF, VESSEL_SRV, VESSEL_EV, VESSEL_SHIP

# ---------------------------------------------------------------------------
class EngineStatus(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_ENGINE_STATUS, default_width=DEFAULT_WIDTH_ENGINE_STATUS, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent
        self.vessel_type = None

        grid = wx.FlexGridSizer(cols=1, hgap=8, vgap=4)

        # Fuel level (label)
        self.lbl_fuel_level = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(DEFAULT_WIDTH_ENGINE_STATUS-50, BTN_HEIGHT))
        grid.Add(self.lbl_fuel_level, 0, wx.EXPAND | wx.ALL, -4)

        # fuel level (gauge)
        self.pnl_fuel_gauge = FuelGauge(parent=self, show_scale=True, warning_threshold=self.parent.prefs.get("fuel_low_threshold", DEFAULT_FUEL_LOW_THRESHOLD))
        grid.Add(self.pnl_fuel_gauge, 0, wx.EXPAND | wx.ALL, -4)

        # FSD supercharged state
        self.lbl_fsd_super_charged = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(DEFAULT_WIDTH_ENGINE_STATUS-50, BTN_HEIGHT))
        grid.Add(self.lbl_fsd_super_charged, 0, wx.EXPAND | wx.ALL, -4)

        # todo: 114 - implement FSD super charged state (perhaps even check for FSD injection via synth?)

        self.window_box.Add(grid, flag=wx.ALL | wx.EXPAND, border=10)

        self.SetSizer(self.window_box)

        self.set_values()

        self.SetSizer(self.window_box)

        ## Bindings
        #btn_cancel.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
        #btn_confirm.Bind(wx.EVT_BUTTON, lambda evt: self._on_confirm())
        self.render()

    def render(self, fuel_current_main: float = 0, fuel_current_reservoir: float = 0, fuel_capacity_main: float = 0, fuel_capacity_reservoir: float = 0, vehicle: str = "ship"):
        if vehicle == VESSEL_SHIP:
            fuel_capacity_total = fuel_capacity_main + fuel_capacity_reservoir
        if vehicle == VESSEL_EV:
            fuel_capacity_total = fuel_capacity_reservoir
        if vehicle == VESSEL_SRV:
            fuel_capacity_total = fuel_capacity_reservoir
        if vehicle == VESSEL_SLF:
            fuel_capacity_total = fuel_capacity_reservoir

        self.vessel_type = vehicle
        if fuel_capacity_total > 0:
            total_fuel = fuel_current_main + fuel_current_reservoir
            fuel_level = float(total_fuel / fuel_capacity_total) * 100
            self.pnl_fuel_gauge.SetLevel(fuel_level)

        self.set_values()
        if not self.IsShown():
            self.Show()

        self.Fit()
        if vehicle == VESSEL_EV:
            self.pnl_fuel_gauge.Hide()
        else:
            self.pnl_fuel_gauge.Show()

    def set_values(self):
        self.lbl_fuel_level.SetLabelText(f"Fuel level - {self.vessel_type}")
        self.lbl_fsd_super_charged.SetLabelText("FSD state")
