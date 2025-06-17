import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicButton(buttons.GenButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0):
        super().__init__(parent=parent, style=style, label=label, size=size)
        DynamicControlsBase.__init__(
            self    = self,
            parent  = parent
        )




