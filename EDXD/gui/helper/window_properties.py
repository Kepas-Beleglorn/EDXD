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


"""

import json
import os
from EDXD.globals import CFG_FILE

class WindowProperties:
    __slots__ = ("window_id", "height", "width", "posx", "posy")

    def __init__(self, window_id: str, height: int, width: int, posx: int, posy: int):
        self.window_id = window_id
        self.height = height
        self.width = width
        self.posx = posx
        self.posy = posy


    @classmethod
    def load(cls, window_id: str, default_height=400, default_width=300, default_posx=100, default_posy=100):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r") as f:
                data = json.load(f)
            props = data.get(window_id)
            if props:
                return cls(window_id, props["height"], props["width"], props["posx"], props["posy"])
        # Return defaults if not found
        return cls(window_id, default_height, default_width, default_posx, default_posy)

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
            "posy": self.posy
        }
        # Write back to disk
        with open(CFG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def __repr__(self):
        return f"WindowProperties({self.window_id}, {self.height}, {self.width}, {self.posx}, {self.posy})"
