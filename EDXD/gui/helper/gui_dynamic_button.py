import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicButton(buttons.GenButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0, draw_border: bool = True, draw_background: bool = True):
        super().__init__(parent=parent, style=style, label=label, size=size)
        self.SetName("pushbutton")
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
            draw_border = draw_border,
            draw_background=draw_background
        )

        self.Bind(wx.EVT_BUTTON, self._on_press)

    def _on_press(self, evt):
        self.Refresh()
        evt.Skip()

    def DrawBezel(self, dc, x1, y1, x2, y2):
        if self._shall_draw_border:
            self._draw_background(dc, x1, y1, x2, y2)
        if self._shall_draw_border:
            self._draw_border(dc, x1, y1, x2, y2)



