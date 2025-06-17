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

        self.Bind(wx.EVT_BUTTON, self._on_toggle)

    def _on_toggle(self, evt):
        if self.GetValue():
            self.SetBackgroundColour(self._hover_colors["toggled_bg"])
            self.SetForegroundColour(self._hover_colors["toggled_fg"])
        else:
            self.SetBackgroundColour(self._hover_colors["normal_bg"])
            self.SetForegroundColour(self._hover_colors["normal_fg"])

        self.Refresh()
        evt.Skip()