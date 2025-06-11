"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict
from .helper.theme_handler import apply_theme
from .helper.window_titlebar_handler import CustomTitlebar
from .helper.window_properties import WindowProperties

TITLE = "Minerals to show"
WINID = "MINERALS_FILTER"

from ..gobal_constants import RAW_MATS

# ---------------------------------------------------------------------------
class ConfigPanel(tk.Toplevel):
    """
    Dark-theme filter window.
    * Landable checkbox lives in MainWindow.
    * Presents 27 mineral check-boxes in a 4-column grid + (De)select-all + Apply.
    """

    def __init__(self, master, prefs: Dict, on_apply):
        super().__init__(master)
        apply_theme(self)

        self.title(TITLE)
        self.resizable(False, False)
        # Load properties for this window (with defaults if not saved before)
        self.props = WindowProperties.load(WINID, default_height=330, default_width=450, default_posx=master.props.posx, default_posy=master.props.posy)
        self.geometry(f"{self.props.width}x{self.props.height}+{self.props.posx}+{self.props.posy}")
        self._ready = False  # not yet mapped
        self._loading = True  # during startup we must not save, otherwise we'll get garbage!!
        self.bind("<Map>", self.on_mapped)  # mapped == now visible
        self.bind("<Configure>", self.on_configure)  # move / resize
        self.attributes("-topmost", True)

        # In your window constructor:
        self.titlebar = CustomTitlebar(self, title=TITLE)
        self.titlebar.pack(fill="x")

        self.grab_set()                     # modal

        self._prefs = prefs
        self._on_apply = on_apply

        self._build_widgets()

        self.after(3000, self.loading_finished)

    def loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def _build_widgets(self):
        frame = ttk.Frame(self, style="Dark.TFrame")
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- mineral check-boxes ------------------------------------
        self.var_mat: Dict[str, tk.BooleanVar] = {}
        cols = 4
        rows = int(round(len(RAW_MATS) / 4 ,0))
        for idx, mat in enumerate(RAW_MATS):
            var = tk.BooleanVar(value=self._prefs["mat_sel"].get(mat, True))
            self.var_mat[mat] = var
            cb = ttk.Checkbutton(frame, text=mat.title(), variable=var)
            c, r = divmod(idx, rows)
            cb.grid(row=r, column=c, sticky="w", padx=4, pady=2)

        # ---- (De)select-all & Apply buttons --------------------------
        btns = ttk.Frame(self, style="Dark.TFrame")
        btns.pack(pady=(4, 8))

        def toggle_all():
            new = not all(v.get() for v in self.var_mat.values())
            for v in self.var_mat.values():
                v.set(new)

        ttk.Button(btns, text="(De)select all", style="Dark.TButton",
                   command=toggle_all).pack(fill="x", pady=(0, 4))

        ttk.Button(btns, text="Apply", style="Dark.TButton",
                   command=self._apply).pack(fill="x")

    # ------------------------------------------------------------------
    def _apply(self):
        # persist selections → prefs dict
        self._prefs["mat_sel"] = {m: v.get() for m, v in self.var_mat.items()}
        self._prefs["save"]()           # write config.json

        # notify main window & close
        if self._on_apply:
            self._on_apply()
        self.destroy()

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
