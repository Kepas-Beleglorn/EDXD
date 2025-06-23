"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations
import wx
from typing import Dict
from EDXD.gui.custom_title_bar import CustomTitleBar
from EDXD.gui.helper.dynamic_frame import DynamicFrame
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "Minerals to show"
WINID = "MINERALS_FILTER"

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, RAW_MATS

# ---------------------------------------------------------------------------
class MineralsFilter(DynamicFrame):
    def __init__(self, parent, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        super().__init__(parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        #self.Bind(wx.EVT_CLOSE, self.on_close)

        self.grab_set()                     # modal

        self._on_apply = on_apply

        self._build_widgets()

        # noinspection PyTypeChecker
        self.after(ms=3000, func=self.loading_finished)

    def loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def _build_widgets(self):
        frame = ttk.Frame(self, style="Dark.TFrame")
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- mineral check-boxes ------------------------------------
        self.var_mat: Dict[str, tk.BooleanVar] = {}
        cols = 4
        rows = int(round(len(RAW_MATS) / cols ,0))
        for idx, mat in enumerate(RAW_MATS):
            var = tk.BooleanVar(value=self._prefs["mat_sel"].get(mat, True))
            self.var_mat[mat] = var
            cb = ttk.Checkbutton(frame, text=mat.title(), variable=var)
            c, r = divmod(idx, rows)
            cb.grid(row=r, column=c, sticky="w", padx=4, pady=2)

        # ---- (De)select-all & Apply buttons --------------------------
        btns = ttk.Frame(self, style="Dark.TFrame")
        btns.pack(pady=(cols, cols*2))

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
        self.on_close(none)

    def on_configure(self, event):  # move/resize
        if self._ready and not self._loading:
            self.props.height = event.height
            self.props.width = event.width
            self.props.posx = event.x
            self.props.posy = event.y
            self.props.save()

    def on_close(self, event):
        # Save geometry
        x, y = self.GetPosition()
        w, h = self.GetSize()
        props = WindowProperties(window_id=WINID, height=h, width=w, posx=x, posy=y)
        props.save()
        # Now close all child windows as needed!
        # for win in self.child_windows:
        #     win.Destroy()
        event.Skip()  # Let wx close the window
