from __future__ import annotations

import wx
from typing import Dict

from EDXD.data_handler.model import Model, Body
from EDXD.data_handler.status_json_watcher import StatusWatcher
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.journal_controller import JournalController

from EDXD.gui.helper.dynamic_frame import DynamicFrame
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.table_view import BodiesTable
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.main_window_options import MainWindowOptions
from EDXD.gui.detail_selected import DetailSelected
from EDXD.gui.detail_target import DetailTargeted
from EDXD.gui.psps_gui import PositionTracker
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN

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

class MainFrame(DynamicFrame):
    def __init__(self, model: Model, prefs: Dict, journal_reader: JournalReader, journal_controller: JournalController, status_watcher: StatusWatcher):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicFrame.__init__(self, title=TITLE, win_id=WINID, parent=None, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, show_minimize=True, show_maximize=True, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.journal_reader = journal_reader
        self.journal_controller = journal_controller
        self.status_watcher = status_watcher

        # Define the handler as a method
        def on_body_selected(body_name: str) -> None:
            self._row_clicked(body_name)
            # You can update other parts of the UI here

        self.model = model
        self.prefs = prefs
        self._refresh_timer = None

        # Add options panel (mineral filter, landable, and maybe more in the future
        self.options = MainWindowOptions(parent=self)
        self.window_box.Add(self.options, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN)

        # System name and body count
        self.lbl_sys = wx.StaticText(parent=self)
        self._update_system()
        self.window_box.Add(self.lbl_sys, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        #System table with body info
        self.table_view = BodiesTable(self, on_select=on_body_selected)
        init_widget(self.table_view)
        self.window_box.Add(self.table_view, 1, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        self.SetSizer(self.window_box)

        # noinspection PyTypeChecker
        self._refresh_timer = wx.CallLater(millis=500, callableObj=self._refresh)
        self.options.chk_landable.SetToggle(self.prefs["land"])
        self.options.chk_landable.Bind(wx.EVT_BUTTON, self._toggle_land)
        self._selected = None  # currently clicked body name

        self.win_sel = DetailSelected(self) #, self.prefs["mat_sel"])
        self.win_sel.Show(True)

        self.win_tar = DetailTargeted(self) #, self.prefs["mat_sel"])
        self.win_tar.Show(True)

        self.win_psps = PositionTracker(self)
        self.win_psps.Show(True)

        # listen for target changes
        self.model.register_target_listener(lambda name: wx.CallAfter(self._update_target, name))

    def _update_system(self, title: str = ""):
        init_widget(widget=self.lbl_sys, title=title)
        font = self.lbl_sys.GetFont()
        font.PointSize += 4
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.lbl_sys.SetFont(font)

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------
    def _reload(self):
        # GUI-only refresh; real cache reload is handled by Model/JournalController
        self._refresh()

    def _toggle_land(self, event):
        # Call the toggle button's handler so its visuals/state update
        if hasattr(self.options.chk_landable, "on_toggle"):
            self.options.chk_landable.on_toggle(event)
        self.prefs["land"] = self.options.chk_landable.GetToggle()
        self.prefs["save"]()
        self._refresh()
        pass

    def _row_clicked(self, body_id: str):
        self._selected = body_id
        self.model.selected_body_id = body_id
        body = self.model.snapshot_bodies().get(body_id)

        if body:
            current_position = self.model.snapshot_position()
            current_heading = self.model.current_heading
            self.win_sel.render(body, self.prefs["mat_sel"], current_position=current_position, current_heading=current_heading)

    def _update_target(self, body_id: str):
        """Called by Model when the cockpit target changes."""
        bodies = self.model.snapshot_bodies()
        body = bodies.get(body_id)
        current_position = self.model.snapshot_position()
        current_heading = self.model.current_heading

        if body is None:
            # target not scanned yet – show name, empty materials
            # from model import Body          # avoid circular import at top
            body = Body(body_id=body_id)

        self.win_tar.render(body=body, filters=self.prefs["mat_sel"], current_position=current_position, current_heading=current_heading)
        if self.win_sel.lbl_body.GetLabelText() == self.win_tar.lbl_body.GetLabelText():
            self.win_sel.render(body=body, filters=self.prefs["mat_sel"], current_position=current_position, current_heading=current_heading)
        self.win_psps.render(body=body, current_position=current_position, current_heading=current_heading)

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
            selected_body_id=self._selected,
            target_body_id=self.model.target_body_id
        )
        # keep the auto-window live even if nothing else changes
        current_position = self.model.snapshot_position()
        current_heading = self.model.current_heading
        tgt = self.model.snapshot_target()

        if current_position:
            self.win_psps.render(body=tgt, current_position=current_position, current_heading=current_heading)

        if tgt:
            self.win_tar.render(body=tgt, filters=self.prefs["mat_sel"],  current_position=current_position, current_heading=current_heading)
        # ---- system label (belts excluded from *scanned* only) -------

        bodies = self.model.snapshot_bodies()

        if self.model.selected_body_id is None:
            self._selected = ""

        try:
            sel_body = None
            if self._selected != "":
                sel_body = bodies[self._selected]

            self.win_sel.render(body=sel_body, filters=self.prefs["mat_sel"], current_position=current_position, current_heading=current_heading)
        except KeyError:
            pass

        scanned = sum(1 for b in bodies.values()
                      if "Belt Cluster" not in b.body_name)

        total = self.model.snapshot_total() or "?"  # raw DSS BodyCount

        name = self.model.system_name or "No system"
        self._update_system(title=f"{name}   ({scanned}/{total})")

        # noinspection PyTypeChecker
        if self._refresh_timer:
            self._refresh_timer.Stop()
        self._refresh_timer = wx.CallLater(millis=1000, callableObj=self._refresh)  # schedule next update

    def on_close(self, event):
        self.win_sel.Close(True)
        self.win_tar.Close(True)
        self.win_psps.Close(True)
        self.save_geometry()
        event.Skip()