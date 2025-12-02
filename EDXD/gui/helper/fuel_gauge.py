import colorsys
import math

import wx

from EDXD.gui.helper.theme_handler import get_theme, apply_theme


class FuelGauge(wx.Panel):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        range=100,
        level=100,
        warning_threshold=10,
        show_scale=False,
        **kwargs
    ):
        super().__init__(parent, id, **kwargs)

        self._range = max(1, range)
        self._level = max(0, min(level, self._range))
        self._warning_threshold = warning_threshold
        self._show_scale = show_scale

        self._pulse_phase = 0.0
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self._timer)

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)  # for flicker-free drawing
        #self.SetBackgroundStyle(wx.BG_STYLE_PAINT)  # for flicker-free drawing
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        apply_theme(self)
        self.UpdateTimer()
        self.SetMinSize(wx.Size(200, 40 if not self._show_scale else 70))

    # ----- public API -----

    def SetRange(self, value):
        self._range = max(1, value)
        self._level = max(0, min(self._level, self._range))
        self.Refresh(False)

    def GetRange(self):
        return self._range

    def SetLevel(self, level):
        """Set the current fuel value (0..range)."""
        level = max(0, min(level, self._range))
        if level == self._level:
            return
        self._level = level
        self.UpdateTimer()
        self.Refresh(False)

    def GetLevel(self):
        return self._level

    def SetWarningThreshold(self, threshold):
        """Set warning threshold in percent (0..100)."""
        self._warning_threshold = threshold
        self.UpdateTimer()
        self.Refresh(False)

    def GetWarningThreshold(self):
        return self._warning_threshold

    def SetShowScale(self, show):
        self._show_scale = bool(show)
        if self._show_scale:
            self.SetMinSize(wx.Size(200, 70))
        else:
            self.SetMinSize(wx.Size(200, 40))
        self.Refresh(False)
        self.Layout()

    # ----- internal helpers / events -----

    def OnSize(self, event):
        self.Refresh(False)
        event.Skip()

    def OnTimer(self, event):
        # advance pulse phase for smooth flashing
        self._pulse_phase = (self._pulse_phase + 0.06) % 1.0
        self.Refresh(False)

    def UpdateTimer(self):
        frac = self._level / float(self._range)
        if frac * 100.0 <= self._warning_threshold:
            if not self._timer.IsRunning():
                self._pulse_phase = 0.0
                self._timer.Start(50)  # ~20 FPS
        else:
            if self._timer.IsRunning():
                self._timer.Stop()
                self._pulse_phase = 0.0

    def _get_bar_rect(self, rect):
        padding = 6
        top_offset = 0
        bottom_offset = 0
        if self._show_scale:
            top_offset = 16   # space for top labels
            bottom_offset = 16  # for bottom labels
        return wx.Rect(
            rect.x + padding,
            rect.y + padding + top_offset,
            rect.width - 2 * padding,
            rect.height - 2 * padding - top_offset - bottom_offset,
        )

    def _fraction_to_color(self, frac, brightness=1.0):
        # Map 0..1 to red-yellow-green using HSV.
        frac = max(0.0, min(1.0, frac))
        # Hue 0.0 (red) to ~0.33 (green)
        h = 0.33 * frac
        s = 1.0
        v = 1.0 * brightness
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return wx.Colour(int(r * 255), int(g * 255), int(b * 255))

    def OnPaint(self, event):
        width, height = self.GetClientSize()
        if width <= 0 or height <= 0:
            return

        # buffered paint
        bmp = wx.Bitmap(width, height)
        dc = wx.MemoryDC(bmp)
        gc = wx.GCDC(dc)

        # background
        bg = self.GetBackgroundColour()
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.Pen(bg))
        gc.DrawRectangle(0, 0, width, height)

        rect = wx.Rect(0, 0, width, height)
        bar_rect = self._get_bar_rect(rect)

        # compute fill fraction
        frac = self._level / float(self._range)

        # pulse brightness if in warning zone
        if frac * 100.0 <= self._warning_threshold:
            # pulse between 0.6 and 1.0 brightness
            pulse = 0.5 * (1.0 + math.sin(2 * math.pi * self._pulse_phase))
            brightness = 0.6 + 0.4 * pulse
        else:
            brightness = 1.0

        # draw bar background
        radius = min(bar_rect.height // 2, 8)
        gc.SetBrush(wx.Brush(wx.Colour(40, 40, 40)))
        gc.SetPen(wx.Pen(wx.Colour(90, 90, 90), 1))
        gc.DrawRoundedRectangle(
            bar_rect.x, bar_rect.y, bar_rect.width, bar_rect.height, radius
        )

        # draw filled portion
        if frac > 0:
            fill_width = max(2, int(bar_rect.width * frac))
            fill_rect = wx.Rect(
                bar_rect.x, bar_rect.y, fill_width, bar_rect.height
            )
            col = self._fraction_to_color(frac, brightness)
            gc.SetBrush(wx.Brush(col))
            gc.SetPen(wx.Pen(col))

            # clip to bar rect for rounded effect
            gc.SetClippingRegion(bar_rect)
            gc.DrawRoundedRectangle(
                fill_rect.x, fill_rect.y, fill_rect.width, fill_rect.height, radius
            )
            gc.DestroyClippingRegion()

        # optional scale ticks & labels
        if self._show_scale:
            self._draw_scale(gc, bar_rect)

        # percentage text in center
        txt = f"{int(round(frac * 100))}%"
        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        gc.SetFont(font)

        if frac * 100.0 <= self._warning_threshold:
            text_col = wx.Colour(255, 30, 30)
        else:
            text_col = wx.Colour(230, 230, 230)
        gc.SetTextForeground(text_col)
        tw, th = gc.GetTextExtent(txt)
        tx = bar_rect.x + (bar_rect.width - tw) // 2
        ty = bar_rect.y + (bar_rect.height - th) // 2
        gc.DrawText(txt, tx, ty)

        # blit to screen
        del gc
        dc.SelectObject(wx.NullBitmap)
        paint_dc = wx.BufferedPaintDC(self)
        paint_dc.DrawBitmap(bmp, 0, 0, True)

    def _draw_scale(self, gc, bar_rect):
        """Draw ticks + labels above and below, plus a coloured strip."""
        theme = get_theme()
        tick_count = 5  # 0,25,50,75,100
        tick_height = 6
        label_offset = -2

        gc.SetPen(wx.Pen(theme["foreground_hover"], 1))
        font = self.GetFont()
        font.SetPointSize(max(7, font.GetPointSize() - 1))
        gc.SetFont(font)
        gc.SetTextForeground(theme["foreground"])

        for i in range(tick_count):
            frac = i / (tick_count - 1)
            x = bar_rect.x + int(bar_rect.width * frac)
            # top tick
            y_top = bar_rect.y - 4
            gc.DrawLine(x, y_top, x, y_top - tick_height)
            label = str(int(frac * 100))
            tw, th = gc.GetTextExtent(label)
            lbl_x =x - tw // 2

            if i == 0:
                lbl_x = lbl_x + 3

            if i == tick_count - 1:
                lbl_x = lbl_x - 10

            gc.DrawText(
                label,
                lbl_x,
                y_top - tick_height - th - label_offset,
            )

            # bottom tick
            y_bottom = bar_rect.y + bar_rect.height + 4
            gc.DrawLine(x, y_bottom, x, y_bottom + tick_height)

        # bottom coloured gradient bar
        grad_height = 6
        grad_rect = wx.Rect(
            bar_rect.x,
            bar_rect.y + bar_rect.height + tick_height + 6,
            bar_rect.width - 0,
            grad_height,
        )
        steps = max(100, bar_rect.width // 3)
        for i in range(steps):
            frac = i / max(1, steps - 1)
            col = self._fraction_to_color(frac)
            gc.SetPen(wx.Pen(col))
            x = grad_rect.x + int(grad_rect.width * frac)
            gc.DrawLine(x, grad_rect.y, x, grad_rect.y + grad_rect.height)

