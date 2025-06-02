from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional

from model import Body
from gui.config_panel import RAW_MATS

# symbol lookup (feel free to extend)
SYMBOL = {
    "antimony":"Sb", "arsenic":"As", "boron":"B", "cadmium":"Cd",
    "carbon":"C",   "chromium":"Cr", "germanium":"Ge", "iron":"Fe",
    "lead":"Pb",    "manganese":"Mn","mercury":"Hg",  "molybdenum":"Mo",
    "nickel":"Ni",  "niobium":"Nb", "phosphorus":"P", "polonium":"Po",
    "rhenium":"Re", "ruthenium":"Ru","selenium":"Se", "sulphur":"S",
    "technetium":"Tc","tellurium":"Te","tin":"Sn","tungsten":"W",
    "vanadium":"V", "yttrium":"Y", "zinc":"Zn", "zirconium":"Zr",
}

# ---------------------------------------------------------------------------
# very small tooltip helper
class _Tip(tk.Toplevel):
    def __init__(self, widget, text):
        super().__init__(widget)

        self.withdraw()                       # keep hidden until .show()
        self.wm_overrideredirect(True)        # no window decorations
        self.label = ttk.Label(self, text=text, style="Tip.TLabel")

        self.label.pack(ipadx=2)

    def show(self, x, y):
        self.wm_geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()

