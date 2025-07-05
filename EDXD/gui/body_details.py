
from __future__ import annotations
import wx
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.gui_handler import init_widget
from typing import Optional, Dict
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN, ICONS
from EDXD.data_handler.model import Body

TITLE = "BODY DETAILS"
WINID = "BODY_DETAILS"

class BodyDetails(DynamicDialog):
    def __init__(self, parent, title, win_id, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

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
        self.lbl_body.SetLabelText(text=body.body_name if body else "")
        self.txt_body_details.Clear()

        if body:
            for mat, pct in sorted(body.materials.items(),
                                   key=lambda kv: kv[1],
                                   reverse=True):
                if filters.get(mat, True):
                    self.txt_body_details.AppendText(f"{mat.title():<12} {pct:5.1f}%\n")

            # ── Biosignals progress lines ───────────────────────────────
            if body.biosignals:
                self.txt_body_details.AppendText(f"\n{ICONS['biosigns']}{' '*2}Bio-signals:\n")
                if body.bio_found:
                    for species, genus in body.bio_found.items():
                        done = int(genus.get("scanned_count") if genus.get("scanned_count") else 0)
                        bio_name = genus.get("variant_localised") or genus.get("species_localised") or genus.get("localised")
                        if done >= 3:
                            self.txt_body_details.AppendText(f"{' '*2}{ICONS['checked']}{' '*2}{bio_name}\n")
                        elif 0 < done < 3:
                            self.txt_body_details.AppendText(f"{' ' * 2}{ICONS['in_progress']}{' ' * 2}{bio_name}{' '*2}({done}/3)\n")
                        else:
                            self.txt_body_details.AppendText(f"{' ' * 2}{ICONS['unknown']}{' '*2}{bio_name}\n")

            # ── Geology progress lines ─────────────────────────────────
            if body.geosignals:
                self.txt_body_details.AppendText(f"\n{ICONS['geosigns']}{' '*2}Geo-signals:")

                done = len(body.geo_found) if body.geo_found is not None else 0
                if 0 < done < body.geosignals:
                    self.txt_body_details.AppendText(f"{' '*2}{done}/{body.geosignals}{' '*2}{ICONS['in_progress']}\n")
                elif done == body.geosignals:
                    self.txt_body_details.AppendText(f"{' '*2}{done}/{body.geosignals}{' '*2}{ICONS['checked']}\n")
                else:
                    self.txt_body_details.AppendText(f"{' '*2}(?)/{body.geosignals}{' '*2}{ICONS['geosigns']}\n")

                for geo in body.geo_found.items():
                    if geo.get("is_new"):
                        self.txt_body_details.AppendText(f"{ICONS['new_entry']:>4}{ICONS['geosigns']:>4}{' '*4}{geo.get('localised')}\n")
                    else:
                        self.txt_body_details.AppendText(f"{ICONS['geosigns']:>13}{' '*4}{geo.get('localised')}\n")

        else:
            self.txt_body_details.Clear()

        if not self.txt_body_details.GetValue().strip():
            self.txt_body_details.SetValue("—")

        if not self.IsShown():
            self.Show()

    # --------------------------------------------------------------
    def _on_show(self, event):
        """First time the window becomes visible."""
        self._ready = True
        event.Skip()

    def _update_body(self, title: str = ""):
        init_widget(widget=self.lbl_body, title=title)
        font = self.lbl_body.GetFont()
        font.PointSize += 2
        font.FontWeight = wx.FONTWEIGHT_BOLD
        self.lbl_body.SetFont(font)
