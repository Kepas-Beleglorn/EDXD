import wx
import wx.lib.buttons as buttons

from EDXD.globals import logging, DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y
from EDXD.gui.helper.theme_handler import apply_theme

logger = logging.getLogger(__name__)


def init_widget(widget, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, posx: int = DEFAULT_POS_X, posy: int = DEFAULT_POS_Y, title: str = "", is_ctrl_box: bool = False):
    apply_theme(widget=widget)
    if widget.Name == "frame":
        init_frame(widget=widget, width=width, height=height, posx=posx, posy=posy, title=title)
    elif widget.Name == "dialog":
        init_dialog(widget=widget, width=width, height=height, posx=posx, posy=posy, title=title)
    elif widget.Name == "panel":
        init_panel(widget=widget, title=title)
    elif widget.Name == "staticText":
        init_static_text(widget=widget, title=title)
    elif widget.Name in ["text"]:
        init_text(widget=widget, title=title)
    elif widget.Name == "genbutton":
        if is_ctrl_box:
            init_gen_button_ctrl_box(widget=widget, title=title)
        else:
            init_gen_button(widget=widget, title=title)
    else:
        logger.debug("Unknown widget type: %s - %s", widget.Name, widget)
        return


def init_frame(widget: wx.Frame, width: int, height: int, posx: int, posy: int, title: str):
    widget.SetSize(wx.Size(width=width, height=height))
    widget.SetPosition(wx.Point(x=posx, y=posy))
    widget.SetTitle(title)

def init_dialog(widget: wx.Dialog, width: int, height: int, posx: int, posy: int, title: str):
    widget.SetSize(wx.Size(width=width, height=height))
    widget.SetPosition(wx.Point(x=posx, y=posy))
    widget.SetTitle(title)

def init_panel(widget: wx.Panel,title: str):
    # widget.SetSize(width, height)
    pass

def init_static_text(widget: wx.StaticText, title: str):
    widget.SetLabelText(title)

def init_text(widget: wx.StaticText, title: str):
    #widget.SetLabelText(title)
    pass

def init_gen_button(widget: buttons.GenButton, title: str):
    widget.SetLabelText(title)
    widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))

def init_gen_button_ctrl_box(widget: buttons.GenButton, title: str):
    widget.SetLabelText(title)
    widget.SetCursor(wx.Cursor(wx.CURSOR_HAND))