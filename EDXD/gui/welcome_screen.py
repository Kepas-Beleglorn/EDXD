from __future__ import annotations

"""
welcome_screen.py – Welcome screen for first-time users
=======================================================
• Displays a welcome message introducing EDXD
• Hints that the configuration panel will open after closing
• Used only on first run to guide new users
"""
import logging

import wx

from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_X, DEFAULT_POS_Y, BTN_WIDTH, BTN_HEIGHT, RESIZE_MARGIN
from EDXD.gui.helper.dynamic_dialog import DynamicDialog
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget


logger = logging.getLogger(__name__)
TITLE = "Welcome to EDXD"
WINID = "EDXD_WELCOME_SCREEN"


class WelcomeScreen(DynamicDialog):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(
            WINID,
            default_height=DEFAULT_HEIGHT,
            default_width=DEFAULT_WIDTH,
            default_posx=DEFAULT_POS_X,
            default_posy=DEFAULT_POS_Y,
            default_is_hidden=False
        )
        DynamicDialog.__init__(
            self,
            parent=parent,
            style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP,
            title=TITLE,
            win_id=WINID,
            show_minimize=False,
            show_maximize=False,
            show_close=True
        )
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        # Welcome message
        welcome_text = (
            "Welcome to ED eXploration Dashboard!\n\n"
            "EDXD is a dashboard for Elite Dangerous that helps you explore and analyze "
            "the stars around you.\n\n"
            "It provides real-time information about your current system, including body "
            "details, navigation routes, engine status, and more.\n\n"
            "To get started, you'll need to configure EDXD to point to your Elite Dangerous "
            "journal files.\n\n"
            "It's recommended to run the Journal Historian first to process your historical journal files.\n\n"
            "The configuration panel will open automatically after you close this window."
        )

        self.lbl_welcome = wx.StaticText(self.scroll_container, label=welcome_text)
        self.window_box.Add(self.lbl_welcome, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        # Continue button
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_continue = DynamicButton(
            self.scroll_container,
            style=wx.ID_OK,
            label="Continue to Configuration",
            size=(BTN_WIDTH, BTN_HEIGHT)
        )
        self.btn_continue.SetName("CONTINUE")
        init_widget(self.btn_continue)
        btn_sizer.Add(self.btn_continue, 0, wx.ALL, 5)

        self.window_box.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        # Bind the continue button
        self.Bind(wx.EVT_BUTTON, self.on_continue, self.btn_continue)

        self.finalize_layout()
        self.Fit()

    def on_continue(self, event):
        self.EndModal(wx.ID_OK)

    def ShowModal(self):
        if self.IsBeingDeleted():
            return wx.ID_CANCEL
        try:
            super().ShowModal()
        except Exception:
            pass
        return self.result if hasattr(self, 'result') else wx.ID_OK
