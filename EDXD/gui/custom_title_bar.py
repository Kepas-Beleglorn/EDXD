import wx

from EDXD.gui.helper.gui_handler import init_widget

from EDXD.globals import logging, SIZE_CTRL_BUTTONS, SIZE_APP_ICON, ICON_PATH
import inspect, functools

from EDXD.gui.helper.gui_hover_button import HoverButton


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
    def __init__(self, parent, title):
        super().__init__(parent)
        self._drag_offset = None
        self.parent = parent
        init_widget(widget=self, width=40, height=40)
        self._prev_size = None
        self._prev_pos = None
        self._current_pos = None    # required for proper resizing on maximize

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # App icon
        icon_widget = self.set_icon()
        # Add to your sizer as before
        hbox.Add(icon_widget, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT)

        # Title label
        self.title_label = wx.StaticText(self)
        init_widget(widget=self.title_label, title=title)
        font = self.title_label.GetFont()
        font.PointSize += 4
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.title_label.SetFont(font)
        hbox.Add(self.title_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)

        # Minimize, Maximize, Close buttons
        self.btn_min = HoverButton(self, label="_", size=wx.Size(SIZE_CTRL_BUTTONS, SIZE_CTRL_BUTTONS), style=wx.BORDER_NONE)
        self.btn_max = HoverButton(self, label="□", size=wx.Size(SIZE_CTRL_BUTTONS, SIZE_CTRL_BUTTONS), style=wx.BORDER_NONE)
        self.btn_close = HoverButton(self, label="✕", size=wx.Size(SIZE_CTRL_BUTTONS, SIZE_CTRL_BUTTONS), style=wx.BORDER_NONE)
        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.SetFont(font)
            hbox.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.SOUTH, 6)

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

    def set_icon(self) ->wx.StaticBitmap:
        # Load the original image as a wx.Image
        image = wx.Image(ICON_PATH.as_posix(), wx.BITMAP_TYPE_PNG)
        # Scale it to the desired size (e.g., 30x30), using high-quality scaling
        scaled_image = image.Scale(SIZE_APP_ICON, SIZE_APP_ICON, wx.IMAGE_QUALITY_HIGH)
        # Convert the scaled wx.Image back to a wx.Bitmap for use in widgets
        scaled_bmp = wx.Bitmap(scaled_image)
        # Wrap in wx.BitmapBundle for DPI awareness (recommended in wxPython 4.1+)
        icon_bundle = wx.BitmapBundle.FromBitmap(scaled_bmp)
        # Use in your StaticBitmap
        return wx.StaticBitmap(self, -1, icon_bundle)

    # ... (other code unchanged)
    def on_left_down(self, event):
        logging.info(event.GetEventObject())
        self.dragging = False
        self.dragging = True
        # Get positions in screen coordinates
        mouse_screen_pos = wx.GetMousePosition()
        win_pos = self.parent.GetPosition()
        self._drag_offset = (mouse_screen_pos.x - win_pos.x, mouse_screen_pos.y - win_pos.y)
        if not self.HasCapture():
            self.CaptureMouse()

    def on_mouse_move(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
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
    #@log_call()
    def on_maximize(self, event):
        logging.info(event.GetEventObject())
        if getattr(self.parent, "_is_maximized", False):
            # Restore
            self.parent._is_maximized = False
            if self._prev_size and self._prev_pos:
                self.parent.SetSize(self._prev_size)
                wx.CallAfter(self.parent.Move, self._prev_pos)

        else:
            # Maximize manually to fill the screen
            self._prev_size = self.parent.GetSize()
            self._prev_pos = self.parent.GetScreenPosition()
            center = wx.Point(self._prev_pos.x + self._prev_size.x // 2, self._prev_pos.y + self._prev_size.y // 2)
            display_idx = wx.Display.GetFromPoint(center)
            if display_idx != wx.NOT_FOUND:
                display = wx.Display(display_idx)
                rect = display.GetGeometry()
                self.parent.SetPosition((rect.x, rect.y))
                self.parent.SetSize((rect.width, rect.height))
                self.parent._is_maximized = True
                self._current_pos = self.parent.GetPosition()
                wx.CallLater(millis=100, callableObj=self._resize_if_required)

    # horizontal taskbar offest must be read from the custom title bar, not from the parent!
    #@log_call()
    def _resize_if_required(self):
        logging.info(f"Maximized parent pos and size: {self.parent.GetPosition()} - {self.parent.GetSize()}")
        logging.info(f"Current pos: {self._current_pos}")
        pos_x, pos_y = self.parent.GetPosition()
        alt_pos_x, alt_pos_y = self._current_pos

        width, height = self.parent.GetSize()
        logging.info(f"current size: {self.parent.GetSize()}")

        if pos_x != alt_pos_x:
            if pos_x > 0:
                width -= pos_x
            else:
                width += pos_x

        if pos_y != alt_pos_y:
            if pos_y > 0:
                height -= pos_y
            else:
                height += pos_y

        self.parent.SetSize(width, height)
