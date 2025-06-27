"""
detail_selected.py – “Selected body” pop-out window
==================================================

A tiny wrapper around a Tk Text widget; MainWindow calls
`detail.render(body, filters)` whenever the table selection changes.
"""

from __future__ import annotations
import wx
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.gui_handler import init_widget
from typing import Optional, Dict
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN
from EDXD.model import Body

TITLE = "Selected body"
WINID = "DETAIL_SELECTED"

class DetailSelected(DynamicDialog):
    def __init__(self, parent, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.prefs = prefs

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # body name
        self.lbl_body = wx.StaticText(parent=self)
        self._update_body()
        self.window_box.Add(self.lbl_body, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # body details
        self.txt_body_details = wx.TextCtrl(parent=self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        init_widget(self.txt_body_details, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)
        self.txt_body_details.SetEditable(False)
        self.window_box.Add(self.txt_body_details, 1, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        self.SetSizer(self.window_box)

        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, body: Optional[Body], filters: Dict[str, bool]):
        self.lbl_body.SetLabelText(text=body.name if body else "")
        self.txt_body_details.Clear()

        if body:
            for mat, pct in sorted(body.materials.items(),
                                   key=lambda kv: kv[1],
                                   reverse=True):
                if filters.get(mat, True):
                    self.txt_body_details.AppendText(f"{mat.title():<12} {pct:5.1f}%\n")

            # ── Biosignals progress lines ───────────────────────────────
            if body.biosignals:
                self.txt_body_details.AppendText("\nBio-signals:\n")
                for species, done in body.bio_found.items():
                    if done >= 3:
                        self.txt_body_details.AppendText(f"  ✅  {species}\n")
                    else:
                        self.txt_body_details.AppendText(f"  {species}  ({done}/3)\n")

            # ── Geology progress lines ─────────────────────────────────
            if body.geosignals:
                self.txt_body_details.AppendText("\nGeo-signals:\n")
                done = len(body.geo_found)
                if done >= 1:
                    self.txt_body_details.AppendText(f"  ✅  {done}/{body.geosignals}\n")
                else:
                    self.txt_body_details.AppendText(f"  🌋  (?)/{body.geosignals}\n")

        if not self.txt_body_details.GetValue().strip():
            self.txt_body_details.SetValue("—")

        if not self.IsShown():
            self.Show()

    # --------------------------------------------------------------
    def _on_show(self, event):
        """First time the window becomes visible."""
        self._ready = True

    def _update_body(self, title: str = ""):
        init_widget(widget=self.lbl_body, title=title)
        font = self.lbl_body.GetFont()
        font.PointSize += 2
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.lbl_body.SetFont(font)
