import wx
import wx.grid as gridlib
from EDXD.globals import ICON_PATH

def get_theme(theme: str = "dark"):
    # Data for theme_handler
    if theme == "dark":
        return get_dark_theme()
    else:
        return get_dark_theme()

def get_dark_theme():
    ed_dark_theme = dict(
        background          = wx.Colour("#121212"),
        background_hover    = wx.Colour("#433322"),
        foreground          = wx.Colour("#ff9a00"),
        foreground_accent   = wx.Colour("#ff9a33"),
        border              = wx.Colour("#aa7700"),
        font                = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
        font_bold           = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
        color_debug         = wx.Colour("#00ff00")
    )
    return ed_dark_theme

def apply_theme(widget):
    if widget.ClassName == "wxFrame":
        apply_theme_to_frame(widget)
    elif widget.ClassName == "wxPanel":
        apply_theme_to_panel(widget)
    elif widget.ClassName == "wxStaticText":
        apply_theme_to_static_text(widget)
    elif widget.ClassName == "wxButton":
        apply_theme_to_button(widget)
    elif widget.ClassName == "wxGrid":
        apply_theme_to_grid(widget)
    else:
        return

def apply_theme_to_frame(widget: wx.Frame):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetIcon(wx.Icon(ICON_PATH.as_posix(), wx.BITMAP_TYPE_ICO))

def apply_theme_to_panel(widget: wx.Panel):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font_bold"])

def apply_theme_to_button(widget: wx.Button):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])
    widget.style = wx.BORDER_NONE

def apply_theme_to_static_text(widget: wx.StaticText):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

def apply_theme_to_grid(widget: gridlib.Grid):
    theme = get_theme()
    widget.DefaultCellBackgroundColour = theme["background"]
    widget.DefaultCellTextColour = theme["foreground"]
    widget.LabelTextColour = theme["foreground"]
    widget.SetFont(theme["font"])
    widget.SelectionBackground = theme["background_hover"]
    widget.SelectionForeground = theme["foreground_accent"]
    widget.CellHighlightPenWidth = 0



