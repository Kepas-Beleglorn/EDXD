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
from gui.theme_handler import apply_theme, apply_text_theme

from model import Body


class DetailTarget(tk.Toplevel):
    """Always reflects whatever the player has targeted in-game."""

    def __init__(self, master):
        super().__init__(master)
        self.title("In-game target")
        self.resizable(False, False)

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

        if not self.txt.get("1.0", tk.END).strip():
            self.txt.insert(tk.END, "—")

        self.txt.config(state="disabled")
