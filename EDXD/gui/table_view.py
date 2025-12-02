import inspect
from typing import Dict, Callable, Optional

import wx
import wx.grid as gridlib

from EDXD.data_handler.model import Body
from EDXD.globals import SYMBOL, logging, RAW_MATS, ICONS, log_call, DEBUG_MODE, log_context, \
    DEFAULT_WORTHWHILE_THRESHOLD
from EDXD.utils.clipboard import copy_text_to_clipboard


class BodiesTable(gridlib.Grid):
    """Table with Status | Body | 🛬 | 🌿 | 🌋 | one column per mineral."""
    #@log_call()
    def __init__(self, parent, on_select: Callable[[str], None]):
        super().__init__(parent)
        self._all_cols = ["body_id", "status", "body_type", "scoopable", "body", "distance", "land", "first_footfalled",
                          "bio", "geo", "value", "worthwhile", "first_discovered", "mapped", "first_mapped"] + list(
            RAW_MATS)
        # At the top of your class, after self._all_cols:
        self._headers = {
            "body_id"           : "BodyID",
            "status"            : ICONS["status_header"],
            "body_type"         : "Type",
            "scoopable"         : ICONS["scoopable"],
            "body"              : "Body",
            "distance"          : "Distance",
            "land"              : ICONS["landable"],
            "first_footfalled"  : ICONS["col_first_footfalled"],
            "bio"               : ICONS["biosigns"],
            "geo"               : ICONS["geosigns"],
            "value"             : ICONS["value"],
            "worthwhile"        : ICONS["worthwhile"],
            "first_discovered"  : ICONS["col_first_discovered"],
            "mapped"            : ICONS["mapped"],
            "first_mapped"      : ICONS["col_first_mapped"]
        }

        self._display_cols = None
        self._rows_data = None

        self.CreateGrid(0, len(self._all_cols))
        self.SetRowLabelSize(0)
        self.SetSelectionMode(gridlib.Grid.SelectRows)
        self.DisableDragGridSize()  # Prevents grid line drag-resizing
        self.EnableDragRowSize(False)  # Disables row resizing
        self.EnableDragColSize(False)  # Disables column resizing
        self.EnableEditing(False)  # Already in your code
        self.ClearSelection()  # To clear any selection if needed
        self._col2name = {mat: mat.title() for mat in RAW_MATS}
        self._col2name.update({
            "body_id"           : "BodyID",
            "status"            : "Selected or targeted",
            "body_type"         : "Type of body or star",
            "scoopable"         : "Star is scoopable",
            "body"              : "Bodies in current system",
            "distance"          : "Distance from entry point",
            "land"              : "Landable",
            "first_footfalled"  : "First footfall",
            "bio"               : "Bio-signals",
            "geo"               : "Geo-signals",
            "value"             : "Estimated value",
            "worthwhile"        : "Worthwhile mapping data",
            "first_discovered"  : "First discovered",
            "mapped"            : "Body was mapped",
            "first_mapped"      : "First mapped"
        })

        self._prepare_columns(display_cols=self._all_cols)

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
        self.Bind(gridlib.EVT_GRID_RANGE_SELECT, self._on_range_select)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.GetGridColLabelWindow().Bind(wx.EVT_MOTION, self._show_tip)
        self.loading = True

        # Bind double-click for copying body name:
        # Prefer the grid's cell double-click event, but also bind the generic mouse double-click as a fallback.
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self._on_table_double_click)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_table_double_click)

    def _show_tip(self, event):
        x = event.GetX()
        col = self.XToCol(x)
        colname = self._display_cols[col] if hasattr(self, "_display_cols") else self._all_cols[col]
        text = self._col2name.get(colname, colname)
        tt = wx.ToolTip(text)
        self.GetGridColLabelWindow().SetToolTip(tt)

    def _on_label_click(self, event):
        # Use the displayed columns for correct column mapping
        col = event.GetCol()
        colname = self._display_cols[col]
        if colname in ["status", "body_type", "scoopable", "body_id"]:
            event.Skip()
            return
        if self.sort_col == colname:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = colname
            self.sort_reverse = (colname in RAW_MATS or colname in ("value", "bio", "geo", "worthwhile", "mapped",
                                                                    "first_discovered", "first_mapped",
                                                                    "first_footfalled"))
        self._refresh_sort()
        event.Skip()

    def _on_select(self, event):
        row = event.GetRow()
        # Always clear any multi-selection, then select only this row
        self.SelectRow(row)
        if 0 <= row < self.GetNumberRows():
            body_id = self.GetCellValue(row, self._all_cols.index("body_id"))
            if self._on_select_cb:
                self.loading = False
                self._on_select_cb(body_id)
        self.ClearSelection()
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

    @staticmethod
    def _on_key_down(event):
        if event.ShiftDown() or event.ControlDown():
            # Block shift/ctrl multi-select
            return  # Ignore event
        event.Skip()

    @log_call(logging.DEBUG)
    def refresh(
            self,
            bodies: Dict[str, Body],
            filters: Dict[str, bool],
            landable_only: bool,
            selected_body_id: str,
            target_body_id: str
    ):
        visible_mats = [m for m, on in filters.items() if on]
        display_cols = ["body_id", "status", "body_type", "scoopable", "body", "distance", "land", "first_footfalled",
                        "bio", "geo", "value", "worthwhile", "first_discovered", "mapped",
                        "first_mapped"] + visible_mats

        needed_cols = len(display_cols)
        current_cols = self.GetNumberCols()
        if current_cols < needed_cols:
            self.AppendCols(needed_cols - current_cols)
        elif current_cols > needed_cols:
            self.DeleteCols(0, current_cols - needed_cols)
        self._prepare_columns(display_cols=display_cols)

        # Align value and distance columns to right
        for i, colname in enumerate(display_cols):
            if colname in ["body", "body_type"]:
                attr_left = gridlib.GridCellAttr()
                attr_left.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self.SetColAttr(i, attr_left)
            elif colname in ("land", "bio", "geo", "status", "scoopable", "worthwhile", "mapped", "first_discovered",
                             "first_mapped", "first_footfalled"):
                attr_center = gridlib.GridCellAttr()
                attr_center.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self.SetColAttr(i, attr_center)
            else:
                attr_right = gridlib.GridCellAttr()
                attr_right.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
                self.SetColAttr(i, attr_right)


        # 1. PREPARE ROW DATA AS LIST OF DICTS (column name -> (disp, raw) tuple)
        rows_data = []
        for body_id, body in bodies.items():
            if landable_only and not getattr(body, "landable", False):
                continue
            try:
                row = {
                    "body_id":  (body_id, body_id if body_id is not None else ""),
                    "status":   (ICONS["status_header"] if body.body_id == target_body_id == selected_body_id
                                else ICONS["status_target"] if body.body_id == target_body_id
                                else ICONS["status_selected"] if body.body_id == selected_body_id
                                else "", 0),
                    "body_type": (f"{str(getattr(body, 'body_type', ''))}", str(getattr(body, 'body_type', '')).lower()),
                    "scoopable": (f"{ICONS['scoopable']}"                               if getattr(body, "scoopable", False) else "",               (0 if getattr(body, "scoopable", False) else 1)),
                    "body": (body.body_name, body.body_name.lower()),
                    "distance": (f"{getattr(body, 'distance', 0):,.0f} Ls"              if getattr(body, 'distance', 0) is not None else "",        getattr(body, 'distance', 0)),
                    "land": (f"{ICONS['landable']}"                                     if getattr(body, "landable", False)    else "",             (0 if getattr(body, "landable", False)  else 1)),
                    "bio":  (f"{ICONS['biosigns']}{ICONS['checked']}" if getattr(body, "bio_complete", False)
                            else f"{ICONS['biosigns']} {getattr(body, 'bio_scanned', 0)}/{getattr(body, 'biosignals', 0)}" if getattr(body, "biosignals", 0) > 0
                            else "", getattr(body, "biosignals", 0)),
                    "geo":  (f"{ICONS['geosigns']}{ICONS['checked']}" if getattr(body, "geo_complete", False)
                            else f"{ICONS['geosigns']} {getattr(body, 'geo_scanned', 0)}/{getattr(body, 'geosignals', 0)}" if getattr(body, "geosignals", 0) > 0
                            else "", getattr(body, "geosignals", 0)),
                    "value": (f"{getattr(body, 'estimated_value', 0):,} Cr"             if getattr(body, "estimated_value", 0) else "",             getattr(body, "estimated_value", 0)),
                    "worthwhile": (f"{ICONS["worthwhile"]}"                             if getattr(body, "estimated_value", 0) >= self.Parent.prefs.get("worthwhile_threshold", DEFAULT_WORTHWHILE_THRESHOLD) else "",  getattr(body, "estimated_value", 0)),
                    "mapped": (f"{ICONS['mapped']}"                                     if getattr(body, "mapped", False) else "",                  (1 if getattr(body, "mapped", False) else 0)),
                    "first_discovered": (
                        f"{ICONS["first_discovered"]}" if getattr(body, "first_discovered", 0) == 2 else (
                            f"{ICONS["previous_discovered"]}" if getattr(body, "first_discovered", 0) == 1 else ""),
                        getattr(body, "first_discovered", 0)),
                    "first_mapped": (f"{ICONS["first_mapped"]}" if getattr(body, "first_mapped", 0) == 2 else (
                        f"{ICONS["previous_mapped"]}" if getattr(body, "first_mapped", 0) == 1 else ""),
                                     getattr(body, "first_mapped", 0)),
                    "first_footfalled": (
                        f"{ICONS["first_footfalled"]}" if getattr(body, "first_footfalled", 0) == 2 else (
                            f"{ICONS["previous_footfalled"]}" if getattr(body, "first_footfalled", 0) == 1 else ""),
                        getattr(body, "first_footfalled", 0)),

                }
                for m in visible_mats:
                    matval = body.materials.get(m, None)
                    row[m] = (f"{matval:.1f} %" if matval is not None else "", matval if matval is not None else -1.0)
                rows_data.append(row)
            except Exception as e:
                log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
                logging.error(f"{getattr(body, 'distance', 0)} Ls")


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
                # todo: remove try... col handling needs to be fixed
                try:
                    self.SetCellValue(r, c, row.get(colname, ("", ""))[0])
                except Exception as e:
                    log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
                    logging.error(f"Failed to set value to {colname}(row[{r}]:col[{c}])")


        for r in range(len(rows_data), self.GetNumberRows()):
            for c in range(self.GetNumberCols()):
                self.SetCellValue(r, c, "")

        if hasattr(self, "_refresh_sort"):
            self._refresh_sort()
        self.ClearSelection()

    def _refresh_sort(self):
        if not self.sort_col:
            return

        # Sort by the visible column (self.sort_col) using the raw value
        def sort_key(sort_row):
            val = sort_row.get(self.sort_col, ("", None))
            raw = val[1]
            if raw is None:
                if self.sort_col in RAW_MATS:
                    return -1.0
                return ""
            return raw

        sorted_rows = sorted(self._rows_data, key=sort_key, reverse=self.sort_reverse)
        for r, row in enumerate(sorted_rows):
            for c, colname in enumerate(self._display_cols):
                # todo: remove try... col handling needs to be fixed
                try:
                    self.SetCellValue(r, c, row.get(colname, ("", ""))[0])
                except Exception as e:
                    log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
                    logging.error(f"Failed to set value to {colname}(row[{r}]:col[{c}])")

    def _prepare_columns(self, display_cols):
        for i, colname in enumerate(display_cols):
            self.SetColLabelValue(i, self._headers.get(colname, SYMBOL.get(colname, colname[:2].title())))

            if colname == "status":
                self.SetColSize(i, 44)
            elif colname == "body_type":
                self.SetColSize(i, 222)
            elif colname == "body":
                self.SetColSize(i, 275)
            elif colname in ("distance"):
                self.SetColSize(i, 80)
            elif colname in ("bio", "geo"):
                self.SetColSize(i, 60)
            elif colname == "value":
                self.SetColSize(i, 100)
            elif colname in ("land", "scoopable", "worthwhile", "mapped", "first_discovered", "first_mapped",
                             "first_footfalled"):
                self.SetColSize(i, 30)
            elif colname == "body_id":
                self.SetColSize(i, 50 if DEBUG_MODE else 0)
            else:
                self.SetColSize(i, 60)

    def _plain_name_from_label(self, raw: str) -> str:
        if not raw:
            return raw
        if " (" in raw:
            raw = raw.split(" (", 1)[0]
        if " - " in raw:
            raw = raw.split(" - ", 1)[0]
        return raw.strip()

    def _on_table_double_click(self, evt: wx.Event):
        """
        Copy the body name from the clicked row/cell.
        Handles both Grid cell-double-click events and generic mouse double-clicks.
        """
        name = None
        index = None

        # 1) If this is a Grid cell event, try to get row/col directly from the event
        row = None
        col = None
        try:
            # gridlib.Grid cell events expose GetRow/GetCol
            row = evt.GetRow()
            col = evt.GetCol()
            index = row
        except Exception:
            # not a grid cell event; try to derive from mouse position
            try:
                pos = evt.GetPosition()
                row = self.YToRow(pos.y)
                col = self.XToCol(pos.x)
                index = row
            except Exception:
                row = None
                col = None

        # If we have a valid row, try to copy the 'body' column if present, else fall back to the clicked cell
        if row is not None and row >= 0:
            try:
                # Prefer the 'body' display column
                if hasattr(self, "_display_cols") and self._display_cols and "body" in self._display_cols:
                    body_col = self._display_cols.index("body")
                    val = self.GetCellValue(row, body_col)
                    if val and val.strip():
                        name = self._plain_name_from_label(val)

                # If that didn't yield a name, try the clicked column
                if not name and col is not None and col >= 0:
                    val = self.GetCellValue(row, col)
                    if val and val.strip():
                        name = self._plain_name_from_label(val)

                # Final fallback: first non-empty cell in the row
                if not name:
                    for c in range(self.GetNumberCols()):
                        try:
                            val = self.GetCellValue(row, c)
                            if val and val.strip():
                                name = self._plain_name_from_label(val)
                                break
                        except Exception:
                            continue
            except Exception:
                pass

        # Fallback: use stored rows_data (the internal data used for rendering) to get the body display
        if not name:
            try:
                if hasattr(self, "_rows_data") and index is not None and 0 <= index < len(self._rows_data):
                    row_data = self._rows_data[index]
                    candidate = ""
                    if isinstance(row_data, dict):
                        candidate = row_data.get("body", ("", ""))[0] or row_data.get("body_id", ("", ""))[0]
                    if candidate:
                        name = self._plain_name_from_label(candidate)
            except Exception:
                pass

        # Final fallback: if a get_row_object mapping exists, prefer that (keeps parity with the previous approach)
        if not name:
            try:
                if hasattr(self, "get_row_object"):
                    row_obj = self.get_row_object(index)
                    if row_obj:
                        name = getattr(row_obj, "name", None) or getattr(row_obj, "body_name", None)
            except Exception:
                pass

        if name:
            copy_text_to_clipboard(name)

        evt.Skip()
