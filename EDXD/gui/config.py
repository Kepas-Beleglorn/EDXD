"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations

from typing import Dict

import wx, json

from EDXD.globals import BTN_HEIGHT, BTN_WIDTH
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "EDXD Configuration"
WINID = "EDXD_CONFIGURATION"

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, CFG_FILE

# ---------------------------------------------------------------------------
class EDXDConfig(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.cfg = {}
        self._load_config()

        # Config items grid
        grid = wx.FlexGridSizer(cols=4, hgap=8, vgap=4)
        #for mat in RAW_MATS:
        #    btn = DynamicToggleButton(
        #        parent=self,
        #        label=mat.title(),
        #        is_toggled=self.prefs.get("mat_sel", {}).get(mat, True),
        #        size=wx.Size(MINERAL_BTN_WIDTH, BTN_HEIGHT)
        #    )
        #    self.mat_buttons[mat] = btn
        #    grid.Add(btn, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, -4)
        self.window_box.Add(grid, flag=wx.ALL, border=10)

        # (De)select all and Apply buttons
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_toggle = DynamicButton(parent=self, label="(De-)select all", size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        btn_apply = DynamicButton(parent=self, label="Apply filter", size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        hbox.Add(btn_toggle, flag=wx.RIGHT, border=8)
        hbox.Add(btn_apply)
        self.window_box.Add(hbox, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        self.SetSizer(self.window_box)

        # Bindings
        btn_toggle.Bind(wx.EVT_BUTTON, self.on_toggle_all)
        btn_apply.Bind(wx.EVT_BUTTON, self.on_apply)

        self.Fit()

    def _load_config(self):
        cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}

        #if args.journals:
        #    cfg["journal_dir"] = str(args.journals.expanduser())
        #    CFG_FILE.write_text(json.dumps(cfg, indent=2))
        ## ensure defaults even if file is old
        #journal_dir = Path(cfg.get("journal_dir", ""))
        #if not journal_dir.is_dir():
        #    sys.exit("Run once with --journals <Saved Games …>")

        #q = queue.Queue()
        #model = Model()
        #journal_reader = JournalReader(journal_dir, q)
        #journal_reader.start()
        #journal_controller = JournalController(q, model)
        #journal_controller.start()

        #cfg.setdefault("land", False)
        #cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})
        #if "worthwhile_threshold" not in cfg.keys():
        #    cfg["worthwhile_threshold"] = DEFAULT_WORTHWHILE_THRESHOLD

        #if "fuel_low_threshold" not in cfg.keys():
        #    cfg["fuel_low_threshold"] = DEFAULT_FUEL_LOW_THRESHOLD

    def _save_config(self):
        def _save():
            data = {k: v for k, v in self.cfg.items() if k != "save"}
            CFG_FILE.write_text(json.dumps(data, indent=2))

        # ensure defaults even if file is old
        self.cfg["save"] = _save  # ← make the save-function available
        self.cfg["save"]()

    def on_toggle_all(self, event):
        # Toggle all buttons to the same value (all on or all off)
        current = all(btn.GetValue() for btn in self.mat_buttons.values())
        new_val = not current
        for btn in self.mat_buttons.values():
            btn.SetValue(new_val)
            btn._is_toggled = new_val
            btn.Refresh()

    def on_apply(self, event):
        # Save the selections back to prefs
        self.prefs["mat_sel"] = {mat: btn.GetValue() for mat, btn in self.mat_buttons.items()}
        if "save" in self.prefs and callable(self.prefs["save"]):
            self.prefs["save"]()
        self.Close()
