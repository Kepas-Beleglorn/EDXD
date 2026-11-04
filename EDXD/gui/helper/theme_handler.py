import wx
import wx.grid as gridlib
import wx.lib.buttons as buttons

from EDXD.globals import logging
from EDXD.gui.helper.themed_slider import ThemedSlider



logger = logging.getLogger(__name__)
# from EDXD.globals import ICON_PATH

def get_theme(theme: str = "dark"):
    # Data for theme_handler
    if theme == "dark":
        return _get_dark_theme()
    else:
        return _get_dark_theme()

def _get_dark_theme():
    ed_dark_theme = dict(
        background              = wx.Colour("#121212"),
        background_hover        = wx.Colour("#433322"),
        background_click        = wx.Colour("#663322"),
        background_toggled      = wx.Colour("#553322"),
        foreground              = wx.Colour("#ff9a00"),
        foreground_less         = wx.Colour("#ff9a0088"),
        foreground_accent       = wx.Colour("#ff9a33"),
        foreground_hover        = wx.Colour("#ff9a33"),
        foreground_click        = wx.Colour("#ffbb55"),
        foreground_toggled      = wx.Colour("#ffaa44"),
        border                  = wx.Colour("#aa4400"),
        border_button_light     = wx.Colour("#bb550088"),
        border_button_dark      = wx.Colour("#88330088"),
        grid_label_background   = wx.Colour("#292c30"),
        grid_line_color         = wx.Colour("#292c30"),
        grid_frozen_border_color= wx.Colour("#bb550088"),
        border_thickness        = 1,
        button_border_width     = 3,
        button_border_margin    = 1,
        font                    = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
        font_bold               = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
        color_debug             = wx.Colour("#00ff00")
    )
    return ed_dark_theme

def apply_theme(widget):
    # Name-based matching (explicit names set by init_widget or Dynamic* classes)
    if widget.Name == "frame":
        _apply_theme_to_frame(widget)
    elif widget.Name == "dialog":
        _apply_theme_to_dialog(widget)
    elif widget.Name == "panel":
        _apply_theme_to_panel(widget)
    elif widget.Name == "staticText":
        _apply_theme_to_static_text(widget)
    elif widget.Name == "text":
        _apply_theme_to_text(widget)
    elif widget.Name in ("genbutton", "pushbutton", "togglebutton"):
        _apply_theme_to_button(widget)
    elif widget.Name == "gauge":
        _apply_theme_to_gauge(widget)
    elif widget.Name == "grid":
        _apply_theme_to_grid(widget)
    elif widget.Name == "dirpickerctrl":
        _apply_theme_to_dirpickerctrl(widget)
    elif widget.Name == "comboBox":
        _apply_theme_to_combobox(widget)
    elif widget.Name == "wxSpinCtrl":
        _apply_theme_to_spin(widget)
    elif widget.Name == "themed_slider":
        _apply_theme_to_slider(widget)
    # Fallback: type-based matching for widgets created without an explicit name
    elif isinstance(widget, wx.StaticText):
        _apply_theme_to_static_text(widget)
    elif isinstance(widget, wx.TextCtrl):
        _apply_theme_to_text(widget)
    elif isinstance(widget, wx.ComboBox):
        _apply_theme_to_combobox(widget)
    elif isinstance(widget, wx.DirPickerCtrl):
        _apply_theme_to_dirpickerctrl(widget)
    elif isinstance(widget, wx.SpinCtrl):
        _apply_theme_to_spin(widget)
    elif isinstance(widget, wx.grid.Grid):
        _apply_theme_to_grid(widget)
    elif isinstance(widget, (buttons.GenButton, buttons.GenBitmapButton)):
        _apply_theme_to_button(widget)
    else:
        return

def _apply_theme_to_frame(widget: wx.Frame):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    #widget.SetIcon(wx.Icon(ICON_PATH.as_posix(), wx.BITMAP_TYPE_ICO))
    # Recursively theme all child widgets
    _apply_theme_to_children(widget)

def _apply_theme_to_dialog(widget: wx.Dialog):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    #widget.SetIcon(wx.Icon(ICON_PATH.as_posix(), wx.BITMAP_TYPE_ICO))
    # Recursively theme all child widgets
    _apply_theme_to_children(widget)

def _apply_theme_to_panel(widget: wx.Panel, theme_children: bool = True):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    if theme_children:
        # Recursively theme all child widgets
        _apply_theme_to_children(widget)

def _apply_theme_to_children(parent):
    """Recursively apply theme to all child widgets of a parent."""
    for child in parent.GetChildren():
        apply_theme(child)
        # Recurse into containers that may have their own children
        if isinstance(child, (wx.Panel, wx.Window)):
            _apply_theme_to_children(child)

def _apply_theme_to_gauge(widget: wx.Gauge):
    pass
    #theme = get_theme()
    #widget.SetBackgroundColour(theme["background"])
    #widget.SetForegroundColour(theme["foreground"])
    #widget.SetFont(theme["font_bold"])

def _apply_theme_to_button(widget: buttons.GenButton):
    theme = get_theme()
    #widget.SetBackgroundColour(theme["background"])
    #widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])
    widget.style = wx.BORDER_NONE

def _apply_theme_to_static_text(widget: wx.StaticText):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

def _apply_theme_to_text(widget: wx.TextCtrl):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])

    widget.SetFont(theme["font"])

def _apply_theme_to_grid(widget: gridlib.Grid):
    theme = get_theme()
    widget.DefaultCellBackgroundColour = theme["background"]
    widget.DefaultCellTextColour = theme["foreground"]
    widget.LabelTextColour = theme["foreground"]
    widget.SetFont(theme["font"])
    widget.SelectionBackground = theme["background_hover"]
    widget.SelectionForeground = theme["foreground_accent"]
    widget.SetLabelBackgroundColour(theme["grid_label_background"])
    widget.SetGridLineColour(theme["grid_line_color"])
    widget.CellHighlightPenWidth = 0
    widget.SetGridFrozenBorderColour(theme["border_button_dark"])


def _apply_theme_to_dirpickerctrl(widget: wx.DirPickerCtrl):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.TextCtrl.SetBackgroundColour(theme["background"])
    widget.TextCtrl.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

def _apply_theme_to_combobox(widget: wx.ComboBox):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

def _apply_theme_to_spin(widget: wx.SpinCtrl):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

def _apply_theme_to_slider(widget: ThemedSlider):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font"])

    widget.SetAccentColour(theme["foreground"])
    widget.SetGrooveColour(theme["background"])
    widget.SetHandleBgColour(theme["background_hover"])
