from __future__ import annotations

import wx


from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

from EDXD.gui.helper.landing_pad_layouts.coriolis_like import CoriolisDisplay
from EDXD.data_handler.helper.landing_pad_layouts.coriolis_like import CoriolisDataGenerator

TITLE = "Landing Pad Indicator"
WINID = "LANDING_PAD_INDICATOR"

from EDXD.globals import DEFAULT_LANDING_PAD_WIDTH, DEFAULT_LANDING_PAD_HEIGHT, DEFAULT_POS_Y, DEFAULT_POS_X


class LandingPadFrame(DynamicDialog):
    """Main application frame"""

    def __init__(self,  parent, station_name: str, station_id, station_type):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_LANDING_PAD_HEIGHT, default_width=DEFAULT_LANDING_PAD_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y,
                                      default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        max_height = wx.Size(-1, DEFAULT_LANDING_PAD_HEIGHT)
        min_width = wx.Size(DEFAULT_LANDING_PAD_WIDTH, -1)
        if props.width < min_width.width:
            props.width = min_width.width
        if props.height > max_height.height:
            props.height = max_height.height
        self.SetMinSize(min_width)
        self.SetMaxSize(max_height)

        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent

        self.station = CoriolisDataGenerator.generate_coriolis(station_name)
        self.display = CoriolisDisplay(self, self.station)

        self.Centre()

    def on_assign_pad(self, pad_num: int):
        self.station.assigned_pad = pad_num
        self.display.Refresh()

    def on_exit(self, event):
        self.Close()