import wx
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y, BTN_WIDTH, BTN_HEIGHT, RESIZE_MARGIN
WINID = "RESTART_MSG_DLG"

class ThemedMessageDialog(DynamicDialog):
    def __init__(self, parent, message, caption):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH,
                                      default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=caption,
                               win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=caption)

        self.window_box.Add(wx.StaticText(self.scroll_container, label=message), 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        no_btn = DynamicButton(self.scroll_container, style=wx.ID_NO, label="No", size=(BTN_WIDTH, BTN_HEIGHT))
        no_btn.SetName("NO")
        init_widget(no_btn)
        yes_btn = DynamicButton(self.scroll_container, style=wx.ID_YES, label="Yes", size=(BTN_WIDTH, BTN_HEIGHT))
        yes_btn.SetName("YES")
        init_widget(yes_btn)
        btn_sizer.Add(no_btn, 0, wx.ALL, 5)
        btn_sizer.Add(yes_btn, 0, wx.ALL, 5)
        self.window_box.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.finalize_layout()
        self.Fit()

        self.Bind(wx.EVT_BUTTON, self.on_button, no_btn)
        self.Bind(wx.EVT_BUTTON, self.on_button, yes_btn)

        self.result = wx.ID_NO

    def on_button(self, event):
        self.result = event.theButton.GetName() == "YES"
        self.EndModal(self.result)

    def ShowModal(self):
        super().ShowModal()
        return self.result


