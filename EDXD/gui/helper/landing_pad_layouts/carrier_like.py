import wx
from EDXD.data_handler.helper.landing_pad_layouts.carrier_like import CarrierPad, CarrierLayout, OFFSET_X, OFFSET_Y

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
            'background': wx.Colour("#121212"),
            'pad_normal': wx.Colour(60, 30, 15),
            'pad_assigned': wx.Colour(220, 100, 20),
        }

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.colors['background']))
        dc.Clear()

        # Draw all pads
        for pad in self.layout.pads:
            self.draw_pad(dc, pad)

    def draw_pad(self, dc: wx.DC, pad: CarrierPad):
        """Draw a single carrier pad at its exact position"""
        # Determine color
        if pad.pad_number == self.layout.assigned_pad:
            color = self.colors['pad_assigned']
        else:
            color = self.colors['pad_normal']

        # Draw pad rectangle
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(color))
        dc.DrawRectangle(pad.x+OFFSET_X, pad.y+OFFSET_Y, pad.width, pad.height)