import wx

class CustomFrame(wx.Frame):
    RESIZE_MARGIN = 8  # px area at edge/corner for resizing

    def __init__(self, *args, **kwargs):
        super().__init__(None, style=wx.NO_BORDER)
        self._resizing = False
        self._resize_dir = None
        self._mouse_start = None
        self._frame_start = None

        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

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

    def on_mouse_down(self, evt):
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