import functools
import inspect
import wx

from EDXD.globals import logging
from EDXD.gui.helper.custom_title_bar import CustomTitleBar
from EDXD.gui.helper.icon_loader import make_icon_bundle
from EDXD.gui.helper.window_properties import WindowProperties


def log_call(level=logging.INFO):
    def decorator(fn):
        logger = logging.getLogger(fn.__module__)
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arg_str = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            logger.log(level, "%s(%s)", fn.__name__, arg_str)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


class DynamicDialog(wx.Dialog):
    from EDXD.globals import RESIZE_MARGIN

    def __init__(self, parent, style, title, win_id, show_minimize: bool = False, show_maximize: bool = False, show_close: bool = False, vertical_scroll: bool = False, horizontal_scroll: bool = False):
        super().__init__(parent=parent, title=title, style=style)

        try:
            self.SetIcons(make_icon_bundle())
        except Exception:
            pass

        self.win_id = win_id
        self._resizing = False
        self._resize_dir = None
        self._mouse_start = None
        self._frame_start = None

        # 1. Main Dialog Sizer (Vertical)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)

        # 2. Titlebar (Fixed, direct child of Dialog)
        self.titlebar = CustomTitleBar(parent=self, title=title, show_minimize=show_minimize, show_maximize=show_maximize, show_close=show_close)
        self.main_sizer.Add(self.titlebar, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, self.RESIZE_MARGIN)

        # 3. The Scrolled Container (Child of Dialog)
        # This window will handle all the scrolling logic internally
        self.scroll_container = wx.ScrolledWindow(self)
        scroll_val_x = 0
        scroll_val_y = 0
        if horizontal_scroll:
            scroll_val_x = 5
        if vertical_scroll:
            scroll_val_y = 5
        self.scroll_container.SetScrollRate(scroll_val_x, scroll_val_y)

        # 4. The Content Sizer (Lives inside the Scrolled Container)
        # Subclasses add to self.window_box, which is now bound to scroll_container
        self.window_box = wx.BoxSizer(wx.VERTICAL)
        self.scroll_container.SetSizer(self.window_box)

        # 5. Add scrolled container to main sizer (expands to fill space)
        self.main_sizer.Add(self.scroll_container, 1, wx.EXPAND | wx.ALL, self.RESIZE_MARGIN)

        # Bind Resize Events to the DIALOG, not the scrolled window
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def finalize_layout(self):
        """
        Call this at the end of subclass __init__.
        It calculates the virtual size of the scroll_container.
        """
        # Tell the scrolled window to calculate its virtual size based on content
        self.scroll_container.FitInside()
        # Layout the sizers
        self.window_box.Layout()
        self.main_sizer.Layout()
        self.Layout()

    # --- Resize Logic (Unchanged logic, operates on Dialog coordinates) ---

    def hit_test(self, pos):
        # pos is relative to the Dialog (self) because events are bound to self
        x, y = pos
        w, h = self.GetSize()
        margin = self.RESIZE_MARGIN

        # Safety: Don't allow resizing if clicking near scrollbars of the child
        # We approximate scrollbar size to avoid interference
        sb_width = 0
        #if self.scroll_container.IsScrollbarVisible(wx.VERTICAL):
        #    sb_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_WIDTH)

        # If mouse is near the right edge where the scrollbar is, ignore 'right' resize
        # to prevent conflict with scrolling.
        effective_w = w - sb_width if sb_width > 0 else w

        directions = []
        if x < margin: directions.append('left')
        if x > effective_w - margin: directions.append('right')
        if y < margin: directions.append('top')
        if y > h - margin: directions.append('bottom')

        return directions

    def on_mouse_down(self, evt):
        # Only start resizing if we are NOT on the scrollable content area
        # (Optional: You might want to allow dragging the titlebar to move,
        # but your current logic is for resizing edges. If you need move logic, add it here.)

        directions = self.hit_test(evt.GetPosition())
        if directions:
            self._resizing = True
            self._resize_dir = directions
            self._mouse_start = evt.GetPosition()
            self._frame_start = self.GetSize(), self.GetPosition()
        evt.Skip()

    def on_mouse_up(self, evt):
        self._resizing = False
        self._resize_dir = None
        evt.Skip()

    def on_mouse_move(self, evt):
        if self._resizing and evt.Dragging() and evt.LeftIsDown():
            dx = evt.GetPosition().x - self._mouse_start.x
            dy = evt.GetPosition().y - self._mouse_start.y
            size, pos = self._frame_start
            w, h = size
            x, y = pos
            directions = self._resize_dir

            if 'right' in directions:
                w = max(w + dx, 200)
            if 'bottom' in directions:
                h = max(h + dy, 150)
            if 'left' in directions:
                new_w = max(w - dx, 200)
                if new_w != w: x += dx
                w = new_w
            if 'top' in directions:
                new_h = max(h - dy, 150)
                if new_h != h: y += dy
                h = new_h

            self.SetSize(wx.Size(w, h))
            self.SetPosition(wx.Point(x, y))
        else:
            # Cursor logic
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
        self.save_geometry()
        event.Skip()

    def save_geometry(self):
        x, y = self.GetPosition()
        w, h = self.GetSize()
        is_hidden = WindowProperties.load(window_id=self.win_id, default_height=h, default_width=w, default_posx=x, default_posy=y, default_is_hidden=False).is_hidden
        props = WindowProperties(window_id=self.win_id, height=h, width=w, posx=x, posy=y, is_hidden=is_hidden)
        props.save()
        if hasattr(self, '_refresh_timer') and getattr(self, '_refresh_timer') is not None:
            getattr(self, '_refresh_timer').Stop()