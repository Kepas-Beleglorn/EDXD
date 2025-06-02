"""
detail_selected.py – “Selected body” pop-out window
==================================================

A tiny wrapper around a Tk Text widget; MainWindow calls
`detail.render(body, filters)` whenever the table selection changes.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict
from gui.theme_handler import apply_theme, apply_text_theme

from model import Body


class DetailSelected(tk.Toplevel):
    """Always reflects the row the user clicked in the BodiesTable."""

    def __init__(self, master):
        super().__init__(master)
        # ---- dark theme colours ----
        apply_theme(self)

        self.title("Selected body")
        self.resizable(False, False)

        self.lbl = ttk.Label(self, font=("Segoe UI", 11, "bold"))
        self.lbl.pack(anchor="w", padx=6, pady=(4, 2))

        self.txt = tk.Text(self,
                           width=40,
                           height=15,
                           state="disabled",
                           font=("Segoe UI", 9))
        self.txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 6))
        apply_text_theme(self.txt)
        

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], filters: Dict[str, bool]):
        """
        Update window contents.

        Args
        ----
        body     : Body object (or None to clear)
        filters  : {material → bool}; only True entries are shown
        """
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

