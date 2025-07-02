import wx

from EDXD.globals import *
from EDXD.gui.helper.theme_handler import get_theme
import inspect, functools

from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.set_mineral_filter import MineralsFilter
from EDXD.data_handler.journal_historian import JournalHistorian



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
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.theme = get_theme()

        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        # Layout
        options_box = wx.BoxSizer(wx.HORIZONTAL)

        # Checkbox for "landable"
        self.chk_landable = DynamicToggleButton(parent=self, label="Show only landable bodies", size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True, is_toggled=self.parent.prefs["land"])
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        options_box.Add(self.chk_landable, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)

        # Call mineral filter
        self.btn_set_mineral_filter = DynamicButton(parent=self, label="Set mineral filter", size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        options_box.Add(self.btn_set_mineral_filter, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)
        self.btn_set_mineral_filter.Bind(wx.EVT_BUTTON, self._show_mineral_filter)

        # Load all journal files
        self.btn_load_history = DynamicButton(parent=self, label="Load historical journals",
                                                    size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        margin = self.theme["button_border_margin"] + self.theme["button_border_width"]
        options_box.Add(self.btn_load_history, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, margin)
        self.btn_load_history.Bind(wx.EVT_BUTTON, self._load_all_logs)

        self.SetSizer(options_box)
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def _load_all_logs(self, event):
        historian = JournalHistorian(journal_reader=self.parent.journal_reader, journal_controller=self.parent.journal_controller, status_json_watcher=self.parent.status_watcher)
        historian.process_all_journals()


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

    def _show_mineral_filter(self, event):
        mineral_filer = MineralsFilter(parent=self, prefs=self.parent.prefs)
        mineral_filer.ShowModal()