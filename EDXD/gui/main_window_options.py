import wx

from EDXD.gui.helper.gui_handler import init_widget

from EDXD.globals import logging, SIZE_CTRL_BUTTONS, SIZE_APP_ICON, ICON_PATH
import inspect, functools

from EDXD.gui.helper.gui_dynamic_button import DynamicButton
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
        # Layout
        options_box = wx.BoxSizer(wx.HORIZONTAL)

        # Checkbox for "landable"
        self.chk_landable = DynamicToggleButton(parent=self, label=title)
        options_box.Add(self.chk_landable, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT)

        self.SetSizer(options_box)
