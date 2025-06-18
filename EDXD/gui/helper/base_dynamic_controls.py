import wx
from EDXD.gui.helper.theme_handler import get_theme
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
    _themed_colors: ...

class DynamicControlsBase:
    def __init__(
            self,
            normal_bg           = None,
            hover_bg            = None,
            pressed_bg          = None,
            toggled_bg          = None,
            normal_fg           = None,
            accent_fg           = None,
            hover_fg            = None,
            pressed_fg          = None,
            toggled_fg          = None,
            border              = None,
            border_button_light = None,
            border_button_dark  = None,
            debug_color         = None,
            *args,
            **kwargs
    ):
        theme = get_theme()
        self._init_dynamic_controls(
            normal_bg           = normal_bg             or theme["background"],
            hover_bg            = hover_bg              or theme["background_hover"],
            pressed_bg          = pressed_bg            or theme["background_click"],
            toggled_bg          = toggled_bg            or theme["background_toggled"],
            normal_fg           = normal_fg             or theme["foreground"],
            accent_fg           = accent_fg             or theme["foreground_accent"],
            hover_fg            = hover_fg              or theme["foreground_hover"],
            pressed_fg          = pressed_fg            or theme["foreground_click"],
            toggled_fg          = toggled_fg            or theme["foreground_toggled"],
            border              = border                or theme["border_button_light"],
            border_button_light = border_button_light   or theme["border_button_light"],
            border_button_dark  = border_button_dark    or theme["border_button_dark"],
            debug_color         = debug_color           or theme["color_debug"],
            *args,
            **kwargs
        )

    def _init_dynamic_controls(
            self: "DynamicControlsBaseHint",
            normal_bg,
            hover_bg,
            pressed_bg,
            toggled_bg,
            normal_fg,
            hover_fg,
            accent_fg,
            pressed_fg,
            toggled_fg,
            border,
            border_button_light,
            border_button_dark,
            debug_color,
            *args,
            **kwargs):

        self._themed_colors = {
            "normal_bg":            normal_bg,
            "hover_bg":             hover_bg,
            "pressed_bg":           pressed_bg,
            "toggled_bg":           toggled_bg,
            "normal_fg":            normal_fg,
            "accent_fg":            accent_fg,
            "hover_fg":             hover_fg,
            "pressed_fg":           pressed_fg,
            "toggled_fg":           toggled_fg,
            "border":               border,
            "border_button_light":  border_button_light,
            "border_button_dark":   border_button_dark,
            "debug_color":          debug_color
        }
        self._is_hovered = False
        self._is_pressed = False

        self.SetBackgroundColour(normal_bg)
        self.SetForegroundColour(normal_fg)

        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_press)
        self.Bind(wx.EVT_LEFT_UP, self._on_release)

        if self.GetName() == "togglebutton":
            print("bind toggle button")
            self.Bind(wx.EVT_BUTTON, self._on_toggle)

    def _on_toggle(self, evt):
        print("event toggle")
        self.Refresh()
        evt.Skip()

    def _on_enter(self: "DynamicControlsBaseHint", event):
        self._is_hovered = True
        if self._is_pressed:
            self.SetBackgroundColour(self._themed_colors["pressed_bg"])
            self.SetForegroundColour(self._themed_colors["pressed_fg"])
        else:
            self.SetBackgroundColour(self._themed_colors["hover_bg"])
            self.SetForegroundColour(self._themed_colors["hover_fg"])
        self.Refresh()
        event.Skip()

    def _on_leave(self: "DynamicControlsBaseHint", event):
        self._is_hovered = False
        self._is_pressed = False
        self.SetBackgroundColour(self._themed_colors["normal_bg"])
        self.SetForegroundColour(self._themed_colors["normal_fg"])
        self.Refresh()
        event.Skip()

    def _on_press(self: "DynamicControlsBaseHint", event):
        self._is_pressed = True
        self.SetBackgroundColour(self._themed_colors["pressed_bg"])
        self.SetForegroundColour(self._themed_colors["pressed_fg"])
        self.Refresh()
        event.Skip()

    def _on_release(self: "DynamicControlsBaseHint", event):
        self._is_pressed = False
        if self._is_hovered:
            self.SetBackgroundColour(self._themed_colors["hover_bg"])
            self.SetForegroundColour(self._themed_colors["hover_fg"])
        else:
            self.SetBackgroundColour(self._themed_colors["normal_bg"])
            self.SetForegroundColour(self._themed_colors["normal_fg"])
        self.Refresh()
        event.Skip()

    def DrawBezel(self, dc, x1, y1, x2, y2):
        theme = get_theme()
        color_bg_toggled = self._themed_colors["toggled_bg"]
        color_bg_hovered = self._themed_colors["hover_bg"]
        color_bg_normal = self._themed_colors["normal_bg"]
        color_btn_border_light = self._themed_colors["border_button_light"]
        color_btn_border_dark = self._themed_colors["border_button_dark"]
        btn_border_width = theme["button_border_width"]

        """Custom painted background for both toggled and untoggled states."""
        if  self.GetName() == "togglebutton" and self.GetValue():
            bg = color_bg_toggled
        elif getattr(self, "_is_hovered", False):
            bg = color_bg_hovered
        else:
            bg = color_bg_normal

        # Fill button area with custom color
        dc.SetBrush(wx.Brush(bg))
        dc.SetPen(wx.Pen(bg))
        dc.DrawRectangle(x1, y1, x2 - x1, y2 - y1)
        self.hasFocus = False


        # Optionally, draw a border or focus indicator here

        # 3D effect: light on top/left, dark on bottom/right
        light = color_btn_border_light
        dark = color_btn_border_dark

        #brush_light = wx.Brush(light)
        #brush_dark = wx.Brush(dark)
        pen_light = wx.Pen(colour=light, width=btn_border_width)
        pen_dark = wx.Pen(colour=dark, width=btn_border_width)
        # Top edge
        #dc.SetBrush(brush_light)
        dc.SetPen(pen_light)
        dc.DrawLine(x1, y1, x2, y1)
        # Left edge
        dc.DrawLine(x1, y1, x1, y2)

        # Bottom edge
        #dc.SetBrush(brush_dark)
        dc.SetPen(pen_dark)
        dc.DrawLine(x1, y2, x2, y2)
        # Right edge
        dc.DrawLine(x2, y1, x2, y2)

        # Label will be drawn by the default paint event