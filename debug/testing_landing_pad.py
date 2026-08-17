#!/usr/bin/env python3
"""
Elite Dangerous Landing Pad Indicator - Coriolis Station Layout
Simple layered approach: grid first, then pads on top
"""

import wx
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class LandingPad:
    """Represents a single landing pad"""
    pad_number: int
    clock_pos: int
    start_angle: float
    end_angle: float
    ring_start: int
    ring_end: int


@dataclass
class StationLayout:
    """Station landing pad layout"""
    station_name: str
    station_type: str
    pads: List[LandingPad]
    assigned_pad: Optional[int] = None


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
        print(pad.pad_number)
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


class CoriolisDataGenerator:
    """Generate Coriolis station layout from specification table"""

    @staticmethod
    def get_clock_angles(clock_num: int) -> Tuple[float, float]:
        """Get start and end angles for a clock position (30° segments)"""
        # Clock 12 = North (-90°), Clock 6 = South (-270° or 90°)
        # Each clock is 30° wide, centered on the clock number
        center = (clock_num - 3) * 30.0

        start = center - 14.0
        end = center + 14.0

        return start, end

    @staticmethod
    def generate_coriolis(station_name: str) -> StationLayout:
        pads = []

        # Exact pad layout from specification table
        # Format: (pad_number, clock_position, ring_start, ring_end)
        # pad_number = 0 means GAP
        pad_layout = [
            (1, 6, 7, 7),
            (2, 6, 4, 6),
            (3, 6, 2, 3),
            (4, 6, 1, 1),
            (5, 7, 6, 7),
            (6, 7, 5, 5),
            (7, 7, 3, 4),
            (8, 7, 1, 2),
            (9, 8, 5, 7),
            (0, 8, 4, 4),  # GAP
            (10, 8, 1, 3),
            (11, 9, 6, 7),
            (12, 9, 5, 5),
            (13, 9, 4, 4),
            (14, 9, 3, 3),
            (15, 9, 1, 2),
            (16, 10, 7, 7),
            (17, 10, 4, 6),
            (18, 10, 2, 3),
            (19, 10, 1, 1),
            (20, 11, 6, 7),
            (21, 11, 5, 5),
            (22, 11, 3, 4),
            (23, 11, 1, 2),
            (24, 12, 5, 7),
            (0, 12, 4, 4),  # GAP
            (25, 12, 1, 3),
            (26, 1, 6, 7),
            (27, 1, 5, 5),
            (28, 1, 4, 4),
            (29, 1, 3, 3),
            (30, 1, 1, 2),
            (31, 2, 7, 7),
            (32, 2, 4, 6),
            (33, 2, 2, 3),
            (34, 2, 1, 1),
            (35, 3, 6, 7),
            (36, 3, 5, 5),
            (37, 3, 3, 4),
            (38, 3, 1, 2),
            (39, 4, 5, 7),
            (0, 4, 4, 4),  # GAP
            (40, 4, 1, 3),
            (41, 5, 6, 7),
            (42, 5, 5, 5),
            (43, 5, 4, 4),
            (44, 5, 3, 3),
            (45, 5, 1, 2),
        ]

        for pad_num, clock_pos, ring_start, ring_end in pad_layout:
            start_angle, end_angle = CoriolisDataGenerator.get_clock_angles(clock_pos)

            pads.append(LandingPad(
                pad_number=pad_num,
                clock_pos=clock_pos,
                start_angle=start_angle,
                end_angle=end_angle,
                ring_start=ring_start,
                ring_end=ring_end
            ))

        return StationLayout(
            station_name=station_name,
            station_type="Coriolis Starport",
            pads=pads,
            assigned_pad=29
        )


class LandingPadFrame(wx.Frame):
    """Main application frame"""

    def __init__(self):
        super().__init__(None, title="EDXD - Coriolis Landing Pad Indicator", size=(800, 800))

        self.station = CoriolisDataGenerator.generate_coriolis("Jameson Memorial")
        self.display = CoriolisDisplay(self, self.station)

        self.CreateStatusBar(2)
        self.update_status_bar()
        self.create_menu()
        self.Centre()

    def update_status_bar(self):
        self.SetStatusText(f"Station: {self.station.station_name}", 0)
        self.SetStatusText(f"Assigned Pad: {self.station.assigned_pad}", 1)

    def create_menu(self):
        menubar = wx.MenuBar()

        test_menu = wx.Menu()

        clock_groups = [
            ("Clock 12 (North)", [24, 25]),
            ("Clock 1", [26, 27, 28, 29, 30]),
            ("Clock 2", [31, 32, 33, 34]),
            ("Clock 3", [35, 36, 37, 38]),
            ("Clock 4", [39, 40]),
            ("Clock 5", [41, 42, 43, 44, 45]),
            ("Clock 6 (South)", [1, 2, 3, 4]),
            ("Clock 7", [5, 6, 7, 8]),
            ("Clock 8", [9, 10]),
            ("Clock 9", [11, 12, 13, 14, 15]),
            ("Clock 10", [16, 17, 18, 19]),
            ("Clock 11", [20, 21, 22, 23]),
        ]

        for group_name, pad_nums in clock_groups:
            submenu = wx.Menu()
            for pad_num in pad_nums:
                item = submenu.Append(wx.ID_ANY, f"Pad {pad_num:02d}")
                self.Bind(wx.EVT_MENU, lambda evt, p=pad_num: self.on_assign_pad(p), item)
            test_menu.AppendSubMenu(submenu, group_name)

        menubar.Append(test_menu, "Test")

        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit application")
        menubar.Append(file_menu, "File")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

    def on_assign_pad(self, pad_num: int):
        self.station.assigned_pad = pad_num
        self.display.Refresh()
        self.update_status_bar()

    def on_exit(self, event):
        self.Close()


def main():
    app = wx.App(False)
    frame = LandingPadFrame()
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()