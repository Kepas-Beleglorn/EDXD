from __future__ import annotations

from pickletools import dis
from sys import displayhook

import wx


from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

from EDXD.gui.helper.landing_pad_layouts.coriolis_like import CoriolisDisplay
from EDXD.data_handler.helper.landing_pad_layouts.coriolis_like import CoriolisDataGenerator
from EDXD.gui.helper.landing_pad_layouts.carrier_like import CarrierDisplay
from EDXD.data_handler.helper.landing_pad_layouts.carrier_like import CarrierDataGenerator, WIDTH_S, OFFSET_X, MARGIN



TITLE = "Landing Pad Indicator"
WINID = "LANDING_PAD_INDICATOR"

from EDXD.globals import DEFAULT_LANDING_PAD_WIDTH, DEFAULT_LANDING_PAD_HEIGHT, DEFAULT_POS_Y, DEFAULT_POS_X


class LandingPadFrame(DynamicDialog):
    """Main application frame"""

    def __init__(self,  parent, station_name: str, station_type: str, landing_pad: int):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_LANDING_PAD_HEIGHT, default_width=DEFAULT_LANDING_PAD_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y,
                                      default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)

        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent

        grid = wx.BoxSizer(wx.VERTICAL)

        self.lbl_station_name = wx.StaticText(self.scroll_container)
        init_widget(widget=self.lbl_station_name, title=station_name + "  [ " + station_type + " ]\n", height=20)

        theme = wx.Font(self.theme["font_bold"])
        theme.SetPointSize(12)
        self.lbl_station_name.SetFont(theme)

        grid.Add(self.lbl_station_name, 0, wx.EXPAND | wx.ALL, -4)

        self.station = None
        self.display = None

        fit_to_labels = False
        self.lbl_landing_pad = wx.StaticText(self.scroll_container)
        init_widget(widget=self.lbl_landing_pad, title="Assigned landing pad: " + str("0" + str(landing_pad))[-2:] + "\n", height=20)
        self.lbl_landing_pad.SetFont(theme)
        grid.Add(self.lbl_landing_pad, 0, wx.EXPAND | wx.ALL, -4)

        width = DEFAULT_LANDING_PAD_WIDTH
        height = DEFAULT_LANDING_PAD_HEIGHT

        if station_type in ["Coriolis", "Orbis", "Ocellus", "Dodec", "AsteroidBase"]:
            self.station = CoriolisDataGenerator.generate_coriolis(station_name, station_type)
            self.display = CoriolisDisplay(self.scroll_container, self.station)
        elif station_type in ["FleetCarrier"]:
            self.station = CarrierDataGenerator.generate_carrier(station_name, station_type)
            self.display = CarrierDisplay(self.scroll_container, self.station)
            width = WIDTH_S * 9 + OFFSET_X * 2 + MARGIN * 12
        else:
            fit_to_labels = True

        self.on_assign_pad(landing_pad)

        if self.display:
            grid.Add(self.display, 1, wx.EXPAND, 5)

        self.window_box.Add(grid, 1, flag=wx.ALL | wx.EXPAND, border=10)

        if fit_to_labels:
            self.Fit()
        else:
            init_widget(self, width=width, height=height, posx=props.posx, posy=props.posy, title=TITLE)

    def on_assign_pad(self, pad_num: int):
        if self.station:
            self.station.assigned_pad = pad_num
        if self.display:
            self.display.Refresh()
