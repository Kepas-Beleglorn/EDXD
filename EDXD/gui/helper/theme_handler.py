"""
theme_handler.py – Centralized theme handling for EDXD GUI
==========================================================
Call `apply_theme(widget)` before creating widgets in any Tk/Toplevel window.
"""

import tkinter as tk
import os
from tkinter import ttk, PhotoImage

# Centralized theme colors
BG = "#121212"      # background
FG = "#ff9a00"      # orange foreground/text
ACC = "#ff9a00"     # accent (same as FG)
HBG = "#433322"     # hover background

ICON_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'resources', 'edxd_16.png'))  # Normalize path for OS compatibility

def set_icon(widget):
    # --- set app icon ---
    img = PhotoImage(file=ICON_PATH)
    widget.iconphoto(True, img)

def apply_theme(widget):
    """
    Apply EDXD dark-orange theme to the provided widget (Tk or Toplevel).
    Should be called before creating child widgets.
    """
    style = ttk.Style(widget)
    style.theme_use("clam")

    # Global background/foreground
    style.configure(".", background=BG, foreground=FG, fieldbackground=BG)

    # Buttons
    style.configure("TButton",
                    background=BG, foreground=FG,
                    borderwidth=1, focusthickness=1, bordercolor=FG, relief="solid")
    style.map("TButton",
              background=[("active", HBG), ("pressed", ACC)],
              foreground=[("active", ACC), ("pressed", BG)])

    # Checkbuttons
    style.configure("TCheckbutton", background=BG, foreground=FG)
    style.map("TCheckbutton",
              background=[("active", HBG)],
              foreground=[("active", ACC)])

    # Treeview headings
    style.configure("Treeview.Heading",
                    background=BG, foreground=FG, relief="flat")
    style.map("Treeview.Heading",
              background=[("active", BG)],
              foreground=[("active", FG)])

    # Treeview rows
    style.configure("Treeview",
                    background=BG, foreground=FG,
                    fieldbackground=BG, borderwidth=0,
                    rowheight=22)
    style.map("Treeview",
              background=[("selected", BG)],
              foreground=[("selected", ACC)])

    # Tooltip (for custom TLabel tooltips)
    style.configure("Tip.TLabel",
                    background="#262626", foreground=FG,
                    borderwidth=1, relief="solid")

    # Labels
    style.configure("TLabel", background=BG, foreground=FG)

    # Textfields
    style.configure("TText", background=BG, foreground=FG, insertbackground=FG)

    # Set widget background directly (for Tk/Toplevel)
    widget.configure(background=BG)

def apply_text_theme(text_widget):
    """Apply EDXD theme to a tk.Text widget."""
    text_widget.configure(
        background=BG,
        foreground=FG,
        insertbackground=FG  # caret color
    )
