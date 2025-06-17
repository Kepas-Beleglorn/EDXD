import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicToggleButton(buttons.GenToggleButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0):
        super().__init__(parent=parent, style=style, label=label, size=size )
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
        )

        self.Bind(wx.EVT_BUTTON, self.on_toggle)

    def on_toggle(self, evt):
        """
        if self.GetValue():
            self.SetBackgroundColour(self._themed_colors["debug_color"])
            self.SetForegroundColour(self._themed_colors["toggled_fg"])
        else:
            self.SetBackgroundColour(self._themed_colors["normal_bg"])
            self.SetForegroundColour(self._themed_colors["normal_fg"])
        """
        self.Refresh()
        evt.Skip()

    def DrawBezel(self, dc, x1, y1, x2, y2):
        """Custom painted background for both toggled and untoggled states."""
        if self.GetValue():
            bg = self._themed_colors["toggled_bg"]
        elif getattr(self, "_is_hovered", False):
            bg = self._themed_colors["hover_bg"]
        else:
            bg = self._themed_colors["normal_bg"]

        # Fill button area with custom color
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg))
        dc.DrawRectangle(x1, y1, x2 - x1, y2 - y1)

        # Optionally, draw a border or focus indicator here
