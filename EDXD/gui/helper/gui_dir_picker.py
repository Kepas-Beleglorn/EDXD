import wx
from EDXD.gui.helper.base_dynamic_controls import DynamicControlsBase
from EDXD.gui.helper.theme_handler import apply_theme


class DirPicker(wx.DirPickerCtrl, DynamicControlsBase):
    def __init__(self, parent, style=0, draw_border: bool = True, draw_background: bool = True):
        super().__init__(parent=parent, style=style)
        self.SetName("dirpickerctrl")
        DynamicControlsBase.__init__(
            self        = self,
            parent      = parent,
            draw_border = draw_border,
            draw_background=draw_background
        )
        apply_theme(self)



