import wx
import wx.lib.buttons as buttons
from EDXD.gui.helper.theme_handler import get_theme

class HoverButton(buttons.GenButton):
    def __init__(self, parent, label="", size=wx.DefaultSize, style=0, normal_bg=None, hover_bg=None, pressed_bg=None, normal_fg=None, hover_fg=None, pressed_fg=None):
        super().__init__(parent, label=label, size=size, style=style)
        self.theme = get_theme()

        self.normal_bg = normal_bg or self.theme["background"]
        self.hover_bg = hover_bg or self.theme["background_hover"]
        self.pressed_bg = pressed_bg or self.theme["background_click"]
        self.normal_fg = normal_fg or self.theme["foreground"]
        self.hover_fg = hover_fg or self.theme["foreground_hover"]
        self.pressed_fg = pressed_fg or self.theme["foreground_click"]

        self.SetBackgroundColour(self.normal_bg)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_press)
        self.Bind(wx.EVT_LEFT_UP, self.on_release)
        self.is_pressed = False

    def on_enter(self, event):
        if not self.is_pressed:
            self.SetBackgroundColour(self.hover_bg)
            self.SetForegroundColour(self.normal_fg)
            self.Refresh()
        event.Skip()

    def on_leave(self, event):
        self.SetBackgroundColour(self.normal_bg)
        self.SetForegroundColour(self.normal_fg)
        self.is_pressed = False
        self.Refresh()
        event.Skip()

    def on_press(self, event):
        self.SetBackgroundColour(self.pressed_bg)
        self.SetForegroundColour(self.pressed_fg)
        self.is_pressed = True
        self.Refresh()
        event.Skip()

    def on_release(self, event):
        self.is_pressed = False
        self.SetBackgroundColour(self.hover_bg)
        self.SetForegroundColour(self.hover_fg)
        self.Refresh()
        event.Skip()
