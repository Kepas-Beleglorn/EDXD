import wx
from typing import Protocol

class DynamicControlsBaseHint(Protocol):
    def SetBackgroundColour(self, colour): ...
    def SetForegroundColour(self, colour): ...
    def Refresh(self): ...
    def Bind(self, event, handler): ...
    def _on_enter(self, event): ...
    def _on_leave(self, event): ...
    def _on_press(self, event): ...
    def _on_release(self, event): ...
    _is_pressed: ...
    _is_released: ...
    _is_hovered: ...
    _hover_colors: ...

class DynamicControlsBase:
    def __init__(
            self,
            normal_bg,
            hover_bg,
            pressed_bg,
            normal_fg,
            hover_fg,
            pressed_fg,
            *args,
            **kwargs
    ):
        self._init_dynamic_controls(
            normal_bg,
            hover_bg,
            pressed_bg,
            normal_fg,
            hover_fg,
            pressed_fg,
            *args,
            **kwargs
        )

    def _init_dynamic_controls(
            self: "DynamicControlsBaseHint",
            normal_bg,
            hover_bg,
            pressed_bg,
            normal_fg,
            hover_fg,
            pressed_fg,
            *args,
            **kwargs):

        self._hover_colors = {
            "normal_bg": normal_bg,
            "hover_bg": hover_bg,
            "pressed_bg": pressed_bg,
            "normal_fg": normal_fg,
            "hover_fg": hover_fg,
            "pressed_fg": pressed_fg,
        }
        self._is_hovered = False
        self._is_pressed = False

        self.SetBackgroundColour(normal_bg)
        self.SetForegroundColour(normal_fg)

        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_press)
        self.Bind(wx.EVT_LEFT_UP, self._on_release)

    def _on_enter(self: "DynamicControlsBaseHint", event):
        self._is_hovered = True
        if self._is_pressed:
            self.SetBackgroundColour(self._hover_colors["pressed_bg"])
            self.SetForegroundColour(self._hover_colors["pressed_fg"])
        else:
            self.SetBackgroundColour(self._hover_colors["hover_bg"])
            self.SetForegroundColour(self._hover_colors["hover_fg"])
        self.Refresh()
        event.Skip()

    def _on_leave(self: "DynamicControlsBaseHint", event):
        self._is_hovered = False
        self._is_pressed = False
        self.SetBackgroundColour(self._hover_colors["normal_bg"])
        self.SetForegroundColour(self._hover_colors["normal_fg"])
        self.Refresh()
        event.Skip()

    def _on_press(self: "DynamicControlsBaseHint", event):
        self._is_pressed = True
        self.SetBackgroundColour(self._hover_colors["pressed_bg"])
        self.SetForegroundColour(self._hover_colors["pressed_fg"])
        self.Refresh()
        event.Skip()

    def _on_release(self: "DynamicControlsBaseHint", event):
        self._is_pressed = False
        if self._is_hovered:
            self.SetBackgroundColour(self._hover_colors["hover_bg"])
            self.SetForegroundColour(self._hover_colors["hover_fg"])
        else:
            self.SetBackgroundColour(self._hover_colors["normal_bg"])
            self.SetForegroundColour(self._hover_colors["normal_fg"])
        self.Refresh()
        event.Skip()