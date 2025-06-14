import wx

from EDXD.globals import ICON_PATH, DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y
from EDXD.gui.helper.theme_handler import apply_theme

def init_widget(widget, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,  posx: int = DEFAULT_POS_X, posy: int = DEFAULT_POS_Y, title: str = ""):
    apply_theme(widget=widget)

    if widget.ClassName == "wxFrame":
        init_frame(widget=widget, width=width, height=height, posx=posx, posy=posy, title=title)
    elif widget.ClassName == "wxPanel":
        init_panel(widget=widget, title=title)
    elif widget.ClassName == "wxStaticText":
        init_static_text(widget=widget, title=title)
    elif widget.ClassName == "wxButton":
        init_static_button(widget=widget, title=title)
    else:
        return


def init_frame(widget: wx.Frame, width: int, height: int, posx: int, posy: int, title: str):
    widget.SetSize(wx.Size(width=width, height=height))
    widget.SetPosition(wx.Point(x=posx, y=posy))
    widget.SetTitle(title)

def init_panel(widget: wx.Panel,title: str):
    # widget.SetSize(width, height)
    return

def init_static_text(widget: wx.StaticText, title: str):
    widget.SetLabelText(title)

def init_static_button(widget: wx.Button, title: str):
    widget.SetLabelText(title)
    widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))
