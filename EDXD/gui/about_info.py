from __future__ import annotations

from typing import Dict

import wx

from EDXD.globals import BTN_HEIGHT, BTN_WIDTH
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.link_label import LinkLabel
from EDXD.gui.helper.theme_handler import get_theme
from EDXD.gui.helper.window_properties import WindowProperties

TITLE = "About EDXD"
WINID = "ABOUT_INFO"

from EDXD.globals import DEFAULT_HEIGHT_ABOUT, DEFAULT_WIDTH_ABOUT, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN
from EDXD.globals import APP_TITLE, GIT_OWNER, GIT_REPO

# current version
try:
    from EDXD._version import VERSION as __version__
except Exception:
    __version__ = "0.0.0.0"

# ---------------------------------------------------------------------------
class AboutInfo(DynamicDialog):
    def __init__(self, parent, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT_ABOUT, default_width=DEFAULT_WIDTH_ABOUT, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicDialog.__init__(self, parent=parent, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, title=TITLE, win_id=WINID, show_minimize=False, show_maximize=False, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.theme = get_theme()
        self.parent = parent

        # current version
        self.txt_edxd_version = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        self.window_box.Add(self.txt_edxd_version, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, RESIZE_MARGIN + 10)

        # update available?
        self.txt_edxd_update = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        self.window_box.Add(self.txt_edxd_update, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN + 10)

        # project
        self.txt_edxd_proj = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        self.window_box.Add(self.txt_edxd_proj, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, RESIZE_MARGIN + 10)

        # link to project
        self.txt_git_proj = LinkLabel(self)
        self.window_box.Add(self.txt_git_proj, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN + 10)

        # latest release
        self.txt_edxd_latest = wx.StaticText(parent=self, style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        self.window_box.Add(self.txt_edxd_latest, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, RESIZE_MARGIN + 10)

        # link to latest release
        self.txt_git_release = LinkLabel(self)
        self.window_box.Add(self.txt_git_release, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN + 10)

        # project on edcodex
        self.txt_edcodex = wx.StaticText(parent=self,
                                             style=wx.TE_READONLY | wx.TEXT_ALIGNMENT_LEFT | wx.ALIGN_TOP | wx.BORDER_NONE)
        self.window_box.Add(self.txt_edcodex, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.NORTH, RESIZE_MARGIN + 10)

        # link to edcodex
        self.txt_edcodex_tool = LinkLabel(self)
        self.window_box.Add(self.txt_edcodex_tool, 0, wx.EXPAND | wx.EAST | wx.WEST, RESIZE_MARGIN + 10)

        # close button
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_close = DynamicButton(parent=self, label="Close", size=wx.Size(BTN_WIDTH + self.theme["button_border_width"], BTN_HEIGHT + self.theme["button_border_width"]), draw_border=True)
        hbox.Add(btn_close)
        self.window_box.Add(hbox, flag=wx.ALIGN_CENTER | wx.NORTH | wx.SOUTH, border=20)

        self.set_values()

        self.SetSizer(self.window_box)

        # Bindings
        btn_close.Bind(wx.EVT_BUTTON, lambda evt: self.Close())

        self.Fit()

    def set_values(self):

        self.txt_edxd_version.SetLabelText(f"{APP_TITLE}: {__version__}")

        # latest release on git
        from EDXD.data_handler.helper.version_check import check_github_for_update

        update, latest = check_github_for_update(__version__, GIT_OWNER, GIT_REPO, include_prereleases=False)
        if update:
            self.txt_edxd_update.SetLabelText(f"A newer version is available: {latest}\n")
        else:
            self.txt_edxd_update.SetLabelText(f"Congratulations! EDXD is up to date.")

        str_git_project = f"https://github.com/{GIT_OWNER}/{GIT_REPO}"
        str_git_release = f"{str_git_project}/releases/latest"

        self.txt_edxd_proj.SetLabelText("Project on github:")
        self.txt_git_proj.SetLabelText(f"{str_git_project}")
        self.txt_git_proj.url = f"{str_git_project}"

        self.txt_edxd_latest.SetLabelText("Latest release:")
        self.txt_git_release.SetLabelText(f"{str_git_release}")
        self.txt_git_release.url = f"{str_git_release}"

        str_edcodex = f"https://edcodex.info/?m=tools&entry=608"
        self.txt_edcodex.SetLabelText("Project on edcodex.info:")
        self.txt_edcodex_tool.SetLabelText(f"{str_edcodex}")
        self.txt_edcodex_tool.url = f"{str_edcodex}"

