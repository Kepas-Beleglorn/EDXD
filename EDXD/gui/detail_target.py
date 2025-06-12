"""
detail_target.py – “In-game target” pop-out window
=================================================

A clone of DetailSelected, used exclusively for the body that the game says is
currently targeted.  MainWindow calls `render(body, filters)` whenever
Model.set_target() fires.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict
from EDXD.gui.helper.theme_handler import apply_theme, apply_text_theme
from EDXD.gui.helper.window_titlebar_handler import CustomTitlebar
from EDXD.gui.helper.window_properties import WindowProperties

from EDXD.model import Body

TITLE = "In-game target"
WINID = "DETAIL_TARGET"

class DetailTarget(tk.Toplevel):
    """Always reflects whatever the player has targeted in-game."""

    def __init__(self, master):
        super().__init__(master)
        self.title(TITLE)
        # Load properties for this window (with defaults if not saved before)
        self.props = WindowProperties.load(WINID)
        self.geometry(f"{self.props.width}x{self.props.height}+{self.props.posx}+{self.props.posy}")
        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.bind("<Map>", self.on_mapped)  # mapped == now visible
        self.bind("<Configure>", self.on_configure)  # move / resize
        self.attributes("-topmost", True)

        # In your window constructor:
        self.titlebar = CustomTitlebar(self, title=TITLE, show_close=False)
        self.titlebar.pack(fill="x")

        self.lbl = ttk.Label(self, font=("Segoe UI", 11, "bold"))
        self.lbl.pack(anchor="w", padx=6, pady=(4, 2))

        self.txt = tk.Text(self,
                           width=40,
                           height=15,
                           state="disabled",
                           font=("Segoe UI", 9))
        self.txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 6))

        # ---- dark theme colours ----
        apply_theme(self)
        apply_text_theme(self.txt)

        # noinspection PyCompatibility,PyTypeChecker
        self.after(ms=3000, func=self.loading_finished)

    def loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], filters: Dict[str, bool]):
        """Update the window to show *body* (or clear if None)."""
        self.lbl.config(text=body.name if body else "")
        self.txt.config(state="normal")
        self.txt.delete("1.0", tk.END)

        if body:
            for mat, pct in sorted(body.materials.items(),
                                   key=lambda kv: kv[1],
                                   reverse=True):
                if filters.get(mat, True):
                    self.txt.insert(tk.END,
                                    f"{mat.title():<12} {pct:5.1f}%\n")

            # ── Biosignals progress lines ───────────────────────────────
            if body.biosignals:
                self.txt.insert(tk.END, "\nBio-signals:\n")
                for species, done in body.bio_found.items():
                    if done >= 3:
                        self.txt.insert(tk.END, f"  ✅  {species}\n")
                    else:
                        self.txt.insert(tk.END, f"  {species}  ({done}/3)\n")

            # ── Geology progress lines ─────────────────────────────────
            if body.geosignals:
                self.txt.insert(tk.END, "\nGeo-signals:\n")
                done = len(body.geo_found)
                if done >= 1:
                    self.txt.insert(tk.END, f"  ✅  {done}/{body.geosignals}\n")
                else:
                    self.txt.insert(tk.END, f"  🌋  (?)/{body.geosignals}\n")

        if not self.txt.get("1.0", tk.END).strip():
            self.txt.insert(tk.END, "—")

        self.txt.config(state="disabled")

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