# ---------------------------------------------------------------------------
class BodiesTable(ttk.Treeview):
    """Table with Body | 🛬 | one column per mineral."""

    def __init__(self, master, on_select: Callable[[str], None]):
        # columns: Body | landable | all minerals (fixed order)
        cols = ("status", "body", "land", "bio") + tuple(RAW_MATS)
        super().__init__(master, columns=cols, show="headings", height=18)

        # Status column – shows selection/target icons; not sortable
        #self.heading("status", text="🎯🖱")
        self.heading("status", text=" ")
        self.column("status", width=40, anchor="center")

        # Body column
        self.heading("body", text="Body",
                     command=lambda: self._sort_by("body"))
        self.column("body", width=300, anchor="w")

        # Landable column – little landing icon
        self.heading("land", text="🛬",
                     command=lambda: self._sort_by("land"))
        self.column("land", width=40, anchor="center")

        # Bio-signals column
        self.heading("bio", text="🌿",
                     command=lambda: self._sort_by("bio"))
        self.column("bio", width=40, anchor="center")

        # Mineral columns
        for mat in RAW_MATS:
            sym = SYMBOL.get(mat, mat[:2].title())
            self.heading(mat, text=sym,
                         command=lambda m=mat: self._sort_by(m))
            self.column(mat, width=50, anchor="e")

        # mapping Treeview column IDs → full mineral names
        self._col2name = {mat: mat.title() for mat in RAW_MATS}
        self._tip      = None              # current tooltip window
        self._tip_col  = None              # column it belongs to

        # mouse-motion handler to pop tool-tips on header hover
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>",  lambda e: self._hide_tip())

        # sort state
        self.sort_col: Optional[str] = None
        self.sort_reverse            = False

        # row-select callback
        self.bind("<<TreeviewSelect>>",
                  lambda _e:
                  on_select(self.selection()[0]) if self.selection() else None)

    # --------------------------------------------------------------
    def _sort_by(self, col: str):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col     = col
            self.sort_reverse = (col in RAW_MATS)    # minerals → descending first
        self.event_generate("<<EdmSortRequest>>")    # MainWindow refreshes

    # --------------------------------------------------------------
    pass

    # ------------------------------------------------------------------
    def refresh(self, *, bodies, filters, landable_only,
                selected_name, target_name):

        """
        bodies        : {name -> Body}
        filters       : {mineral -> bool}
        landable_only : True = show only landable worlds
        """
        # 1) decide which mineral columns are visible right now
        visible_mats = [m for m, on in filters.items() if on]

        # show Body | land | each visible mineral (in RAW_MATS order)
        self["displaycolumns"] = ("status", "body", "land", "bio", *visible_mats)

        # 2) update / create rows
        existing = set(self.get_children())
        for name, body in bodies.items():
            if landable_only and not body.landable:
                continue

            status_icon = (
                "🎯🖱" if name == target_name == selected_name else
                "🎯"    if name == target_name else
                "🖱"    if name == selected_name else
                ""
            )

            # fixed-length value list: one cell per column declared in __init__
            row = [
                status_icon,                     # NEW status column
                name,                            # body name
                "🛬" if body.landable else "",
                f"🌿 {body.biosignals}" if body.biosignals else "",
            ] + [
                f"{body.materials[m]:.1f} %" if m in body.materials else ""
                for m in RAW_MATS
            ]


            if name in existing:
                self.item(name, values=row)
                existing.remove(name)
            else:
                self.insert("", "end", iid=name, values=row)

        # 3) remove rows that vanished
        for iid in existing:
            self.delete(iid)

        # 4) apply current sort order (if any)
        if self.sort_col:
            if self.sort_col == "body":
                idx, numeric = 0, False
            elif self.sort_col == "land":
                idx, numeric = 1, False
            else:                           # mineral column
                idx = 2 + RAW_MATS.index(self.sort_col)
                numeric = True
            self._apply_sort(idx, numeric)

    # ------------------------------------------------------------------
    def _apply_sort(self, col_index: int, numeric: bool):
        """
        col_index : 0 = body, 1 = land, 2-… mineral columns
        numeric   : True for mineral columns
        """

        def sort_key(iid):
            cell = self.set(iid, column=col_index)

            # Body column ─────────────────────────────────────────────
            if col_index == 1:
                return cell.lower()

            # Landable column (🛬 / '') ───────────────────────────────
            if col_index == 2:
                return 0 if cell else 1      # 🛬 rows first when ascending

            # Biosign column (🌿 / '') ───────────────────────────────
            if col_index == 3:
                return 0 if cell else 1      # 🛬 rows first when ascending

            # Mineral columns – strip the “ %” and convert ────────────
            if numeric:
                value = cell.replace("%", "").strip()
                try:
                    return float(value)
                except ValueError:
                    return -1.0              # blank cells sort last
            return cell

        # Retrieve, sort, and re-order the children
        children = list(self.get_children(""))
        children.sort(key=sort_key, reverse=self.sort_reverse)
        for index, iid in enumerate(children):
            self.move(iid, "", index)

    # ------------------------------------------------------------------
    def _on_motion(self, event):
        """Show tooltip with full mineral name when mouse hovers header."""
        if self.identify_region(event.x, event.y) != "heading":
            self._hide_tip()
            return

        # visible column index (#1, #2, …)
        col_tag = self.identify_column(event.x)     # e.g. "#3"
        try:
            vis_idx = int(col_tag.lstrip("#")) - 1
        except ValueError:
            self._hide_tip()
            return

        # which column key is that in the current display set?
        disp_cols = self["displaycolumns"]          # tuple: body, land, …
        if vis_idx >= len(disp_cols):
            self._hide_tip()
            return

        col_key = disp_cols[vis_idx]                # "body" | "land" | mineral
        if col_key not in RAW_MATS:                 # ignore non-mineral headers
            self._hide_tip()
            return

        # already showing correct tooltip?
        if self._tip_col == col_key:
            return

        # show / move tooltip
        self._show_tip(col_key, event)

    # ------------------------------------------------------------------
    def _show_tip(self, mineral, event):
        self._hide_tip()                         # hide any existing tip
        self._tip_col = mineral
        text = self._col2name[mineral]
        self._tip = _Tip(self, text)
        x = self.winfo_rootx() + event.x + 15
        y = self.winfo_rooty() - 25
        self._tip.show(x, y)

    def _hide_tip(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None
            self._tip_col = None
