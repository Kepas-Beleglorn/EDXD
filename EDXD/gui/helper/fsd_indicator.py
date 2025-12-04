import math
import wx
from EDXD.gui.helper.theme_handler import get_theme, apply_theme
# FSDIndicator - revised to draw a hollow triangular band (like the reference image)
# - Each side is drawn as a polygon band filled with a linear gradient.
# - Small outer corner highlights create the "cut" look at each corner.
# - Pulsing is done by modulating the gradient intensity and a tiny overall scale.
#
# Usage:
#   widget = FSDIndicator(parent, size=wx.Size(400, 360))
#   widget.set_text("FSD SUPER CHARGED")
#   widget.set_state(FSDIndicator.STATE_CHARGING)
#
# Notes:
# - Uses GraphicsContext CreateLinearGradientBrush for smooth gradients.
# - Uses a simple centroid-based inset to form the inner hole; this is robust and fast.
# - Tune BAND_RATIO, PULSE_SPEED, COLOR_* at top for different looks.

class FSDIndicator(wx.Panel):
    STATE_OFF = "off"
    STATE_CHARGING = "charging"
    STATE_SUPERCHARGED = "supercharged"

    # Visual tuning
    BASE_COLOR_OUTER = wx.Colour(0, 200, 255)      # saturated cyan
    BASE_COLOR_INNER = wx.Colour(170, 255, 255)    # lighter cyan (used as gradient start)
    EDGE_GAP_RATIO_OUTER = 0.03  # fraction of each outer edge to trim from both ends (0..0.5)
    EDGE_GAP_RATIO_INNER = 0.03  # fraction of each inner edge to trim from both ends (0..0.5)
    BAND_RATIO = 0.45      # how thick the band is relative to triangle size (0..0.5)
    PULSE_SPEED = 0.07     # base speed (radians per tick)
    TIMER_MS = 30

    def __init__(self, parent, id=wx.ID_ANY, size=wx.Size(420, 400)):
        super().__init__(parent, id=id, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.text = ""
        self.state = self.STATE_OFF
        self._phase = 0.0
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, lambda evt: self.Refresh())

        apply_theme(self)
        self.SetMinSize(size)
        self.SetMaxSize(size)

        # font: prefer "EURO CAPS", fallback to bold sans
        desired_point_size = max(20, int(self.GetSize().GetHeight() * 0.12))
        try:
            f = wx.Font(desired_point_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="EURO CAPS")
            if not f.IsOk():
                raise Exception("Font missing")
            self._font = f
        except Exception:
            self._font = wx.Font(desired_point_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self._base_outer = self.BASE_COLOR_OUTER
        self._base_inner = self.BASE_COLOR_INNER

        self._pulse_speed = self.PULSE_SPEED
        self._running = False

    def set_text(self, text: str):
        self.text = text or ""
        self.Refresh()

    def set_state(self, state: str):
        if state not in (self.STATE_OFF, self.STATE_CHARGING, self.STATE_SUPERCHARGED):
            state = self.STATE_OFF

        self.state = state
        if state == self.STATE_OFF:
            if self._timer.IsRunning():
                self._timer.Stop()
            self._running = False
        else:
            if not self._timer.IsRunning():
                self._timer.Start(self.TIMER_MS)
            self._running = True

        # tweak pulse speed depending on state
        if state == self.STATE_CHARGING:
            self._pulse_speed = self.PULSE_SPEED * 1.1
        elif state == self.STATE_SUPERCHARGED:
            self._pulse_speed = self.PULSE_SPEED * 1.6
        else:
            self._pulse_speed = self.PULSE_SPEED
        self.set_text(state)
        self.Refresh()

    # little linear interpolation helper
    def _lerp_color(self, c1: wx.Colour, c2: wx.Colour, t: float) -> wx.Colour:
        t = max(0.0, min(1.0, t))
        return wx.Colour(
            int(c1.Red() + (c2.Red() - c1.Red()) * t),
            int(c1.Green() + (c2.Green() - c1.Green()) * t),
            int(c1.Blue() + (c2.Blue() - c1.Blue()) * t),
            int(c1.Alpha() + (c2.Alpha() - c1.Alpha()) * t),
        )

    def _on_timer(self, evt):
        self._phase += self._pulse_speed
        # keep phase in reasonable range
        if self._phase > math.pi * 10000:
            self._phase = self._phase % (math.pi * 2)
        self.Refresh(False)

    def _triangle_vertices(self, cx, cy, radius, rotation= -math.pi/2):
        # produce 3 outer triangle vertices (pointing up by default)
        pts = []
        for i in range(3):
            angle = rotation + i * (2 * math.pi / 3)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            pts.append((x, y))
        return pts

    def _centroid(self, pts):
        x = sum(p[0] for p in pts) / len(pts)
        y = sum(p[1] for p in pts) / len(pts)
        return (x, y)

    def _inset_triangle(self, outer_pts, inset_ratio):
        # Move each outer vertex towards centroid by inset_ratio (0..1) to get inner triangle
        cx, cy = self._centroid(outer_pts)
        inner = []
        for (x, y) in outer_pts:
            ix = x + (cx - x) * inset_ratio
            iy = y + (cy - y) * inset_ratio
            inner.append((ix, iy))
        return inner

    def _midpoint(self, a, b):
        return ((a[0]+b[0])/2.0, (a[1]+b[1])/2.0)

    def _shorten_edge(self, a, b, gap_ratio):
        # return two points along edge ab shortened by gap_ratio at both ends
        # i.e. new_a = a + (b-a)*gap_ratio, new_b = b + (a-b)*gap_ratio
        ax, ay = a
        bx, by = b
        new_a = (ax + (bx - ax) * gap_ratio, ay + (by - ay) * gap_ratio)
        new_b = (bx + (ax - bx) * gap_ratio, by + (ay - by) * gap_ratio)
        return new_a, new_b

    def _draw_band(self, gc, outer_a, outer_b, inner_b, inner_a, pulse_t, color_outer, color_inner):
        # outer_a->outer_b->inner_b->inner_a polygon filled with a linear gradient
        # BUT: shorten outer edge endpoints to leave a gap at each tip (EDGE_GAP_RATIO)
        outer_a_s, outer_b_s = self._shorten_edge(outer_a, outer_b, self.EDGE_GAP_RATIO_OUTER)
        inner_a_s, inner_b_s = self._shorten_edge(inner_a, inner_b, self.EDGE_GAP_RATIO_INNER)

        outer_mid = self._midpoint(outer_a_s, outer_b_s)
        inner_mid = self._midpoint(inner_a_s, inner_b_s)

        # modulate colors by pulse_t (0..1) to get a glowing effect
        glow_outer = self._lerp_color(color_outer, wx.Colour(255, 255, 255), pulse_t * 0.45)
        glow_inner = self._lerp_color(color_inner, wx.Colour(255, 255, 255), pulse_t * 0.55)

        # create gradient brush
        try:
            brush = gc.CreateLinearGradientBrush(inner_mid[0], inner_mid[1], outer_mid[0], outer_mid[1], glow_inner, glow_outer)
        except Exception:
            # fallback: solid brush
            brush = wx.Brush(glow_outer)

        gc.SetBrush(brush)
        pen = gc.CreatePen(wx.Pen(wx.Colour(0, 0, 0, 0), 0))  # transparent/none-stroke
        gc.SetPen(pen)

        path = gc.CreatePath()
        path.MoveToPoint(outer_a_s[0], outer_a_s[1])
        path.AddLineToPoint(outer_b_s[0], outer_b_s[1])
        path.AddLineToPoint(inner_b_s[0], inner_b_s[1])
        path.AddLineToPoint(inner_a_s[0], inner_a_s[1])
        path.CloseSubpath()
        gc.FillPath(path)

    def _on_paint(self, evt):
        dc = wx.BufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        gc.SetAntialiasMode(wx.ANTIALIAS_DEFAULT)

        w, h = self.GetClientSize().GetWidth(), self.GetClientSize().GetHeight()
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        # compute pulse and tiny scale
        pulse = 0.5 + 0.5 * math.sin(self._phase)  # 0..1
        if self.state == self.STATE_CHARGING:
            pulse_t = 0.35 + 0.65 * pulse
            scale_factor = 1.0 + 0.005 * pulse
        elif self.state == self.STATE_SUPERCHARGED:
            pulse_t = 0.6 + 0.9 * pulse
            scale_factor = 1.0 + 0.012 * pulse
        else:
            pulse_t = 0.05 + 0.1 * pulse
            scale_factor = 1.0

        # triangle geometry
        cx, cy = w * 0.5, h * 0.5
        # radius limited by panel size
        radius = min(w, h) * 0.44 * scale_factor
        outer = self._triangle_vertices(cx, cy, radius, rotation=-math.pi/2)
        # inset ratio derived from BAND_RATIO and radius; clamp
        inset_ratio = max(0.08, min(0.45, self.BAND_RATIO))
        inner = self._inset_triangle(outer, inset_ratio)

        # draw each band (side)
        for i in range(3):
            oa = outer[i]
            ob = outer[(i + 1) % 3]
            ia = inner[i]
            ib = inner[(i + 1) % 3]
            # for color variation, mix base inner/out color slightly per side
            col_in = self._lerp_color(self._base_inner, wx.Colour(255, 255, 255), 0.06 * (i+1))
            col_out = self._lerp_color(self._base_outer, wx.Colour(0, 255, 255), 0.08 * (i+1))
            self._draw_band(gc, oa, ob, ib, ia, pulse_t, col_out, col_in)

        # Foreground text (centered)
        if self.text:
            # Use dc for text for better font support on some platforms
            dc.SetFont(self._font)
            # text color bright cyan-ish, slightly modulated by pulse
            text_col = self._lerp_color(wx.Colour(200, 222, 255), wx.Colour(200, 222, 255), 0.35 * pulse_t)
            # ensure good contrast with tiny shadow
            shadow = wx.Colour(0, 0, 0, 160)
            dc.SetTextForeground(shadow)
            tw, th = dc.GetTextExtent(self.text)
            tx = cx - tw * 0.5
            ty = cy - th * 0.5
            dc.DrawText(self.text, int(tx + 2), int(ty))
            dc.SetTextForeground(text_col)
            dc.DrawText(self.text, int(tx), int(ty))
