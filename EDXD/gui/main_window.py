"""
main_window.py – root Tk window that wires all GUI pieces together
=================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict

from EDXD.model import Model, Body
from EDXD.gui.table_view     import BodiesTable
from EDXD.gui.set_mineral_filter   import ConfigPanel
from EDXD.gui.detail_selected import DetailSelected
from EDXD.gui.detail_target   import DetailTarget
from EDXD.gui.helper.theme_handler import apply_theme
from EDXD.gui.helper.window_titlebar_handler import CustomTitlebar
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "ED eXploration Dashboard"
WINID = "EDXD_MAIN_WINDOW"

class MainWindow(tk.Tk):
    """Composes toolbar  +  table  +  two detail windows."""

    def __init__(self, model: Model, prefs: Dict):
        super().__init__()
        self.model  = model
        self.prefs  = prefs

        self.title(TITLE)
        # Load properties for this window (with defaults if not saved before)
        self.props = WindowProperties.load(WINID, default_height=1000, default_width=1200)
        self.geometry(f"{self.props.width}x{self.props.height}+{self.props.posx}+{self.props.posy}")
        self._ready = False  # not yet mapped
        self._loading = True # during startup we must not save, otherwise we'll get garbage!!
        self.bind("<Map>", self.on_mapped)  # mapped == now visible
        self.bind("<Configure>", self.on_configure)  # move / resize
        self.attributes("-topmost", True)

        # In your window constructor:
        self.titlebar = CustomTitlebar(self, title=TITLE)
        self.titlebar.pack(fill="x")

        apply_theme(self)

        self._build_widgets()
        self.after(500, self._refresh)
        self.var_land.set(self.prefs["land"])
        self._selected = None          # currently clicked body name

        # listen for target changes
        self.model.register_target_listener(self._update_target)

        self.after(3000, self.loading_finished)

    def loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def _build_widgets(self):

        # ── toolbar ───────────────────────────────────────────────

        bar = ttk.Frame(self)

        bar.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(bar, text="Filters", command=self._open_filters).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="Reload cache", command=self._reload).pack(side=tk.LEFT, padx=2)
        self.var_land = tk.BooleanVar(value=self.prefs["land"])
        ttk.Checkbutton(bar, text="Landable", variable=self.var_land, command=self._toggle_land).pack(side=tk.LEFT, padx=8)

        # system name + body counts
        self.lbl_sys = ttk.Label(self, font=("Segoe UI", 10, "bold"))
        self.lbl_sys.pack(anchor="w", padx=4, pady=(0, 4))

        # ── table ────────────────────────────────────────────────
        self.table = BodiesTable(self, on_select=self._row_clicked)
        self.table.bind("<<EdmSortRequest>>", lambda e: self._refresh())
        self.table.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # ── detail windows ───────────────────────────────────────
        self.win_sel  = DetailSelected(self)
        self.win_auto = DetailTarget(self)

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------
    def _open_filters(self):
        # open modal config window
        ConfigPanel(self, self.prefs, on_apply=self._refresh)

    def _reload(self):
        # GUI-only refresh; real cache reload is handled by Model/Controller
        self._refresh()

    def _toggle_land(self):
        self.prefs["land"] = self.var_land.get()
        self.prefs["save"]()
        self._refresh()

    def _row_clicked(self, body_name: str):
        self._selected = body_name
        body = self.model.snapshot_bodies().get(body_name)
        if body:
            self.win_sel.render(body, self.prefs["mat_sel"])


    def _update_target(self, body_name: str):
        """Called by Model when the cockpit target changes."""
        bodies = self.model.snapshot_bodies()
        body   = bodies.get(body_name)

        if body is None:
            # target not scanned yet – show name, empty materials
            # from model import Body          # avoid circular import at top
            body = Body(body_name, False, {})

        self.win_auto.render(body, self.prefs["mat_sel"])

        # trigger a table refresh so the status icon updates immediately
        self._refresh()
        
    # ------------------------------------------------------------------
    # periodic refresh
    # ------------------------------------------------------------------
    def _refresh(self):
        self.table.refresh(
            bodies        = self.model.snapshot_bodies(),
            filters       = self.prefs["mat_sel"],
            landable_only = self.prefs["land"],
            selected_name = self._selected,
            target_name   = self.model.target_body
        )

        # keep the auto-window live even if nothing else changes
        tgt = self.model.snapshot_target()
        if tgt:
            self.win_auto.render(tgt, self.prefs["mat_sel"])

                # ---- system label (belts excluded from *scanned* only) -------
        bodies  = self.model.snapshot_bodies()

        scanned = sum(1 for b in bodies.values()
                      if "Belt Cluster" not in b.name)

        total = self.model.snapshot_total() or "?"   # raw DSS BodyCount

        name = self.model.system_name or "No system"
        self.lbl_sys.config(text=f"{name}   ({scanned}/{total})")

        self.after(1_000, self._refresh)     # schedule next update

    # --------------------------------------------------------------
    def on_mapped(self, _):
        """First time the window becomes visible."""
        self._ready = True

    def on_configure(self, event):  # move/resize
        if self._ready and not self._loading:
            self.props.height = event.height
            self.props.width = event.width
            self.props.posx = event.x
            self.props.posy = event.y
            self.props.save()
