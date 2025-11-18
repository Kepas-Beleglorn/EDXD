import wx
import wx.grid as gridlib
import wx.lib.buttons as buttons

#from EDXD.globals import ICON_PATH

from EDXD.globals import logging
import inspect, functools

def log_call(level=logging.INFO):
    """Decorator that logs function name and bound arguments."""
    def decorator(fn):
        logger = logging.getLogger(fn.__module__)   # one logger per module
        sig = inspect.signature(fn)                 # capture once, not on every call

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arg_str = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            logger.log(level, "%s(%s)", fn.__name__, arg_str)
            return fn(*args, **kwargs)

        return wrapper
    return decorator

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
        foreground_accent       = wx.Colour("#ff9a33"),
        foreground_hover        = wx.Colour("#ff9a33"),
        foreground_click        = wx.Colour("#ffbb55"),
        foreground_toggled      = wx.Colour("#ffaa44"),
        border                  = wx.Colour("#aa4400"),
        border_button_light     = wx.Colour("#bb550088"),
        border_button_dark      = wx.Colour("#88330088"),
        grid_label_background   = wx.Colour("#292c30"),
        grid_line_color         = wx.Colour("#292c30"),
        border_thickness        = 1,
        button_border_width     = 3,
        button_border_margin    = 1,
        font                    = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
        font_bold               = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
        color_debug             = wx.Colour("#00ff00")
    )
    return ed_dark_theme

def apply_theme(widget):
    #logging.info(f"Applying theme... {widget.Name}")
    if widget.Name == "frame":
        _apply_theme_to_frame(widget)
    if widget.Name == "dialog":
        _apply_theme_to_dialog(widget)
    elif widget.Name == "panel":
        _apply_theme_to_panel(widget)
    elif widget.Name == "staticText":
        _apply_theme_to_static_text(widget)
    elif widget.Name == "text":
        _apply_theme_to_text(widget)
    elif widget.Name == "genbutton":
        _apply_theme_to_button(widget)
    elif widget.Name == "gauge":
        _apply_theme_to_gauge(widget)
    elif widget.Name == "grid":
        _apply_theme_to_grid(widget)
    else:
        return

def _apply_theme_to_frame(widget: wx.Frame):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    #widget.SetIcon(wx.Icon(ICON_PATH.as_posix(), wx.BITMAP_TYPE_ICO))

def _apply_theme_to_dialog(widget: wx.Dialog):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    #widget.SetIcon(wx.Icon(ICON_PATH.as_posix(), wx.BITMAP_TYPE_ICO))

def _apply_theme_to_panel(widget: wx.Panel):
    theme = get_theme()
    widget.SetBackgroundColour(theme["background"])
    widget.SetForegroundColour(theme["foreground"])
    widget.SetFont(theme["font_bold"])

def _apply_theme_to_gauge(widget: wx.Gauge):
    theme = get_theme()
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



