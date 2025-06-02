# gui/__init__.py
"""
gui package
===========

Re-exports:
    • MainWindow – the root Tk window composed in main_window.py
    • RAW_MATS   – master list of material names (from config_panel.py)
"""

from .main_window import MainWindow
from .config_panel import RAW_MATS       # convenience re-export

__all__ = ["MainWindow", "RAW_MATS"]
