import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicToggleButton(buttons.GenToggleButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0):
        super().__init__(parent=parent, style=style, label=label, size=size )
        self.SetName("togglebutton")
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
        )
        #self.Bind(wx.EVT_BUTTON, self.on_toggle)

    """ def on_toggle(self, evt):
            self.Refresh()
            evt.Skip()
    """
    """def DrawBezel(self, dc, x1, y1, x2, y2):
        theme = get_theme()
        color_bg_toggled = self._themed_colors["toggled_bg"]
        color_bg_hovered = self._themed_colors["hover_bg"]
        color_bg_normal = self._themed_colors["normal_bg"]
        color_btn_border_light = self._themed_colors["border_button_light"]
        color_btn_border_dark = self._themed_colors["border_button_dark"]
        btn_border_width = theme["button_border_width"]

        #Custom painted background for both toggled and untoggled states.
        if self.Name == "genbutton" and self.GetValue():
            bg = color_bg_toggled
        elif getattr(self, "_is_hovered", False):
            bg = color_bg_hovered
        else:
            bg = color_bg_normal

        # Fill button area with custom color
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg))
        dc.DrawRectangle(x1, y1, x2 - x1, y2 - y1)
        self.hasFocus = False


        # Optionally, draw a border or focus indicator here

        # 3D effect: light on top/left, dark on bottom/right
        light = color_btn_border_light
        dark = color_btn_border_dark

        #brush_light = wx.Brush(light)
        #brush_dark = wx.Brush(dark)
        pen_light = wx.Pen(colour=light, width=btn_border_width)
        pen_dark = wx.Pen(colour=dark, width=btn_border_width)
        # Top edge
        #dc.SetBrush(brush_light)
        dc.SetPen(pen_light)
        dc.DrawLine(x1, y1, x2, y1)
        # Left edge
        dc.DrawLine(x1, y1, x1, y2)

        # Bottom edge
        #dc.SetBrush(brush_dark)
        dc.SetPen(pen_dark)
        dc.DrawLine(x1, y2, x2, y2)
        # Right edge
        dc.DrawLine(x2, y1, x2, y2)

        # Label will be drawn by the default paint event"""