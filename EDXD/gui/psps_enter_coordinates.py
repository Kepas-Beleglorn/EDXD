from __future__ import annotations

import wx
from wx import Size

from EDXD.globals import BTN_HEIGHT, BTN_WIDTH
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.utils.float_range_validator import FloatRangeValidator

TITLE = "Enter coordinates"
WINID = "PSPS_MANUAL_COORDINATES"

from EDXD.globals import DEFAULT_HEIGHT_PSPS_MANUAL_COORDINATES, DEFAULT_WIDTH_PSPS_MANUAL_COORDINATES, DEFAULT_POS_Y, DEFAULT_POS_X



# ---------------------------------------------------------------------------
class PSPSManualCoordinates(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_PSPS_MANUAL_COORDINATES, default_width=DEFAULT_WIDTH_PSPS_MANUAL_COORDINATES, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent

        grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=4)

        # latitude
        self.lbl_latitude = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(BTN_WIDTH-50, BTN_HEIGHT))
        grid.Add(self.lbl_latitude, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)

        self.txt_latitude = wx.TextCtrl(parent=self, style=wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_SIMPLE, size=Size(BTN_WIDTH-50, BTN_HEIGHT), validator=FloatRangeValidator(min_val=-90.0, max_val=90.0))
        grid.Add(self.txt_latitude, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)

        # longitude
        self.lbl_longitude = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE, size=Size(BTN_WIDTH-50, BTN_HEIGHT))
        grid.Add(self.lbl_longitude, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)

        self.txt_longitude = wx.TextCtrl(parent=self, style=wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_SIMPLE, size=Size(BTN_WIDTH-50, BTN_HEIGHT), validator=FloatRangeValidator(min_val=-180.0, max_val=180.0))
        grid.Add(self.txt_longitude, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)


        self.window_box.Add(grid, flag=wx.ALL, border=10)

        # confirm button
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_confirm = DynamicButton(parent=self, label="Confirm",
                                   size=wx.Size(BTN_WIDTH + self.theme["button_border_width"],
                                                BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        btn_cancel = DynamicButton(parent=self, label="Cancel",
                                  size=wx.Size(BTN_WIDTH + self.theme["button_border_width"],
                                               BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        hbox.Add(btn_confirm, flag=wx.RIGHT, border=8)
        hbox.Add(btn_cancel)
        self.window_box.Add(hbox, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        self.SetSizer(self.window_box)

        self.set_values()

        self.SetSizer(self.window_box)

        # Bindings
        btn_cancel.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
        btn_confirm.Bind(wx.EVT_BUTTON, lambda evt: self._on_confirm())
        self.Fit()

    def set_values(self):
        position = None
        if self.parent is None or self.parent.parent is None:
            return

        if self.parent.parent.pinned_position is not None:
            position = self.parent.parent.pinned_position

        if position is None and self.parent.parent.current_position is not None:
            position = self.parent.parent.current_position

        lat = position.latitude if position else None
        lon = position.longitude if position else None

        self.lbl_latitude.SetLabelText("Latitude (-90..90): ")
        self.lbl_longitude.SetLabelText("Longitude (-180..180): ")

        if lat is not None and lon is not None:
            self.txt_latitude.SetValue(f"{lat}")
            self.txt_longitude.SetValue(f"{lon}")

        init_widget(self.txt_latitude)
        init_widget(self.txt_longitude)

    def _on_confirm(self):
        # Validate both controls using the validators
        if not self.Validate():
            wx.MessageBox("Please fix the highlighted fields.", "Validation failed", wx.ICON_ERROR)
            return

        lat = float(self.txt_latitude.GetValue())
        lon = float(self.txt_longitude.GetValue())
        self.Close(True)
