"""
config_panel.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk
from typing import Dict, List
from gui.theme_handler import apply_theme

# ---------------------------------------------------------------------------
# master material list – imported by MainWindow and others via gui.RAW_MATS
# ---------------------------------------------------------------------------
RAW_MATS: List[str] = sorted([
    "antimony",  "arsenic",   "boron",  "cadmium",
    "carbon",    "chromium",  "germanium", "iron",
    "lead",      "manganese", "mercury", "molybdenum",
    "nickel",    "niobium",   "phosphorus", "polonium",
    "rhenium",   "ruthenium", "selenium",   "sulphur",
    "technetium","tellurium", "tin",    "tungsten",
    "vanadium",  "yttrium",   "zinc", "zirconium",
])

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

        self.title("Filters")
        self.resizable(False, False)
        self.grab_set()                     # modal

        self._prefs = prefs
        self._on_apply = on_apply

        self._build_widgets()

    # ------------------------------------------------------------------
    def _build_widgets(self):
        frame = ttk.Frame(self, style="Dark.TFrame")
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- mineral check-boxes ------------------------------------
        self.var_mat: Dict[str, tk.BooleanVar] = {}
        COLS = 4
        for idx, mat in enumerate(RAW_MATS):
            var = tk.BooleanVar(value=self._prefs["mat_sel"].get(mat, True))
            self.var_mat[mat] = var
            cb = ttk.Checkbutton(frame, text=mat.title(), variable=var)
            r, c = divmod(idx, COLS)
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
