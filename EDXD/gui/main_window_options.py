import wx

from EDXD.globals import logging
from EDXD.gui.helper.theme_handler import get_theme
import inspect, functools

from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton


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


class MainWindowOptions(wx.Panel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.parent = parent
        self.theme = get_theme()

        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        # Layout
        options_box = wx.BoxSizer(wx.HORIZONTAL)

        # Checkbox for "landable"
        self.chk_landable = DynamicToggleButton(parent=self, label=title, size=wx.Size(180 + self.theme["button_border_width"], 31 + self.theme["button_border_width"]))

        margin = self.theme["utton_border_margin"] + self.theme["button_border_width"]
        options_box.Add(self.chk_landable, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)

        self.SetSizer(options_box)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):

        dc = wx.PaintDC(self)
        w, h = self.GetSize()
        pen = wx.Pen(self.theme["foreground"], self.theme["border_thickness"])
        dc.SetPen(pen)
        # Top border
        dc.DrawLine(0, 0, w, 0)
        # Bottom border
        dc.DrawLine(0, h - 1, w, h - 1)
        event.Skip()