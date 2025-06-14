import wx
import wx.grid as gridlib
from typing import Dict, Callable, Optional

from EDXD.model import Body
from EDXD.globals import SYMBOL, logging, RAW_MATS
import inspect, functools

TABLE_ICONS = {
    "status_header": "🎯🖱",
    "status_target": "🎯",
    "status_selected": "🖱",
    "landable": "🛬",
    "biosigns": "🌿",
    "geosigns": "🌋",
    "value": "🔍💲"
}

def log_call(level=logging.INFO):
    """Logs qualified name plus bound arguments, even for inner functions."""
    def deco(fn):
        logger = logging.getLogger(fn.__module__)
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            arglist = ", ".join(f"{k}={v!r}" for k, v in bound.arguments.items())
            qualname = fn.__qualname__           # includes outer.<locals>.inner
            logger.log(level, "%s(%s)", qualname, arglist)
            return fn(*args, **kwargs)
        return wrapper
    return deco


class BodiesTable(gridlib.Grid):
    """Table with Status | Body | 🛬 | 🌿 | 🌋 | one column per mineral."""
    @log_call()
    def __init__(self, parent, on_select: Callable[[str], None]):
        super().__init__(parent)
        self._all_cols = ["status", "body", "distance", "land", "bio", "geo", "value"] + list(RAW_MATS)
        # At the top of your class, after self._all_cols:
        self._headers = {
            "status": TABLE_ICONS["status_header"],
            "body": "Body",
            "distance": "Distance",
            "land": TABLE_ICONS["landable"],
            "bio": TABLE_ICONS["biosigns"],
            "geo": TABLE_ICONS["geosigns"],
            "value": TABLE_ICONS["value"]
        }
        self.CreateGrid(0, len(self._all_cols))
        self.SetRowLabelSize(0)
        self.SetSelectionMode(gridlib.Grid.SelectRows)
        self.DisableDragGridSize()  # Prevents grid line drag-resizing
        self.EnableDragRowSize(False)  # Disables row resizing
        #self.EnableDragColSize(False)  # Disables column resizing
        self.EnableEditing(False)  # Already in your code
        self.ClearSelection()  # To clear any selection if needed
        self._col2name = {mat: mat.title() for mat in RAW_MATS}
        self._col2name.update({
            "distance": "Distance from entry point",
            "land": "Landable",
            "bio": "Bio-signals",
            "geo": "Geo-signals",
            "value": "Estimated value"
        })

        for idx, col in enumerate(self._all_cols):
            self.SetColLabelValue(idx, self._headers.get(col, SYMBOL.get(col, col[:2].title())))
            if col == "status":
                self.SetColSize(idx, 44)
            elif col == "body":
                self.SetColSize(idx, 250)
            elif col == "distance" or col == "value":
                self.SetColSize(idx, 80)
            elif col in ("land", "bio", "geo"):
                self.SetColSize(idx, 40)
            else:
                self.SetColSize(idx, 60)
        # Sorting
        self.sort_col: Optional[str] = "body"
        self.sort_reverse: bool = False
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self._on_label_click)
        # Selection
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self._on_select)
        self._on_select_cb = on_select
        # Tooltips
        self._tip_win = None
        self._tip_col = None
        self.Bind(wx.EVT_MOTION, self._on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._hide_tip)
        self.Bind(gridlib.EVT_GRID_RANGE_SELECT, self._on_range_select)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _on_label_click(self, event):
        # Use the displayed columns for correct column mapping
        col = event.GetCol()
        colname = self._display_cols[col]
        if self.sort_col == colname:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = colname
            self.sort_reverse = (colname in RAW_MATS or colname in ("value", "bio", "geo"))
        self._refresh_sort()
        event.Skip()

    def _on_select(self, event):
        row = event.GetRow()
        # Always clear any multi-selection, then select only this row
        self.ClearSelection()
        self.SelectRow(row)
        if 0 <= row < self.GetNumberRows():
            body_name = self.GetCellValue(row, self._all_cols.index("body"))
            if body_name and self._on_select_cb:
                self._on_select_cb(body_name)
        event.Skip()

    def _on_range_select(self, event):
        if event.Selecting() and event.GetTopRow() != event.GetBottomRow():
            # Block multi-row selection
            event.Veto()  # Prevents the selection
            # Optionally, select just the row under the mouse:
            self.ClearSelection()
            self.SelectRow(event.GetTopRow())
        else:
            event.Skip()

    def _on_key_down(self, event):
        if event.ShiftDown() or event.ControlDown():
            # Block shift/ctrl multi-select
            return  # Ignore event
        event.Skip()

    @log_call()
    def refresh(
            self,
            bodies: Dict[str, Body],
            filters: Dict[str, bool],
            landable_only: bool,
            selected_name: str,
            target_name: str,
    ):
        visible_mats = [m for m, on in filters.items() if on]
        display_cols = ["status", "body", "distance", "land", "bio", "geo", "value"] + visible_mats

        needed_cols = len(display_cols)
        current_cols = self.GetNumberCols()
        if current_cols < needed_cols:
            self.AppendCols(needed_cols - current_cols)
        elif current_cols > needed_cols:
            self.DeleteCols(0, current_cols - needed_cols)
        for i, colname in enumerate(display_cols):
            self.SetColLabelValue(i, self._headers.get(colname, SYMBOL.get(colname, colname[:2].title())))
            if colname == "status":
                self.SetColSize(i, 44)
            elif colname == "body":
                self.SetColSize(i, 250)
            elif colname in ("distance", "value"):
                self.SetColSize(i, 80)
            elif colname in ("land", "bio", "geo"):
                self.SetColSize(i, 40)
            else:
                self.SetColSize(i, 60)

        # 1. PREPARE ROW DATA AS LIST OF DICTS (column name -> (disp, raw) tuple)
        rows_data = []
        for name, body in bodies.items():
            if landable_only and not getattr(body, "landable", False):
                continue

            row = {
                "status": (TABLE_ICONS["status_header"] if name == target_name == selected_name
                           else TABLE_ICONS["status_target"] if name == target_name
                else TABLE_ICONS["status_selected"] if name == selected_name
                else "", 0),
                "body": (name, name.lower()),
                "distance": (f"{getattr(body, 'distance', 0):,.0f} Ls", getattr(body, 'distance', 0)),
                "land": (f"{TABLE_ICONS['landable']}"                                   if getattr(body, "landable", False)    else "", (0 if getattr(body, "landable", False)  else 1)),
                "bio": (f"{TABLE_ICONS['biosigns']} {getattr(body, 'biosignals', 0)}"   if getattr(body, "biosignals", 0) > 0  else "", getattr(body, "biosignals", 0)),
                "geo": (f"{TABLE_ICONS['geosigns']} {getattr(body, 'geosignals', 0)}"   if getattr(body, "geosignals", 0) > 0  else "", getattr(body, "geosignals", 0)),
                "value": (f"{getattr(body, 'estimated_value', 0):,} Cr"                 if getattr(body, "estimated_value", 0) else "", getattr(body, "estimated_value", 0)),
            }
            for m in visible_mats:
                matval = body.materials.get(m, None)
                row[m] = (f"{matval:.1f} %" if matval is not None else "", matval if matval is not None else -1.0)
            rows_data.append(row)

        needed_rows = len(rows_data)
        current_rows = self.GetNumberRows()
        if current_rows < needed_rows:
            self.AppendRows(needed_rows - current_rows)
        elif current_rows > needed_rows:
            self.DeleteRows(0, current_rows - needed_rows)

        # 2. STORE rows_data FOR SORTING
        self._display_cols = display_cols
        self._rows_data = rows_data

        # 3. FILL VISIBLE DATA
        for r, row in enumerate(rows_data):
            for c, colname in enumerate(display_cols):
                self.SetCellValue(r, c, row.get(colname, ("", ""))[0])

        for r in range(len(rows_data), self.GetNumberRows()):
            for c in range(self.GetNumberCols()):
                self.SetCellValue(r, c, "")

        if hasattr(self, "_refresh_sort"):
            self._refresh_sort()

    def _refresh_sort(self):
        if not self.sort_col:
            return

        # Sort by the visible column (self.sort_col) using the raw value
        def sort_key(row):
            val = row.get(self.sort_col, ("", None))
            raw = val[1]
            if raw is None:
                if self.sort_col in RAW_MATS:
                    return -1.0
                return ""
            return raw

        sorted_rows = sorted(self._rows_data, key=sort_key, reverse=self.sort_reverse)
        for r, row in enumerate(sorted_rows):
            for c, colname in enumerate(self._display_cols):
                self.SetCellValue(r, c, row.get(colname, ("", ""))[0])

    def _on_motion(self, event):
        x, y = event.GetPosition()
        col = self.XToCol(x)
        if col < 0 or col >= self.GetNumberCols():
            self._hide_tip(event)
            return
        colname = self.GetColLabelValue(col)
        if self._tip_col == colname:
            return
        self._hide_tip(event)
        text = self._col2name.get(self.sort_col, colname)
        if text:
            self._tip_win = wx.TipWindow(self, text, maxLength=120)
            self._tip_col = colname

    def _hide_tip(self, event=None):
        if self._tip_win:
            self._tip_win.Close()
            self._tip_win = None
            self._tip_col = None


