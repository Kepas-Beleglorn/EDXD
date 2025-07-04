from __future__ import annotations

from EDXD.gui.body_details import BodyDetails
from typing import Dict
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X

TITLE = "Targeted body"
WINID = "DETAIL_TARGETED"

class DetailTargeted(BodyDetails):
    def __init__(self, parent, prefs: Dict):
        # 1. Load saved properties (or use defaults)
        BodyDetails.__init__(self, parent=parent, title=TITLE, win_id=WINID, prefs=prefs)
