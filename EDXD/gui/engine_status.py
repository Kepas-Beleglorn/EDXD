from __future__ import annotations

import wx
from wx import Size

from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.fuel_gauge import FuelGauge
from EDXD.gui.helper.fsd_indicator import FSDIndicator
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "Engine status"
WINID = "ENGINE_STATUS"

from EDXD.globals import DEFAULT_HEIGHT_ENGINE_STATUS, DEFAULT_WIDTH_ENGINE_STATUS, DEFAULT_POS_Y, DEFAULT_POS_X, VESSEL_SLF, VESSEL_SRV, VESSEL_EV, VESSEL_SHIP, DEFAULT_WINDOW_SHOW, BTN_HEIGHT, DEFAULT_FUEL_LOW_THRESHOLD

# ---------------------------------------------------------------------------
class EngineStatus(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        self._props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_ENGINE_STATUS, default_width=DEFAULT_WIDTH_ENGINE_STATUS, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_show=DEFAULT_WINDOW_SHOW)
        if not self._props.show_window:
            return

        # 2. Apply geometry
        init_widget(self, width=self._props.width, height=self._props.height, posx=self._props.posx, posy=self._props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent
        self.vessel_type = None

        max_height = wx.Size(-1, DEFAULT_HEIGHT_ENGINE_STATUS)
        min_width = wx.Size(DEFAULT_WIDTH_ENGINE_STATUS, -1)
        self.SetMinSize(min_width)
        self.SetMaxSize(max_height)

        grid = wx.BoxSizer(wx.VERTICAL)

        # Fuel level (label)
        self.lbl_fuel_level = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(DEFAULT_WIDTH_ENGINE_STATUS-50, BTN_HEIGHT))
        grid.Add(self.lbl_fuel_level, 0, wx.EXPAND | wx.ALL, -4)

        # fuel level (gauge)
        self.pnl_fuel_gauge = FuelGauge(parent=self, show_scale=True, warning_threshold=self.parent.prefs.get("fuel_low_threshold", DEFAULT_FUEL_LOW_THRESHOLD))
        grid.Add(self.pnl_fuel_gauge, 0, wx.EXPAND | wx.ALL, -4)

        # spacer
        self.lbl_spacer = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(DEFAULT_WIDTH_ENGINE_STATUS-50, BTN_HEIGHT))
        grid.Add(self.lbl_spacer, 0, wx.EXPAND | wx.ALL, -4)

        # FSD supercharged state
        self.fsd_indicator = FSDIndicator(parent=self, size=wx.Size(-1, 100))
        self.fsd_indicator.set_text("FSD STATUS")

        grid.Add(self.fsd_indicator, 0, wx.CENTER | wx.EXPAND | wx.ALL, 5)

        # spacer
        self.lbl_fsd_injection = wx.StaticText(parent=self,
                                               style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE,
                                               size=Size(DEFAULT_WIDTH_ENGINE_STATUS, BTN_HEIGHT))
        grid.Add(self.lbl_fsd_injection, 0, wx.CENTER | wx.EXPAND | wx.ALL, -4)

        self.window_box.Add(grid, flag=wx.ALL | wx.EXPAND, border=10)
        self.set_values()

        self.SetSizer(self.window_box)

        self.render()

    def render(self, fuel_current_main: float = 0, fuel_current_reservoir: float = 0, fuel_capacity_main: float = 0, fuel_capacity_reservoir: float = 0, vehicle: str = "ship"):
        fuel_capacity_total = 0
        if vehicle == VESSEL_SHIP:
            fuel_capacity_total = fuel_capacity_main + fuel_capacity_reservoir
        if vehicle == VESSEL_EV:
            fuel_capacity_total = fuel_capacity_reservoir
        if vehicle == VESSEL_SRV:
            fuel_capacity_total = fuel_capacity_reservoir or 0.5
        if vehicle == VESSEL_SLF:
            fuel_capacity_total = fuel_capacity_reservoir or 0.5

        self.vessel_type = vehicle
        if fuel_capacity_total > 0:
            total_fuel = fuel_current_main + fuel_current_reservoir
            fuel_level = float(total_fuel / fuel_capacity_total) * 100
            self.pnl_fuel_gauge.SetLevel(fuel_level)

        self.set_values()
        if not self.IsShown():
            self.Show()

        self.Fit()
        if vehicle == VESSEL_SHIP:
            self.pnl_fuel_gauge.Show()
            self.fsd_indicator.Show()
            self.lbl_fsd_injection.Show()
        else:
            if vehicle == VESSEL_EV:
                self.pnl_fuel_gauge.Hide()
            else:
                self.pnl_fuel_gauge.Show()
            self.fsd_indicator.Hide()
            self.lbl_fsd_injection.Hide()

    def set_values(self):
        self.lbl_fuel_level.SetLabelText(f"Fuel level - {self.vessel_type}")

        if self.parent.model is None or self.parent.model.ship_status is None or self.parent.model.ship_status.jet_cone_boost_factor is None:
            self.fsd_indicator.set_state(FSDIndicator.STATE_OFF)
            self.fsd_indicator.set_text("FSD nominal")
        else:
            self.fsd_indicator.set_state(FSDIndicator.STATE_SUPERCHARGED)
            self.fsd_indicator.set_text(f"FSD supercharged (x{self.parent.model.ship_status.jet_cone_boost_factor})")

        if self.parent.model is None or self.parent.model.ship_status is None or self.parent.model.ship_status.fsd_injection_factor is None:
            self.lbl_fsd_injection.SetLabelText("")
        else:
            self.lbl_fsd_injection.SetLabelText(f"FSD injection active: +{self.parent.model.ship_status.fsd_injection_factor * 100}%")
