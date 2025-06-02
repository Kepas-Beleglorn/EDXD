from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional

from model import Body
from gui.config_panel import RAW_MATS

# symbol lookup (feel free to extend)
SYMBOL = {
    "antimony":   "Sb", "arsenic":    "As", "boron":     "B",  "cadmium": "Cd",
    "carbon":     "C",  "chromium":   "Cr", "germanium": "Ge", "iron": "Fe",
    "lead":       "Pb", "manganese":  "Mn", "mercury":   "Hg", "molybdenum": "Mo",
    "nickel":     "Ni", "niobium":    "Nb", "phosphorus":"P",  "polonium": "Po",
    "rhenium":    "Re", "ruthenium":  "Ru", "selenium":  "Se", "sulphur": "S",
    "technetium":"Tc", "tellurium":  "Te", "tin":       "Sn","tungsten":"W",
    "vanadium":   "V",  "yttrium":    "Y",  "zinc":      "Zn","zirconium":"Zr",
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
    """Table with Status | Body | 🛬 | 🌿 | 🌋 | one column per mineral."""

    def __init__(self, master, on_select: Callable[[str], None]):
        # define the fixed column order
        self._all_cols = ("status", "body", "land", "bio", "geo") + tuple(RAW_MATS)
        super().__init__(master, columns=self._all_cols, show="headings", height=18)

        # Status column (not sortable)
        self.heading("status", text="🎯🖱")
        self.column("status", width=40, anchor="center")

        # Body column
        self.heading("body", text="Body", command=lambda: self._sort_by("body"))
        self.column("body", width=300, anchor="w")

        # Landable column
        self.heading("land", text="🛬", command=lambda: self._sort_by("land"))
        self.column("land", width=40, anchor="center")

        # Bio-signals column
        self.heading("bio", text="🌿", command=lambda: self._sort_by("bio"))
        self.column("bio", width=40, anchor="center")

        # Geo-signals column
        self.heading("geo", text="🌋", command=lambda: self._sort_by("geo"))
        self.column("geo", width=40, anchor="center")


        # Mineral columns (sortable by their key)
        for mat in RAW_MATS:
            sym = SYMBOL.get(mat, mat[:2].title())
            self.heading(mat, text=sym, command=lambda m=mat: self._sort_by(m))
            self.column(mat, width=60, anchor="e")

        # Tooltip support for mineral headers
        # build a map of column key → tooltip text
        self._col2name: Dict[str, str] = {}
        self._col2name = {mat: mat.title() for mat in RAW_MATS}
        self._col2name["land"] = "Landable"
        self._col2name["bio"] = "Bio-signals"
        self._col2name["geo"] = "Geo-signals"
        self._tip = None
        self._tip_col = None
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._hide_tip())

        # sort state
        self.sort_col: Optional[str] = None
        self.sort_reverse = False

        # row-select callback
        self.bind("<<TreeviewSelect>>",
                  lambda e: on_select(self.selection()[0]) if self.selection() else None)

    # ------------------------------------------------------------------
    def _sort_by(self, col: str):
        """Set or toggle the sort column/direction, then ask MainWindow to refresh."""
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            # Minerals, bio, geo sort descending first; others ascend
            self.sort_reverse = (col in RAW_MATS or col in ("bio", "geo"))
        self.event_generate("<<EdmSortRequest>>")

    # ------------------------------------------------------------------
    def refresh(
        self,
        *,
        bodies: Dict[str, Body],
        filters: Dict[str, bool],
        landable_only: bool,
        selected_name: str,
        target_name: str,
    ):
        """
        Update all rows and columns.
        - `bodies`: map of bodyName → Body
        - `filters`: map mineral→bool (visible minerals)
        - `landable_only`: if True, skip bodies with body.landable==False
        - `selected_name`: clicked-in-GUI body
        - `target_name`: in-game target from Status.json
        """
        # 1) decide which mineral columns are currently visible
        visible_mats = [m for m, on in filters.items() if on]

        # 2) set displaycolumns in order: status, body, land, bio, geo, <minerals>
        display = ("status", "body", "land", "bio", "geo") + tuple(visible_mats)
        self["displaycolumns"] = display

        # 3) update/create rows
        existing = set(self.get_children())
        for name, body in bodies.items():
            if landable_only and not body.landable:
                continue

            status_icon = (
                "🎯🖱"
                if name == target_name == selected_name
                else "🎯"
                if name == target_name
                else "🖱"
                if name == selected_name
                else ""
            )

            # Construct a full-length row, one cell per column in _all_cols
            row = [
                status_icon,
                name,
                "🛬" if body.landable else "",
                f"🌿 {getattr(body, 'biosignals', 0)}"
                if getattr(body, "biosignals", 0)
                else "",
                f"🌋 {getattr(body, 'geosignals', 0)}"
                if getattr(body, "geosignals", 0)
                else "",
            ] + [
                f"{body.materials.get(m,0):.1f} %"
                if m in body.materials
                else ""
                for m in RAW_MATS
            ]

            if name in existing:
                self.item(name, values=row)
                existing.remove(name)
            else:
                self.insert("", "end", iid=name, values=row)

        for iid in existing:
            self.delete(iid)

        # 4) apply sorting if requested
        if self.sort_col:
            try:
                idx = self._all_cols.index(self.sort_col)
            except ValueError:
                idx = 0
            numeric = self.sort_col in RAW_MATS or self.sort_col in ("bio", "geo")
            self._apply_sort(idx, numeric)

    # ------------------------------------------------------------------
    def _apply_sort(self, col_index: int, numeric: bool):
        """Reorder rows based on the chosen column index & type (numeric vs text)."""

        def sort_key(iid):
            cell = self.set(iid, column=col_index)
            # Body column → alphabetical
            if self._all_cols[col_index] == "body":
                return cell.lower()
            # Landable → place 🛬 rows first
            if self._all_cols[col_index] == "land":
                return 0 if cell else 1
            # Bio → place 🌿 rows first
            if self._all_cols[col_index] == "bio":
                return 0 if cell else 1
            # Geo → place 🌋 rows first
            if self._all_cols[col_index] == "geo":
                return 0 if cell else 1
            # Mineral columns → strip " %" and convert to float
            if numeric:
                val = cell.replace("%", "").strip()
                try:
                    return float(val)
                except ValueError:
                    return -1.0
            return cell

        children = list(self.get_children(""))
        children.sort(key=sort_key, reverse=self.sort_reverse)
        for position, iid in enumerate(children):
            self.move(iid, "", position)

    # ------------------------------------------------------------------
    def _on_motion(self, event):
        """Show tool-tip when hovering any header (mineral only)."""
        if self.identify_region(event.x, event.y) != "heading":
            self._hide_tip()
            return

        col_tag = self.identify_column(event.x)  # e.g. "#3"
        try:
            idx = int(col_tag.lstrip("#")) - 1
        except ValueError:
            self._hide_tip()
            return

        # only minerals were checked before; now include land/bio/geo
        disp_cols = self["displaycolumns"]
        if idx < 0 or idx >= len(disp_cols):
            self._hide_tip()
            return

        col_key = disp_cols[idx]
        if col_key not in self._col2name:
            self._hide_tip()
            return

        if self._tip_col == col_key:
            return

        # Show the tooltip with full name
        self._show_tip(col_key, event)

    # ------------------------------------------------------------------
    def _show_tip(self, col_key: str, event):
        self._hide_tip()
        self._tip_col = col_key
        text = self._col2name.get(col_key, "")
        self._tip = _Tip(self, text)
        x = self.winfo_rootx() + event.x + 15
        y = self.winfo_rooty() - 25
        self._tip.show(x, y)

    def _hide_tip(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None
            self._tip_col = None
