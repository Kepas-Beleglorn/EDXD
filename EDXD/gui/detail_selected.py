from __future__ import annotations
import logging

from EDXD.gui.body_details import BodyDetails


logger = logging.getLogger(__name__)
TITLE = "Selected body"
WINID = "DETAIL_SELECTED"

class DetailSelected(BodyDetails):
    def __init__(self, parent):
        # 1. Load saved properties (or use defaults)
        BodyDetails.__init__(self, parent=parent, title=TITLE, win_id=WINID)
