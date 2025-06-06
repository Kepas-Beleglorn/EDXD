

import json
import os
from ...gobal_constants import CFG_FILE

class WindowProperties:
    __slots__ = ("window_id", "height", "width", "posx", "posy")

    def __init__(self, window_id: str, height: int, width: int, posx: int, posy: int):
        self.window_id = window_id
        self.height = height
        self.width = width
        self.posx = posx
        self.posy = posy

    @classmethod
    def load(cls, window_id: str, default_size=(400, 300), default_pos=(100, 100)):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r") as f:
                data = json.load(f)
            props = data.get(window_id)
            if props:
                return cls(window_id, props["height"], props["width"], props["posx"], props["posy"])
        # Return defaults if not found
        return cls(window_id, default_size[1], default_size[0], default_pos[0], default_pos[1])

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
props = WindowProperties.load("main_window", default_size=(800, 600))

# Set/restore geometry
root.geometry(f"{props.width}x{props.height}+{props.posx}+{props.posy}")

# ... later, before closing or after a resize/move event
props.height = new_height
props.width = new_width
props.posx = new_x
props.posy = new_y
props.save()
"""