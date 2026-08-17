#!/usr/bin/env python3
"""
Elite Dangerous Landing Pad Indicator Prototype v8
Updated: Fixed position for red/green dots regardless of number width
Integrates with EDXD project
"""

import wx
import math
import random
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class PadSize(Enum):
    """Landing pad size categories"""
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"


class PadStatus(Enum):
    """Landing pad status"""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    OCCUPIED = "occupied"
    DISABLED = "disabled"


@dataclass
class LandingPad:
    """Represents a single landing pad"""
    pad_number: int
    size: PadSize
    status: PadStatus
    ring: int  # 1, 2, or 3 (inner to outer)
    position: int  # 0-11 (clock position, 0 = 12 o'clock)
    angle: float = 0.0  # Angle in degrees


@dataclass
class StationLayout:
    """Station landing pad layout"""
    station_name: str
    station_type: str
    pads: List[LandingPad]
    assigned_pad: Optional[int] = None


class RadarDisplay(wx.Panel):
    """Radar-style landing pad display with correct proportions"""

    def __init__(self, parent, layout: StationLayout):
        super().__init__(parent)
        self.layout = layout
        # Panel background (outside grid) is #121212
        self.SetBackgroundColour(wx.Colour("#121212"))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

        # Colors matching reference image
        self.colors = {
            'grid_background': wx.Colour(30, 15, 8),  # Dark brown for grid area and segments
            'ring': wx.Colour(50, 25, 12),  # Darker brown rings/lines
            'assigned': wx.Colour(220, 100, 20),  # Orange for assigned pad
            'text': wx.Colour(0, 200, 220),  # Cyan for pad number
            'dot_red': wx.Colour(255, 50, 50),  # Red dot
            'dot_green': wx.Colour(50, 255, 50),  # Green dot
        }

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        # Clear with the panel background color (#121212)
        dc.SetBackground(wx.Brush(wx.Colour("#121212")))
        dc.Clear()

        client_size = self.GetClientSize()
        center_x = client_size.width / 2
        center_y = client_size.height / 2

        # Calculate base radius (center circle radius = r)
        margin = 20
        max_radius = min(center_x, center_y) - margin
        r = max_radius / 4.0  # Base unit radius

        # 1. Draw the full grid background (circle of radius 4r)
        self.draw_grid_background(dc, center_x, center_y, r)

        # 2. Draw the rings and lines on top
        self.draw_rings(dc, center_x, center_y, r)
        self.draw_radial_lines(dc, center_x, center_y, r)

        # 3. Draw the assigned pad highlight (on top of lines)
        self.draw_assigned_pad(dc, center_x, center_y, r)

        # 4. Draw center info (on top of everything)
        self.draw_center_info(dc, center_x, center_y, r)

    def draw_grid_background(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw the full circular background for the grid area"""
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(self.colors['grid_background']))
        dc.DrawCircle(int(cx), int(cy), int(4 * r))

    def draw_rings(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw three concentric rings at 2r, 3r, 4r"""
        dc.SetPen(wx.Pen(self.colors['ring'], 3))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 0)))  # Transparent brush

        # Center circle boundary (r)
        dc.DrawCircle(int(cx), int(cy), int(r))

        # Three docking rings at 2r, 3r, 4r
        ring_radii = [2 * r, 3 * r, 4 * r]

        for ring_radius in ring_radii:
            dc.DrawCircle(int(cx), int(cy), int(ring_radius))

    def draw_radial_lines(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw 12 radial lines, rotated so segments align with clock numbers"""
        dc.SetPen(wx.Pen(self.colors['ring'], 3))

        num_lines = 12

        for i in range(num_lines):
            # Each line is at position * 30 + 15 degrees offset
            angle_deg = (i * 30) - 90 + 15
            angle = math.radians(angle_deg)

            # Lines go from center circle (r) to outer ring (4r)
            x1 = cx + r * math.cos(angle)
            y1 = cy + r * math.sin(angle)
            x2 = cx + 4 * r * math.cos(angle)
            y2 = cy + 4 * r * math.sin(angle)

            dc.DrawLine(int(x1), int(y1), int(x2), int(y2))

    def draw_assigned_pad(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw the assigned landing pad highlight"""
        if not self.layout.assigned_pad:
            return

        # Find the assigned pad
        assigned = next((p for p in self.layout.pads if p.pad_number == self.layout.assigned_pad), None)
        if not assigned:
            return

        # Calculate ring boundaries
        ring_inner_radius = r * assigned.ring
        ring_outer_radius = r * (assigned.ring + 1)

        # Calculate segment angles
        segment_angle = 30.0  # 360 / 12
        center_angle = (assigned.position * segment_angle) - 90  # Center of segment
        start_angle = center_angle - (segment_angle / 2)
        end_angle = center_angle + (segment_angle / 2)

        # Convert to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        # Create polygon for the segment
        points = []

        # Number of points for smooth arcs
        num_arc_points = 15

        # Outer arc (clockwise)
        for i in range(num_arc_points + 1):
            angle = start_rad + (end_rad - start_rad) * (i / num_arc_points)
            x = cx + ring_outer_radius * math.cos(angle)
            y = cy + ring_outer_radius * math.sin(angle)
            points.append(wx.Point(int(x), int(y)))

        # Inner arc (counter-clockwise)
        for i in range(num_arc_points, -1, -1):
            angle = start_rad + (end_rad - start_rad) * (i / num_arc_points)
            x = cx + ring_inner_radius * math.cos(angle)
            y = cy + ring_inner_radius * math.sin(angle)
            points.append(wx.Point(int(x), int(y)))

        # Draw the filled segment
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(self.colors['assigned']))
        dc.DrawPolygon(points)

    def draw_center_info(self, dc: wx.DC, cx: float, cy: float, r: float):
        """Draw center circle with pad number and indicators"""
        # Draw center circle background
        dc.SetPen(wx.Pen(self.colors['ring'], 3))
        dc.SetBrush(wx.Brush(self.colors['grid_background']))
        dc.DrawCircle(int(cx), int(cy), int(r))

        # Draw pad number in center
        if self.layout.assigned_pad:
            dc.SetFont(wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            dc.SetTextForeground(self.colors['text'])

            label = str(self.layout.assigned_pad)
            text_width, text_height = dc.GetTextExtent(label)

            text_x = cx - text_width / 2
            text_y = cy - text_height / 2

            dc.DrawLabel(label, wx.Rect(int(text_x), int(text_y), text_width, text_height))

        # Draw red and green dots with FIXED positions
        # Positions are now based on a fixed offset from center, not text width
        dot_radius = 6
        # Fixed offset: 40% of the center circle radius
        dot_offset = r * 0.7

        # Red dot (left) - always at same position
        dc.SetBrush(wx.Brush(self.colors['dot_red']))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawCircle(int(cx - dot_offset), int(cy), dot_radius)

        # Green dot (right) - always at same position
        dc.SetBrush(wx.Brush(self.colors['dot_green']))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawCircle(int(cx + dot_offset), int(cy), dot_radius)


class StationDataGenerator:
    """Generate realistic station landing pad layouts"""

    @staticmethod
    def generate_orbis(station_name: str) -> StationLayout:
        """Generate Orbis station layout with 12 segments × 3 rings = 36 pads"""
        pads = []

        # 3 rings, each with 12 positions (clock-style)
        for ring in range(1, 4):  # rings 1, 2, 3
            for position in range(12):  # positions 0-11 (clock)
                # Pad numbering: ring 1 = 1-12, ring 2 = 13-24, ring 3 = 25-36
                pad_number = (ring - 1) * 12 + position + 1

                # Determine pad size based on ring
                if ring == 1:
                    size = PadSize.SMALL
                elif ring == 2:
                    size = PadSize.MEDIUM
                else:
                    size = PadSize.LARGE

                # Calculate angle (0 = 12 o'clock position, centered)
                angle = position * 30.0 - 90  # -90 to start at 12 o'clock

                # Random status
                status_roll = random.random()
                if status_roll < 0.7:
                    status = PadStatus.AVAILABLE
                elif status_roll < 0.9:
                    status = PadStatus.OCCUPIED
                else:
                    status = PadStatus.DISABLED

                pads.append(LandingPad(
                    pad_number=pad_number,
                    size=size,
                    status=status,
                    ring=ring,
                    position=position,
                    angle=angle
                ))

        # Assign a random medium or large pad (rings 2 or 3)
        assignable_pads = [p.pad_number for p in pads if p.ring >= 1]
        assigned = random.choice(assignable_pads) if assignable_pads else None

        return StationLayout(
            station_name=station_name,
            station_type="Orbis Starport",
            pads=pads,
            assigned_pad=assigned
        )


class LandingPadFrame(wx.Frame):
    """Main application frame"""

    def __init__(self):
        super().__init__(None, title="EDXD - Landing Pad Indicator", size=(600, 600))

        # Generate sample data
        self.station = StationDataGenerator.generate_orbis("Jameson Memorial")

        # Create radar display
        self.radar_display = RadarDisplay(self, self.station)

        # Create status bar
        self.CreateStatusBar(2)
        self.update_status_bar()

        # Create menu
        self.create_menu()

        self.Centre()

    def update_status_bar(self):
        """Update status bar with current info"""
        self.SetStatusText(f"Station: {self.station.station_name}", 0)
        self.SetStatusText(f"Assigned Pad: {self.station.assigned_pad}", 1)

    def create_menu(self):
        """Create application menu"""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        refresh_item = file_menu.Append(wx.ID_REFRESH, "Refresh\tCtrl+R", "Refresh display")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit application")

        menubar.Append(file_menu, "File")

        self.SetMenuBar(menubar)

        # Bind events
        self.Bind(wx.EVT_MENU, self.on_refresh, refresh_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

    def on_refresh(self, event):
        """Refresh the display with new random data"""
        random.seed()

        # Regenerate data
        self.station = StationDataGenerator.generate_orbis("Jameson Memorial")

        # Update display
        self.radar_display.layout = self.station
        self.radar_display.Refresh()

        self.update_status_bar()

    def on_exit(self, event):
        """Exit application"""
        self.Close()


def main():
    """Main entry point"""
    app = wx.App(False)
    frame = LandingPadFrame()
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()