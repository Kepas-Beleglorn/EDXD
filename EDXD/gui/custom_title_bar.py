import wx

from EDXD.gui.helper.gui_handler import init_widget, ICON_PATH

from EDXD.globals import logging
import inspect, functools

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


class CustomTitleBar(wx.Panel):
    @log_call()
    def __init__(self, parent, title):
        super().__init__(parent)
        self._drag_offset = None
        self.parent = parent
        init_widget(widget=self, width=40, height=40)
        self._prev_size = None
        self._prev_pos = None

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # App icon
        icon = wx.Bitmap(ICON_PATH.as_posix(), wx.BITMAP_TYPE_PNG)
        icon_widget = wx.StaticBitmap(self, -1, icon)
        hbox.Add(icon_widget, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)

        # Title label
        self.title_label = wx.StaticText(self)
        init_widget(widget=self.title_label, title=title)
        font = self.title_label.GetFont()
        font.PointSize += 4
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.title_label.SetFont(font)
        hbox.Add(self.title_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)

        # Minimize, Maximize, Close buttons
        self.btn_min = wx.Button(self, size=(30, 30), style=wx.BORDER_NONE)
        init_widget(widget=self.btn_min, title="_")
        self.btn_max = wx.Button(self, size=(30, 30), style=wx.BORDER_NONE)
        init_widget(widget=self.btn_max, title="□")
        self.btn_close = wx.Button(self, size=(30, 30), style=wx.BORDER_NONE)
        init_widget(widget=self.btn_close, title="✕")
        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.SetFont(font)
            hbox.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

        self.SetSizer(hbox)

        # Bind events for dragging
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.title_label.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.title_label.Bind(wx.EVT_MOTION, self.on_mouse_move)
        icon_widget.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        icon_widget.Bind(wx.EVT_MOTION, self.on_mouse_move)

        # Bind button events
        self.btn_min.Bind(wx.EVT_BUTTON, lambda evt: parent.Iconize())
        self.btn_max.Bind(wx.EVT_BUTTON, self.on_maximize)
        self.btn_close.Bind(wx.EVT_BUTTON, lambda evt: parent.Close())

        self.dragging = False
        self._drag_pos = None

    # ... (other code unchanged)
    def on_left_down(self, event):
        self.dragging = False
        self.dragging = True
        # Get positions in screen coordinates
        mouse_screen_pos = wx.GetMousePosition()
        win_pos = self.parent.GetPosition()
        self._drag_offset = (mouse_screen_pos.x - win_pos.x, mouse_screen_pos.y - win_pos.y)
        if not self.HasCapture():
            self.CaptureMouse()

    def on_mouse_move(self, event):
        if self.dragging and event.Dragging() and event.LeftIsDown():
            mouse_screen_pos = wx.GetMousePosition()
            new_x = mouse_screen_pos.x - self._drag_offset[0]
            new_y = mouse_screen_pos.y - self._drag_offset[1]
            self.parent.Move((new_x, new_y))
        if not event.LeftIsDown():
            self.dragging = False
            if self.HasCapture():
                self.ReleaseMouse()

    # ... (other code unchanged)
    @log_call()
    def on_maximize(self, event):
        if getattr(self.parent, "_is_maximized", False):
            # Restore
            logging.info(f"Restoring to: {self._prev_pos}, {self._prev_size}")
            self.parent._is_maximized = False
            if self._prev_size and self._prev_pos:
                self.parent.SetSize(self._prev_size)
                wx.CallAfter(self.parent.Move, self._prev_pos)

        else:
            # Maximize manually to fill the screen
            self._prev_size = self.parent.GetSize()
            self._prev_pos = self.parent.GetPosition()
            logging.info(f"Saving pos/size: {self._prev_pos}, {self._prev_size}")
            display = wx.Display()
            logging.info(f"Display: {display}")
            rect = display.GetGeometry()
            logging.info(f"geom rect: {rect}")
            self.parent.SetPosition((rect.x, rect.y))
            self.parent.SetSize((rect.width, rect.height))
            self.parent._is_maximized = True
