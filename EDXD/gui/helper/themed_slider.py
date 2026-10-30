import wx
import math


class ThemedSlider(wx.Control):
    """Custom-drawn slider with optional logarithmic or power-curve mapping."""

    def __init__(self, parent, value=0, min_val=0, max_val=100,
                 accent="#4ecdc4", groove="#3a3a50", handle_bg="#1e1e2e",
                 scale="linear", exponent=2.0, lin_thresh=1000, size=(200, 24)):
        """
        scale: "linear" | "log" | "power" | "symlog"
        lin_thresh: (symlog) value below which the mapping is linear.
                    Must be > 0 and < max_val.
        """
        super().__init__(parent, style=wx.BORDER_NONE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetBackgroundColour(parent.GetBackgroundColour())

        self.Name = "themed_slider"

        self._min = min_val
        self._max = max_val
        self._value = value
        self._scale = scale
        self._exponent = exponent
        self._lin_thresh = lin_thresh

        if scale == "log" and min_val <= 0:
            raise ValueError("Log scale requires min_val > 0 (use symlog for 0)")
        if scale == "symlog" and not (0 < lin_thresh < max_val):
            raise ValueError("symlog needs 0 < lin_thresh < max_val")

        # fraction of the bar devoted to the linear [0..lin_thresh] region,
        # chosen so the curve is C1-continuous at the transition point
        self._f = 1.0 / (1.0 + math.log(max_val / lin_thresh)) if scale == "symlog" else 0.0

        self._accent = wx.Colour(accent)
        self._groove = wx.Colour(groove)
        self._handle_bg = wx.Colour(handle_bg)
        self._dragging = False
        self.SetMinSize(size)

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_up)
        self.Bind(wx.EVT_MOTION, self._on_motion)
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))

    # --- coordinate mapping (the core of the non-linearity) ---

    def _ratio(self):
        """value → 0.0..1.0"""
        if self._max == self._min:
            return 0.0
        if self._scale == "symlog":
            L, f = self._lin_thresh, self._f
            if self._value <= L:
                return (self._value / L) * f
            return f + (1.0 - f) * math.log(self._value / L) / math.log(self._max / L)
        if self._scale == "log":
            return math.log(self._value / self._min) / math.log(self._max / self._min)
        if self._scale == "power":
            linear = (self._value - self._min) / (self._max - self._min)
            return linear ** (1.0 / self._exponent)
        return (self._value - self._min) / (self._max - self._min)

    def _value_from_ratio(self, r):
        """0.0..1.0 → value"""
        r = max(0.0, min(1.0, r))
        if self._scale == "symlog":
            L, f = self._lin_thresh, self._f
            if r <= f:
                return (r / f) * L
            return L * (self._max / L) ** ((r - f) / (1.0 - f))
        if self._scale == "log":
            return self._min * (self._max / self._min) ** r
        if self._scale == "power":
            return self._min + (self._max - self._min) * (r ** self._exponent)
        return self._min + (self._max - self._min) * r

    # --- public API ---

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        value = max(self._min, min(self._max, value))
        if self._scale in ("log", "power", "symlog"):
            value = round(value)

        if value != self._value:
            self._value = value
            self.Refresh()
            self._notify()

    def SetRange(self, min_val, max_val):
        self._min, self._max = min_val, max_val
        self.Refresh()

    def SetAccentColour(self, accent_colour):
        self._accent = accent_colour

    def SetGrooveColour(self, groove_colour):
        self._groove = groove_colour

    def SetHandleBgColour(self, handle_bg_colour):
        self._handle_bg = handle_bg_colour

    # --- internals ---

    def _value_from_x(self, x):
        w = self.GetClientSize().width
        margin = 10
        usable = max(1, w - 2 * margin)
        r = max(0.0, min(1.0, (x - margin) / usable))
        return int(round(self._value_from_ratio(r)))

    def _notify(self):
        evt = wx.CommandEvent(wx.wxEVT_SLIDER, self.GetId())
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()

        w, h = self.GetClientSize()
        groove_h = 6
        y = h // 2
        margin = 10
        x0, x1 = margin, w - margin

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(self._groove))
        dc.DrawRoundedRectangle(x0, y - groove_h // 2, x1 - x0, groove_h, groove_h // 2)

        handle_x = int(x0 + self._ratio() * (x1 - x0))
        if handle_x > x0:
            dc.SetBrush(wx.Brush(self._accent))
            dc.DrawRoundedRectangle(x0, y - groove_h // 2, handle_x - x0, groove_h, groove_h // 2)

        r = 9
        dc.SetBrush(wx.Brush(self._handle_bg))
        dc.SetPen(wx.Pen(self._accent, 2))
        dc.DrawCircle(handle_x, y, r)

    def _on_down(self, event):
        self._dragging = True
        self.SetFocus()
        self.SetValue(self._value_from_x(event.GetX()))

    def _on_up(self, event):
        self._dragging = False

    def _on_motion(self, event):
        if self._dragging:
            self.SetValue(self._value_from_x(event.GetX()))
