import functools
import inspect

import wx

from EDXD.globals import logging
from EDXD.gui.helper.custom_title_bar import CustomTitleBar
from EDXD.gui.helper.icon_loader import make_icon_bundle
from EDXD.gui.helper.window_properties import WindowProperties


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

class DynamicFrame(wx.Frame):
    from EDXD.globals import RESIZE_MARGIN  # px area at edge/corner for resizing
    def __init__(self, parent, style, title, win_id, show_minimize: bool = False, show_maximize: bool = False, show_close: bool = False):
        super().__init__(parent=parent, title=title, style=style)

        try:
            self.SetIcons(make_icon_bundle())  # <— plural: SetIcons uses wx.IconBundle
        except Exception as e:
            # optional logging
            pass

        self.win_id = win_id
        self._resizing = False
        self._resize_dir = None
        self._mouse_start = None
        self._frame_start = None
        self._props: WindowProperties = WindowProperties(None, None, None, None, None, None)

        self._resize = False
        self._resize_dir = None
        self._mouse_start = None

        # Window box sizer for titlebar + content
        self.window_box = wx.BoxSizer(wx.VERTICAL)

        # 1. add custom titlebar
        self.titlebar = CustomTitleBar(parent=self, title=title, show_minimize=show_minimize, show_maximize=show_maximize, show_close=show_close)
        self.window_box.Add(self.titlebar, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, self.RESIZE_MARGIN)

        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    # @log_call()
    def hit_test(self, pos):
        # Returns direction: 'left', 'right', 'top', 'bottom', or 'corner' (for diagonal)
        x, y = pos
        w, h = self.GetSize()
        margin = self.RESIZE_MARGIN
        directions = []
        if x < margin: directions.append('left')
        if x > w - margin: directions.append('right')
        if y < margin: directions.append('top')
        if y > h - margin: directions.append('bottom')

        return directions

    # @log_call()
    def on_mouse_down(self, evt):
        directions = self.hit_test(evt.GetPosition())
        if directions:
            self._resizing = True
            self._resize_dir = directions
            self._mouse_start = evt.GetPosition()
            self._frame_start = self.GetSize(), self.GetPosition()
        evt.Skip()

    # @log_call()
    def on_mouse_up(self, evt):
        self._resizing = False
        self._resize_dir = None
        evt.Skip()

    # @log_call()
    def on_mouse_move(self, evt):
        if self._resizing and evt.Dragging() and evt.LeftIsDown():
            dx = evt.GetPosition().x - self._mouse_start.x
            dy = evt.GetPosition().y - self._mouse_start.y
            size, pos = self._frame_start
            w, h = size
            x, y = pos
            directions = self._resize_dir
            if 'right' in directions:
                w = max(w + dx, 200)  # 200 = min width
            if 'bottom' in directions:
                h = max(h + dy, 150)  # 150 = min height
            if 'left' in directions:
                new_w = max(w - dx, 200)
                if new_w != w:
                    x += dx
                w = new_w
            if 'top' in directions:
                new_h = max(h - dy, 150)
                if new_h != h:
                    y += dy
                h = new_h
            self.SetSize(wx.Size(w, h))
            self.SetPosition(wx.Point(x, y))
        else:
            # Change cursor if hovering over edge/corner
            directions = self.hit_test(evt.GetPosition())
            if directions:
                if 'left' in directions or 'right' in directions:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
                elif 'top' in directions or 'bottom' in directions:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
                else:
                    self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            else:
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        evt.Skip()

    def on_close(self, event):
        # todo: save current show-state when closing app
        self.save_geometry(show_window=False)
        event.Skip()

    def save_geometry(self, show_window: bool):
        # Save geometry
        if self._props.show_window:
            x, y = self.GetPosition()
            w, h = self.GetSize()
            #show = self._props.show_window

        else:
            x = self._props.posx
            y = self._props.posy
            w = self._props.width
            h = self._props.height
            #show = show_window

        props = WindowProperties(window_id=self.win_id, height=h, width=w, posx=x, posy=y, show_window=show_window)
        props.save()
        if hasattr(self, '_refresh_timer') and getattr(self, '_refresh_timer') is not None:
            getattr(self, '_refresh_timer').Stop()
