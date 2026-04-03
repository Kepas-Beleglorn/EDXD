
from __future__ import annotations

from typing import Dict, List, Set

import wx

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import EDXD.data_handler.helper.data_helper as dh

TITLE = "Biosignal prediction"
WINID = "BIOSIGNAL_PREDICTION"

class SignalPrediction(DynamicDialog):
    def __init__(self, parent, title=TITLE, win_id=WINID, is_hidden: bool = True):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(win_id, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y, default_is_hidden=False)
        if props.is_hidden: return
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=title, win_id=win_id, show_minimize=False, show_maximize=False, show_close=True, vertical_scroll=True, horizontal_scroll=False)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=win_id)

        self.theme = get_theme()

        self._ready = False  # not yet mapped
        self._loading = True  # during startup, we must not save, otherwise we'll get garbage!!
        self.Bind(wx.EVT_SHOW, self._on_show)

        # collapsible panels with details
        self.prediction_panels: Dict[str, CollapsiblePanel] = {}

        self.finalize_layout()
        # noinspection PyTypeChecker
        wx.CallLater(millis=3000, callableObj=self._loading_finished)

    def _loading_finished(self):
        self._loading = False

    # ------------------------------------------------------------------
    def render(self, prediction: Dict[str, List[Dict]] = None):
        panels_to_remove: Set[str] = set()
        # remove unnecessary panels
        for panel_key in self.prediction_panels:
            if panel_key not in prediction.keys():
                panels_to_remove.add(panel_key)

        for panel_key in panels_to_remove:
            panel: CollapsiblePanel = self.prediction_panels.pop(panel_key)
            self.window_box.Detach(panel)
            panel.Destroy()

        # add more panels
        for prediction_key in prediction.keys():
            if prediction_key not in self.prediction_panels.keys():
                body_name = prediction[prediction_key][0]["body_name"]
                new_panel = CollapsiblePanel(parent=self.scroll_container, columns=5, label=body_name)
                self.prediction_panels[prediction_key] = new_panel
                self.window_box.Add(self.prediction_panels[prediction_key], 0, wx.EXPAND, RESIZE_MARGIN)

        for panel_key in self.prediction_panels:
            self.prediction_panels[panel_key].reset_table()

        for body_id, body_data in prediction.items():
            self._update_general(self.prediction_panels[body_id], body_data)

        self.window_box.Layout()

        if not self.IsShown():
            self.Show()

    # --------------------------------------------------------------
    def _on_show(self, event):
        """First time the window becomes visible."""
        self._ready = True
        event.Skip()

    def _update_general(self, prediction_panel: CollapsiblePanel, body_data: List[Dict] = None):
        if prediction_panel is None or body_data is None or len(body_data) == 0:
            return

        if not prediction_panel.IsShown():
            prediction_panel.Show()

        for item in body_data:
            genus_name: str = item["name"]
            genus_variant: str = item["variant_color"] or ""
            genus_probability: float = item["probability"]
            genus_value: int = item["base_value"]
            prediction_panel.add_table_item(f"  {genus_name}")
            prediction_panel.add_table_item(f" {genus_variant}")
            self._set_probability_colour(prediction_panel.add_table_item(f"  {dh.format_probability(genus_probability)}", align=wx.ALIGN_RIGHT), genus_probability)
            prediction_panel.add_table_item(f"  {genus_value:,} Cr", align=wx.ALIGN_RIGHT)
            prediction_panel.add_table_item("")

        if prediction_panel.IsShown():
            # Force a layout update
            prediction_panel.force_render()

    @staticmethod
    def _set_probability_colour(label: wx.StaticText = None, probability: float = 0.0):
        if label is None:
            return
        label.SetForegroundColour(dh.get_colour_gradient_from_probability(probability))

