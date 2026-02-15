"""
set_mineral_filter.py – filter & preferences window
============================================
• “Landable only” master checkbox
• 4-column alphabetic grid with a (De)select-all toggle
• Writes changes back to the `prefs` dict supplied by MainWindow
"""

from __future__ import annotations

import wx, json
import subprocess
import sys

from EDXD.globals import BTN_HEIGHT, BTN_WIDTH, CACHE_DIR
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dir_picker import DirPicker
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "EDXD Configuration"
WINID = "EDXD_CONFIGURATION"

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, CFG_FILE, RESIZE_MARGIN

# ---------------------------------------------------------------------------
class EDXDConfig(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=False)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.cfg = {}
        self._load_config()

        # Config items grid
        self.grid_paths = wx.FlexGridSizer(cols=2, hgap=8, vgap=4)

        # Make the second, third, and fourth columns growable
        self.grid_paths.AddGrowableCol(1)

        # Journal directory label
        self.lbl_journal_dir = wx.StaticText(self, label="Journal file directory:")
        self.grid_paths.Add(self.lbl_journal_dir, flag=wx.ALIGN_CENTER_VERTICAL)

        # Journal directory file picker
        self.journal_dir_picker = DirPicker(self, style=wx.DIRP_USE_TEXTCTRL)
        self.grid_paths.Add(self.journal_dir_picker, flag=wx.EXPAND)

        # System cache directory label
        self.lbl_system_cache_dir = wx.StaticText(self, label="System cache directory:")
        self.grid_paths.Add(self.lbl_system_cache_dir, flag=wx.ALIGN_CENTER_VERTICAL)

        # System cache directory file picker
        self.system_cache_dir_picker = DirPicker(self, style=wx.DIRP_USE_TEXTCTRL)
        self.journal_dir_picker.SetPath(self.cfg.get("cache_dir", ""))
        self.grid_paths.Add(self.system_cache_dir_picker, flag=wx.EXPAND)

        # Add the grid to your main sizer
        self.window_box.Add(self.grid_paths, flag=wx.ALL | wx.EXPAND, border=10)

        # set defaults
        temp: str = self.cfg.get("journal_dir", "")
        self.journal_dir_picker.SetPath(temp)
        self.journal_dir_picker.Refresh()
        temp: str = self.cfg.get("cache_dir", str(CACHE_DIR))
        self.system_cache_dir_picker.SetPath(temp)
        self.system_cache_dir_picker.Refresh()
        self.Layout()

        # Config items grid for buttons
        self.grid_windows = wx.FlexGridSizer(cols=2, hgap=8, vgap=4)
        self.grid_windows.AddGrowableCol(0)
        self.grid_windows.AddGrowableCol(1)

        # Buttons
        self.window_identifiers = [
            ["DETAIL_TARGETED", "Targeted body"],
            ["DETAIL_SELECTED", "Selected body"],
            ["PSPS",            "Planetary Surface Positioning System"],
            ["ENGINE_STATUS",   "Engine status"],
            ["STATUS_FLAGS",    "Status flags"]
        ]

        self.window_buttons = {}
        for i in range(len(self.window_identifiers)):
            btn = DynamicToggleButton(
                parent=self,
                label=f"{self.window_identifiers[i][1]}",
                is_toggled=not self.cfg.get(self.window_identifiers[i][0], {}).get("is_hidden", False),
                size=wx.Size(BTN_WIDTH, BTN_HEIGHT)
            )
            self.window_buttons[self.window_identifiers[i][0]] = btn
            self.grid_windows.Add(btn, flag=wx.EXPAND)

        # Add the grid to your main sizer
        self.window_box.Add(self.grid_windows, flag=wx.ALL | wx.EXPAND, border=10)

        # Config items grid for buttons
        self.grid_save_close = wx.FlexGridSizer(cols=2, hgap=8, vgap=4)
        self.grid_save_close.AddGrowableCol(0)
        self.grid_save_close.AddGrowableCol(1)

        # Save button
        self.btn_save_and_close = DynamicButton(parent=self, label="Save and close settings",
                                   size=wx.Size(BTN_WIDTH + self.theme["button_border_width"],
                                                BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        self.grid_save_close.Add(self.btn_save_and_close, flag=wx.EXPAND)

        self.btn_cancel = DynamicButton(parent=self, label="Discard changes and close settings",
                                                size=wx.Size(BTN_WIDTH + self.theme["button_border_width"],
                                                             BTN_HEIGHT + self.theme["button_border_width"]),
                                                draw_border=True)
        self.grid_save_close.Add(self.btn_cancel, flag=wx.EXPAND)

        self.window_box.Add(self.grid_save_close, flag=wx.ALL | wx.EXPAND, border=10)

        # Bindings
        self.btn_save_and_close.Bind(wx.EVT_BUTTON, self._save_config)
        self.btn_cancel.Bind(wx.EVT_BUTTON, lambda evt: self.Close())

        # Set the main sizer
        self.SetSizer(self.window_box)

    def restart_app(self):
        wx.GetApp().ExitMainLoop()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()

    def _load_config(self):
        self.cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}

    def _save_config(self, event):
        for win_id, btn in self.window_buttons.items():
            self.cfg[win_id]["is_hidden"] = not btn.GetValue()

        # check if paths have changed
        old_journal_path = self.cfg["journal_dir"]
        old_system_cache_dir = self.cfg["cache_dir"]
        restart_required = False
        if old_journal_path != self.journal_dir_picker.GetPath():
            restart_required = True

        if old_system_cache_dir != self.system_cache_dir_picker.GetPath():
            restart_required = True

        self.cfg["journal_dir"] = self.journal_dir_picker.GetPath()
        self.cfg["cache_dir"] = self.system_cache_dir_picker.GetPath()

        def _save():
            data = {k: v for k, v in self.cfg.items() if k != "save"}
            CFG_FILE.write_text(json.dumps(data, indent=2))

        self.cfg["save"] = _save  # ← make the save-function available
        self.cfg["save"]()

        if restart_required:
            dlg = wx.MessageDialog(None, "Changing paths requires a restart, otherwise the old paths will be used! Restart now?",
                                   "Restart Required", wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.restart_app()
            dlg.Destroy()
        else:
            self.Close()
