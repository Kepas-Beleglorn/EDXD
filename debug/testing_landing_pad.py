#!/usr/bin/env python3
"""
Elite Dangerous Landing Pad Indicator - Fleet Carrier Layout
Pixel-perfect positioning with bottom-center reference (X=0, Y=0)
"""

import wx
from dataclasses import dataclass
from typing import Optional, List, Tuple


# dimensions and margin
OFFSET_X  :int  = 25
OFFSET_Y  :int  = 75
MARGIN    :int  = 2
RATIO     :float  = 1.5
WIDTH_S   :int  = 80
HEIGHT_S  :int  = int(RATIO*WIDTH_S)
WIDTH_M   :int  = int(1.5*WIDTH_S)
HEIGHT_M  :int  = int(RATIO*WIDTH_M)
WIDTH_L   :int  = int(2*WIDTH_S)
HEIGHT_L  :int  = int(RATIO*WIDTH_L)

@dataclass
class CarrierPad:
    """Represents a single carrier landing pad"""
    pad_number: int
    size: str  # 'L', 'M', or 'S'
    x: int  # X position in pixels (relative to center)
    y: int  # Y position in pixels (relative to bottom)
    width: int
    height: int


@dataclass
class CarrierLayout:
    """Fleet carrier landing pad layout"""
    carrier_name: str
    carrier_id: str
    pads: List[CarrierPad]
    assigned_pad: Optional[int] = None


class CarrierDisplay(wx.Panel):
    """Fleet carrier landing pad display with pixel-perfect positioning"""

    def __init__(self, parent, layout: CarrierLayout):
        super().__init__(parent)
        self.layout = layout
        self.SetBackgroundColour(wx.Colour("#121212"))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

        # Colors matching the screenshot
        self.colors = {
            'background': wx.Colour(12, 12, 12),
            'pad_normal': wx.Colour(60, 30, 15),
            'pad_assigned': wx.Colour(220, 100, 20),
            'text': wx.Colour(0, 255, 0),
            'text_assigned': wx.Colour(0, 0, 0),
        }

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.colors['background']))
        dc.Clear()

        client_size = self.GetClientSize()

        # Draw carrier info at top
        self.draw_carrier_info(dc, client_size)

        # Draw all pads
        for pad in self.layout.pads:
            self.draw_pad(dc, pad)

    def draw_pad(self, dc: wx.DC, pad: CarrierPad):
        """Draw a single carrier pad at its exact position"""
        # Determine color
        if pad.pad_number == self.layout.assigned_pad:
            color = self.colors['pad_assigned']
            text_color = self.colors['text_assigned']
        else:
            color = self.colors['pad_normal']
            text_color = self.colors['text']

        # Draw pad rectangle
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(color))
        dc.DrawRectangle(pad.x+OFFSET_X, pad.y+OFFSET_Y, pad.width, pad.height)

    def draw_carrier_info(self, dc: wx.DC, size: wx.Size):
        """Draw carrier name and ID at top"""
        dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.SetTextForeground(wx.Colour(200, 200, 200))

        # Carrier name
        dc.DrawLabel(self.layout.carrier_name, wx.Rect(0, 10, size.width, 25), wx.ALIGN_CENTER)

        # Carrier ID
        dc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.SetTextForeground(wx.Colour(150, 150, 150))
        dc.DrawLabel(self.layout.carrier_id, wx.Rect(0, 30, size.width, 20), wx.ALIGN_CENTER)


