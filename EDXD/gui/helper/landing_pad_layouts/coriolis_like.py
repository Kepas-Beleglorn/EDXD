import wx
import math

from EDXD.data_handler.helper.landing_pad_layouts.coriolis_like import StationLayout, LandingPad


class CoriolisDisplay(wx.Panel):
    """Coriolis station landing pad display - simple layered approach"""

    def __init__(self, parent, layout: StationLayout):
        super().__init__(parent)
        self.layout = layout
        self.SetBackgroundColour(wx.Colour("#121212"))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

        self.colors = {
            'grid': wx.Colour(0, 200, 250, 150),  # Dark brown for grid background
            'gap': wx.Colour(25, 12, 6),  # Dark brown for gap
            'pad': wx.Colour(60, 30, 15),  # Lighter brown for pads
            'assigned': wx.Colour(220, 100, 20),  # Orange for assigned pad
            'text': wx.Colour(0, 200, 220),  # Cyan for center number
            'dot_red': wx.Colour(255, 50, 50),
            'dot_green': wx.Colour(50, 255, 50),
        }

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(wx.Colour("#121212")))
        dc.Clear()

        client_size = self.GetClientSize()
        center_x = client_size.width / 2
        center_y = client_size.height / 2

        margin = 20
        max_radius = min(center_x, center_y) - margin
        r = max_radius / 8.0

        # Layer 1: Draw the dark grid circle (radius 8r)
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(self.colors['grid']))
        dc.DrawCircle(int(center_x), int(center_y), int(8 * r))

        # Layer 2: Draw all landing pads on top
        for pad in self.layout.pads:
            is_assigned = (pad.pad_number == self.layout.assigned_pad)
            self.draw_pad(dc, center_x, center_y, r, pad, is_assigned)

        # Layer 3: Draw center info
        self.draw_center_info(dc, center_x, center_y, r)

    def draw_pad(self, dc: wx.DC, cx: float, cy: float, r: float,
                 pad: LandingPad, is_assigned: bool):
        """Draw a single landing pad segment - spans multiple rings as one piece"""
        if is_assigned:
            color = self.colors['assigned']
        elif pad.pad_number == 0:
            color = self.colors['gap']
        else:
            color = self.colors['pad']

        # Convert angles to radians
        start_rad = math.radians(pad.start_angle)
        end_rad = math.radians(pad.end_angle)

        # Calculate radii (ring N spans from N*r to (N+1)*r)
        inner_radius = (r * pad.ring_start)+2
        outer_radius = (r * (pad.ring_end + 1))-3

        # Create polygon for the segment
        points = []
        num_arc_points = 50

        # Outer arc
        for i in range(num_arc_points + 1):
            angle = start_rad + (end_rad - start_rad) * (i / num_arc_points)
            x = cx + outer_radius * math.cos(angle)
            y = cy + outer_radius * math.sin(angle)
            points.append(wx.Point(int(x), int(y)))

        # Inner arc (reverse)
        for i in range(num_arc_points, -1, -1):
            angle = start_rad + (end_rad - start_rad) * (i / num_arc_points)
            x = cx + inner_radius * math.cos(angle)
            y = cy + inner_radius * math.sin(angle)
            points.append(wx.Point(int(x), int(y)))

        # Draw as one solid piece
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(color))
        dc.DrawPolygon(points)

    def draw_center_info(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw center circle with pad number and indicators"""
        # Center circle background
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.Colour(25, 12, 6)))
        dc.DrawCircle(int(cx), int(cy), int(r))

        # Center circle border
        dc.SetPen(wx.Pen(wx.Colour(40, 20, 10), 2))
        dc.DrawCircle(int(cx), int(cy), int(r))

        # Pad number
        if self.layout.assigned_pad:
            dc.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            dc.SetTextForeground(self.colors['text'])

            label = str(self.layout.assigned_pad)
            text_width, text_height = dc.GetTextExtent(label)

            text_x = cx - text_width / 2
            text_y = cy - text_height / 2

            dc.DrawLabel(label, wx.Rect(int(text_x), int(text_y), text_width, text_height))

        # Red and green dots (fixed position)
        dot_radius = 6
        dot_offset = r * 0.7

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(self.colors['dot_red']))
        dc.DrawCircle(int(cx - dot_offset), int(cy), dot_radius)

        dc.SetBrush(wx.Brush(self.colors['dot_green']))
        dc.DrawCircle(int(cx + dot_offset), int(cy), dot_radius)