import wx
import wx.lib.buttons as buttons

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y
from EDXD.gui.helper.theme_handler import apply_theme

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

#@log_call()
def init_widget(widget, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, posx: int = DEFAULT_POS_X, posy: int = DEFAULT_POS_Y, title: str = "", is_ctrl_box: bool = False):
    apply_theme(widget=widget)
    #logging.info(f"widget class name: {widget.ClassName} | widget name: {widget.Name} | pure widget: {widget}")
    if widget.Name == "frame":
        init_frame(widget=widget, width=width, height=height, posx=posx, posy=posy, title=title)
    elif widget.Name == "dialog":
        init_dialog(widget=widget, width=width, height=height, posx=posx, posy=posy, title=title)
    elif widget.Name == "panel":
        init_panel(widget=widget, title=title)
    elif widget.Name == "staticText":
        init_static_text(widget=widget, title=title)
    elif widget.Name == "text":
        init_text(widget=widget, title=title)
    elif widget.Name == "genbutton":
        if is_ctrl_box:
            init_gen_button_ctrl_box(widget=widget, title=title)
        else:
            init_gen_button(widget=widget, title=title)
    else:
        #logging.info(f"{widget.Name} - {}")
        return


def init_frame(widget: wx.Frame, width: int, height: int, posx: int, posy: int, title: str):
    if width is None or height is None or posx is None or posy is None:
        return

    widget.SetSize(wx.Size(width=width, height=height))
    widget.SetPosition(wx.Point(x=posx, y=posy))
    widget.SetTitle(title)

def init_dialog(widget: wx.Dialog, width: int, height: int, posx: int, posy: int, title: str):
    if width is None or height is None or posx is None or posy is None:
        return

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