class CarrierDataGenerator:
    """Generate fleet carrier landing pad layout with precise pixel positioning"""

    @staticmethod
    def generate_carrier(carrier_name: str, carrier_id: str) -> CarrierLayout:
        """
        Generate carrier layout with exact pixel positions.
        """
        pads = []

        # Define each pad with exact pixel coordinates
        # Format: (pad_number, size, x_position, y_position)

        X1_L = 2 * WIDTH_S + 4 * MARGIN     # Left large pads
        X2_L = X1_L + 2 * MARGIN + WIDTH_L  # Right large pads

        X1_M = X1_L - 2 * MARGIN - WIDTH_M  # Left medium pads
        X2_M = X2_L + 2 * MARGIN + WIDTH_L  # Right medium pads

        Y1_M = 4 * HEIGHT_L + 6 * MARGIN - HEIGHT_M # lower medium pads
        Y2_M = Y1_M - 2 * MARGIN - HEIGHT_M         # upper medium pads

        X_S = X2_L + WIDTH_L + 2 * MARGIN
        Y_S = Y2_M - 2 * MARGIN - HEIGHT_S

        pad_layout = [
            # Large pads
            {"num": 7, "size": "L", "x":    X1_L,   "y": 0},
            {"num": 8, "size": "L", "x":    X2_L,   "y": 0},
            {"num": 5, "size": "L", "x":    X1_L,   "y": HEIGHT_L + 2 * MARGIN},
            {"num": 6, "size": "L", "x":    X2_L,   "y": HEIGHT_L + 2 * MARGIN},
            {"num": 3, "size": "L", "x":    X1_L,   "y": 2 * HEIGHT_L + 4 * MARGIN},
            {"num": 4, "size": "L", "x":    X2_L,   "y": 2 * HEIGHT_L + 4 * MARGIN},
            {"num": 1, "size": "L", "x":    X1_L,   "y": 3 * HEIGHT_L + 6 * MARGIN},
            {"num": 2, "size": "L", "x":    X2_L,   "y": 3 * HEIGHT_L + 6 * MARGIN},

            # Medium pads
            {"num": 9,  "size": "M", "x": X1_M, "y": Y1_M},
            {"num": 10, "size": "M", "x": X1_M, "y": Y2_M},
            {"num": 11, "size": "M", "x": X2_M, "y": Y1_M},
            {"num": 12, "size": "M", "x": X2_M, "y": Y2_M},

            # Small pads
            {"num": 13, "size": "S", "x": 0, "y": Y_S},
            {"num": 16, "size": "S", "x": WIDTH_S + 2 * MARGIN, "y": Y_S},
            {"num": 14, "size": "S", "x": X_S, "y": Y_S},
            {"num": 15, "size": "S", "x": X_S + 2 * MARGIN + WIDTH_S, "y": Y_S},
        ]

        for pad_info in pad_layout:
            size = str(pad_info["size"])
            spec = CarrierDataGenerator.get_pad_spec(size)

            pads.append(CarrierPad(
                pad_number=int(pad_info["num"]),
                size=size,
                x=int(pad_info["x"]),
                y=int(pad_info["y"]),
                width=spec['width'],
                height=spec['height']
            ))

        return CarrierLayout(
            carrier_name=carrier_name,
            carrier_id=carrier_id,
            pads=pads,
            assigned_pad=5  # Default assigned pad
        )

    @staticmethod
    def get_pad_spec(size: str) -> dict:
        """Get pad dimensions for a given size"""
        specs = {
            'S': {'width': WIDTH_S, 'height': HEIGHT_S},
            'M': {'width': WIDTH_M, 'height': HEIGHT_M},
            'L': {'width': WIDTH_L, 'height': HEIGHT_L},
        }
        return specs[size]


class LandingPadFrame(wx.Frame):
    """Main application frame for carrier display"""

    def __init__(self):
        super().__init__(None, title="EDXD - Fleet Carrier Landing Pad Indicator", size=(1500, 1500))

        self.carrier = CarrierDataGenerator.generate_carrier("EDXD Carrier", "FC-001-EDXD")
        self.display = CarrierDisplay(self, self.carrier)

        self.CreateStatusBar(2)
        self.update_status_bar()
        self.create_menu()
        self.Centre()

    def update_status_bar(self):
        self.SetStatusText(f"Carrier: {self.carrier.carrier_name}", 0)
        self.SetStatusText(f"Assigned Pad: {self.carrier.assigned_pad}", 1)

    def create_menu(self):
        menubar = wx.MenuBar()

        test_menu = wx.Menu()
        for pad_num in range(1, 17):
            item = test_menu.Append(wx.ID_ANY, f"Assign Pad {pad_num}")
            self.Bind(wx.EVT_MENU, lambda evt, p=pad_num: self.on_assign_pad(p), item)

        menubar.Append(test_menu, "Test")

        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit application")
        menubar.Append(file_menu, "File")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

    def on_assign_pad(self, pad_num: int):
        self.carrier.assigned_pad = pad_num
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