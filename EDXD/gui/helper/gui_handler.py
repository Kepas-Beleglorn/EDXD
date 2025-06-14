import wx

from EDXD.globals import ICON_PATH, DEFAULT_HEIGHT, DEFAULT_WIDTH
from EDXD.gui.helper.theme_handler import apply_theme

def init_widget(widget, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, title: str = ""):
    apply_theme(widget=widget)

    if widget.ClassName == "wxFrame":
        init_frame(widget=widget, width=width, height=height, title=title)
    elif widget.ClassName == "wxPanel":
        init_panel(widget=widget, title=title)
    elif widget.ClassName == "wxStaticText":
        init_static_text(widget=widget, title=title)
    elif widget.ClassName == "wxButton":
        init_static_button(widget=widget, title=title)
    else:
        return


def init_frame(widget: wx.Frame, width: int, height: int, title: str):
    widget.SetSize(width, height)
    widget.SetTitle(title)

def init_panel(widget: wx.Panel,title: str):
    # widget.SetSize(width, height)
    return

def init_static_text(widget: wx.StaticText, title: str):
    widget.SetLabelText(title)

def init_static_button(widget: wx.Button, title: str):
    widget.SetLabelText(title)
    widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))
