# gui/__init__.py
"""
gui package
===========

Re-exports:
    • MainWindow – the root Tk window composed in main_window.py
    • RAW_MATS   – master list of material names (from set_mineral_filter.py)
"""

from .main_window import MainWindow
from .set_mineral_filter import RAW_MATS       # convenience re-export

__all__ = ["MainWindow", "RAW_MATS"]
