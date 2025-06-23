import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicToggleButton(buttons.GenToggleButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0, draw_border: bool = True, is_toggled: bool = False):
        super().__init__(parent=parent, style=style, label=label, size=size)
        self.SetName("togglebutton")
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
            draw_border = draw_border
        )
        self._is_toggled = is_toggled
        self.SetValue(is_toggled)
        self.Bind(wx.EVT_BUTTON, self._on_toggle)

    def _on_toggle(self, evt):
        self._is_toggled = self.GetValue()
        self.Refresh()
        evt.Skip()

    def DrawBezel(self, dc, x1, y1, x2, y2):
        if self._shall_draw_border:
            self._draw_background(dc, x1, y1, x2, y2)
        if self._shall_draw_border:
            self._draw_border(dc, x1, y1, x2, y2)
