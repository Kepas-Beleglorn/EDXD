import functools
import inspect

import wx

from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates
from EDXD.globals import *
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.theme_handler import get_theme


def log_call(level=logging.INFO):
    """Decorator that logs function name and bound arguments."""
    def decorator(fn):
        logger = logging.getLogger(fn.__module__)   # one logger per module
        sig = inspect.signature(fn)                 # capture once, not on every call

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arg_str = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            logger.log(level, "%s(%s)", fn.__name__, arg_str)
            return fn(*args, **kwargs)

        return wrapper
    return decorator


class PSPSButtons(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.theme = get_theme()

        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        # Layout
        button_box = wx.BoxSizer(wx.HORIZONTAL)

        # set current position
        self.btn_set_current_position = DynamicButton(parent=self, label="Pin current position",
                                                      size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        button_box.Add(self.btn_set_current_position, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)
        self.btn_set_current_position.Bind(wx.EVT_BUTTON, self._init_psps)

        # set manual position
        self.btn_set_manual_position = DynamicButton(parent=self, label="Enter position manually",
                                                      size=wx.Size(BTN_WIDTH + self.theme["button_border_width"],
                                                                   BTN_HEIGHT + self.theme["button_border_width"]),
                                                      draw_border=True)
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        button_box.Add(self.btn_set_manual_position, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)
        self.btn_set_manual_position.Bind(wx.EVT_BUTTON, self._init_manual_psps)

        # clear current position
        self.btn_set_current_position = DynamicButton(parent=self, label="Clear pinned position",
                                                      size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        button_box.Add(self.btn_set_current_position, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)
        self.btn_set_current_position.Bind(wx.EVT_BUTTON, self._clear_psps)

        self.SetSizer(button_box)
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        w, h = self.GetSize()
        pen = wx.Pen(self.theme["foreground"], self.theme["border_thickness"])
        dc.SetPen(pen)
        # Top border
        dc.DrawLine(0, 0, w, 0)
        # Bottom border
        dc.DrawLine(0, h - 1, w, h - 1)
        event.Skip()

    def _init_psps(self, event):
        self.parent.pinned_position = self.parent.current_position

    def _init_manual_psps(self, event):
        import EDXD.gui.psps_enter_coordinates as psps_manual
        psps_input = psps_manual.PSPSManualCoordinates(parent=self)
        psps_input.ShowModal()
        lat = float(psps_input.txt_latitude.GetValue())
        lon = float(psps_input.txt_longitude.GetValue())

        self.parent.pinned_position = PSPSCoordinates(latitude=lat, longitude=lon)

    def _clear_psps(self, event):
        self.parent.pinned_position = None
