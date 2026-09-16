import wx
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y, BTN_WIDTH, BTN_HEIGHT, RESIZE_MARGIN
WINID = "RESTART_MSG_DLG"

class ThemedMessageDialog(DynamicDialog):
    def __init__(self, parent, message, caption, yesno: bool = True):
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
        #ToDo: Modularize message dialogues
        if yesno:
            no_btn = DynamicButton(self.scroll_container, style=wx.ID_NO, label="No", size=(BTN_WIDTH, BTN_HEIGHT))
            no_btn.SetName("NO")
            init_widget(no_btn)
            yes_btn = DynamicButton(self.scroll_container, style=wx.ID_YES, label="Yes", size=(BTN_WIDTH, BTN_HEIGHT))
            yes_btn.SetName("YES")
            init_widget(yes_btn)
            btn_sizer.Add(no_btn, 0, wx.ALL, 5)
            btn_sizer.Add(yes_btn, 0, wx.ALL, 5)

            self.Bind(wx.EVT_BUTTON, self.on_button, no_btn)
            self.Bind(wx.EVT_BUTTON, self.on_button, yes_btn)

            self.result = wx.ID_NO
        else:
            ok_btn = DynamicButton(self.scroll_container, style=wx.ID_YES, label="Ok", size=(BTN_WIDTH, BTN_HEIGHT))
            ok_btn.SetName("OK")
            init_widget(ok_btn)
            btn_sizer.Add(ok_btn, 0, wx.ALL, 5)

            self.Bind(wx.EVT_BUTTON, self.on_button, ok_btn)

            self.result = wx.ID_OK

        self.window_box.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.finalize_layout()
        self.Fit()

    def on_button(self, event):
        # Safe retrieval of button name
        btn = event.GetEventObject()
        if btn:
            match btn.GetName():
                case "YES":
                    self.result = True
                case "NO":
                    self.result = False
                case "OK":
                    self.result = wx.ID_OK
                case _:
                    self.result = wx.ID_CANCEL
        else:
            self.result = wx.ID_CANCEL

        self.EndModal(self.result)

    def ShowModal(self):
        # Ensure we don't call super on a partially constructed object
        if self.IsBeingDeleted():
            return self.result
        try:
            super().ShowModal()
        except Exception:
            pass # Ignore GTK errors during modal loop if any
        return self.result


