from __future__ import annotations

import wx
from typing import Dict

from EDXD.model import Model, Body
from EDXD.gui.custom_title_bar import CustomTitleBar
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.table_view import BodiesTable
from EDXD.gui.helper.window_properties import WindowProperties

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


TITLE = "ED eXploration Dashboard"
WINID = "EDXD_MAIN_WINDOW"

class MainFrame(wx.Frame):
    @log_call()
    def __init__(self, model: Model, prefs: Dict):
        super().__init__(parent=None, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP)
        init_widget(self, width=1000, height=500, title=TITLE)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Define the handler as a method
        def on_body_selected(body_name: str) -> None:
            self._row_clicked(body_name)
            # You can update other parts of the UI here

        self.model = model
        self.prefs = prefs

        # customized titlebar
        self.titlebar = CustomTitleBar(parent=self, title=TITLE)

        # VBox sizer for titlebar + content
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.titlebar, 0, wx.EXPAND)

        # In your main frame:
        self.table_view = BodiesTable(self, on_select=on_body_selected)
        init_widget(self.table_view)
        vbox.Add(self.table_view, 1, wx.EXPAND)

        self.SetSizer(vbox)

        # noinspection PyTypeChecker
        #logging.info(f"init before first refresh: {self.table_view}")
        wx.CallLater(millis=500, callableObj=self._refresh)
        #self.var_land.set(self.prefs["land"])
        self._selected = None  # currently clicked body name
        #logging.info(f"init after first refresh: {self.table_view}")

        # listen for target changes
        self.model.register_target_listener(self._update_target)

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------
    def _open_filters(self):
        # open modal config window
        # ConfigPanel(self, self.prefs, on_apply=self._refresh)
        pass

    def _reload(self):
        # GUI-only refresh; real cache reload is handled by Model/Controller
        self._refresh()

    def _toggle_land(self):
        #self.prefs["land"] = self.var_land.get()
        #self.prefs["save"]()
        #self._refresh()
        pass

    def _row_clicked(self, body_name: str):
        self._selected = body_name
        body = self.model.snapshot_bodies().get(body_name)
        if body:
            #self.win_sel.render(body, self.prefs["mat_sel"])
            logging.info(f"Selected body: {body_name}")

    def _update_target(self, body_name: str):
        """Called by Model when the cockpit target changes."""
        bodies = self.model.snapshot_bodies()
        body = bodies.get(body_name)

        if body is None:
            # target not scanned yet – show name, empty materials
            # from model import Body          # avoid circular import at top
            body = Body(name=body_name, landable=False, materials={})

        #self.win_auto.render(body, self.prefs["mat_sel"])
        logging.info(f"Targeted body: {body_name}")

        # trigger a table refresh so the status icon updates immediately
        self._refresh()

    # ------------------------------------------------------------------
    # periodic refresh
    # ------------------------------------------------------------------
    #@log_call()
    def _refresh(self):
        self.table_view.refresh(
            bodies=self.model.snapshot_bodies(),
            filters=self.prefs["mat_sel"],
            landable_only=self.prefs["land"],
            selected_name=self._selected,
            target_name=self.model.target_body
        )
        #logging.info(f"Refreshed: {self.model.target_body}")
        # keep the auto-window live even if nothing else changes
        tgt = self.model.snapshot_target()
        if tgt:
            #self.win_auto.render(tgt, self.prefs["mat_sel"])
            logging.info(f"Current target: {tgt}")
            # ---- system label (belts excluded from *scanned* only) -------
        bodies = self.model.snapshot_bodies()

        scanned = sum(1 for b in bodies.values()
                      if "Belt Cluster" not in b.name)

        total = self.model.snapshot_total() or "?"  # raw DSS BodyCount

        name = self.model.system_name or "No system"
        #self.lbl_sys.config(text=f"{name}   ({scanned}/{total})")

        # noinspection PyTypeChecker
        wx.CallLater(millis=1000, callableObj=self._refresh)  # schedule next update

    def on_close(self, event):
        # Save geometry
        x, y = self.GetPosition()
        w, h = self.GetSize()
        props = WindowProperties(window_id=WINID, height=h, width=w, posx=x, posy=y)
        props.save()
        # Now close all child windows as needed!
        # for win in self.child_windows:
        #     win.Destroy()
        event.Skip()  # Let wx close the window

