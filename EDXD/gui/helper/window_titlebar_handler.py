"""
window_titlebar_handler.py – Centralized theme handling for EDXD title bars
==========================================================
Call `CustomTitlebar(widget)` before creating widgets in any Tk/Toplevel window.
"""
from EDXD.gui.helper.theme_handler import BG, FG, HBG, ICON_PATH
import tkinter as tk
import os

btn_style = {
    "relief": "flat",
    "bd": 0,
    "highlightthickness": 0,
    "bg": BG,
    "fg": FG,
    "activebackground": HBG,  # No color change on hover
    "activeforeground": FG
}

class CustomTitlebar(tk.Frame):
    def __init__(self, parent, title="Window", theme=None, on_close=None, show_close=True, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.title = title
        self.theme = theme or {
            'titlebar_bg': BG,
            'title_fg': FG,
            'button_bg': BG,
            'button_fg': FG
        }

        parent.overrideredirect(True)

        self.show_close = show_close
        self.on_close = on_close or parent.destroy
        #self.on_minimize = on_minimize or getattr(parent, 'iconify', lambda: None)
        self.icon_img = None

        self.configure(bg=self.theme['titlebar_bg'])
        self._create_widgets(ICON_PATH)
        self._place_widgets()
        self._add_dragging()

    def _create_widgets(self, icon_path):
        # Load the icon if provided and file exists
        if icon_path and os.path.isfile(icon_path):
            try:
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.icon_label = tk.Label(
                    self, image=self.icon_img, bg=self.theme['titlebar_bg'], bd=0
                )
            except Exception as e:
                print(f"Could not load icon: {e}")
                self.icon_label = None
        else:
            self.icon_label = None

        self.title_label = tk.Label(
            self, text=self.title,
            bg=self.theme['titlebar_bg'], fg=self.theme['title_fg'],
            font=("Segoe UI", 10, "bold")
        )
        """
        self.min_btn = tk.Button(
            self, text="__", command=self.on_minimize, padx=8, font=("Segoe UI", 10, "bold"), **btn_style
        )
        """
        self.close_btn = tk.Button(
            self, text="✕", command=self.on_close, padx=4, font=("Segoe UI", 10, "bold"), **btn_style
        )

    def _place_widgets(self):
        if self.icon_label:
            self.icon_label.pack(side="left", padx=4, pady=2)
        self.title_label.pack(side="left", padx=7)
        if self.show_close:
            self.close_btn.pack(side="right", padx=1)
        #self.min_btn.pack(side="right", padx=1)

    def _add_dragging(self):
        def start_move(event):
            self.x = event.x
            self.y = event.y
        def do_move(event):
            # noinspection PyUnresolvedReferences
            x = event.x_root - self.x
            # noinspection PyUnresolvedReferences
            y = event.y_root - self.y
            self.parent.geometry(f'+{x}+{y}')
        # Bind dragging to icon, title, and frame itself
        for widget in (self, self.title_label, getattr(self, "icon_label", None)):
            if widget:
                widget.bind("<Button-1>", start_move)
                widget.bind("<B1-Motion>", do_move)

"""
# Example usage in your window/widget:
if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(True)
    titlebar = CustomTitlebar(root, title="EDXD Demo")
    titlebar.pack(fill="x")
    main = tk.Frame(root, bg="#333", height=200)
    main.pack(fill="both", expand=True)
    root.geometry("400x300")
    root.mainloop()
------    
    from .helper.window_titlebar_handler import CustomTitlebar
    TITLE = "..."
    # In your window constructor:
    self.titlebar = CustomTitlebar(self, title=TITLE)
    self.titlebar.pack(fill="x")

"""
