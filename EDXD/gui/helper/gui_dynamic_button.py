import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase

class DynamicButton(buttons.GenButton, DynamicControlsBase):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0):
        theme = get_theme()
        buttons.GenButton.__init__(self, parent=parent, label=label, size=size, style=style)
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
            normal_bg   = theme["background"],
            hover_bg    = theme["background_hover"],
            pressed_bg  = theme["background_click"],
            normal_fg   = theme["foreground"],
            hover_fg    = theme["foreground_hover"],
            pressed_fg  = theme["foreground_click"]
        )




