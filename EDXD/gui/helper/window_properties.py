"""
saves /loads stored window positions and sizes
------------------------------------------------------
===================== USAGE SAVE =====================
class WINDOW(wx.Frame):
    def __init__(self, ...):
        ...
        self.Bind(wx.EVT_CLOSE, self.on_close)
        ...

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

------------------------------------------------------
===================== USAGE LOAD =====================
class WINDOW(wx.Frame):
    def __init__(self, model, prefs):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load("MAIN_FRAME", default_height=600, default_width=900, default_posx=100, default_posy=100)
        super().__init__(parent=None, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP)

        # 2. Apply geometry
        self.SetSize((props.width, props.height))
        self.SetPosition((props.posx, props.posy))

"""

import json
import os
from typing import Optional
from EDXD.globals import CFG_FILE

class WindowProperties:
    __slots__ = ("window_id", "height", "width", "posx", "posy", "show_window")

    def __init__(self, window_id: Optional[str], height: Optional[int], width: Optional[int], posx: Optional[int], posy: Optional[int], show_window: Optional[bool]) -> None:
        self.window_id:     Optional[str]   = window_id
        self.height:        Optional[int]   = height
        self.width:         Optional[int]   = width
        self.posx:          Optional[int]   = posx
        self.posy:          Optional[int]   = posy
        self.show_window:   Optional[bool]  = show_window

    @classmethod
    def load(cls, window_id: str, default_height=400, default_width=300, default_posx=100, default_posy=100, default_show=True):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r") as f:
                data = json.load(f)
            props = data.get(window_id)
            if props:
                if "show_window" not in props:
                    props["show_window"] = default_show
                return cls(window_id, props["height"], props["width"], props["posx"], props["posy"], props["show_window"])
        # Return defaults if not found
        return cls(window_id, default_height, default_width, default_posx, default_posy, default_show)

    def save(self):
        # Read current config or create new
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
        # Update this window's properties
        data[self.window_id] = {
            "height": self.height,
            "width": self.width,
            "posx": self.posx,
            "posy": self.posy,
            "show": self.show_window
        }
        # Write back to disk
        with open(CFG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def __repr__(self):
        return f"WindowProperties({self.window_id}, {self.height}, {self.width}, {self.posx}, {self.posy}, {self.show_window})"
