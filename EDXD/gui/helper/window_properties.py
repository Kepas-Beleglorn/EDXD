

import json
import os
from EDXD.gobal_constants import CFG_FILE

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


"""
*** USAGE ***
from window_properties import WindowProperties

        # Load properties for this window (with defaults if not saved before)
        self.props = WindowProperties.load(WINID)
        self.geometry(f"{self.props.width}x{self.props.height}+{self.props.posx}+{self.props.posy}")
        self._ready = False  # not yet mapped
        self._loading = True  # during startup we must not save, otherwise we'll get garbage!!
        self.bind("<Map>", self.on_mapped)  # mapped == now visible
        self.bind("<Configure>", self.on_configure)  # move / resize
        
        ...
        
        self.after(3000, self.loading_finished)

    def loading_finished(self):
        self._loading = False

# ... later, after a resize/move event
    # --------------------------------------------------------------
    def on_mapped(self, _):
        #First time the window becomes visible.
        self._ready = True

    def on_configure(self, event):  # move/resize
        if self._ready and not self._loading:
            self.props.height = event.height
            self.props.width = event.width
            self.props.posx = event.x
            self.props.posy = event.y
            self.props.save()


"""