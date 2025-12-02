"""
Example wxPython TextCtrl validator that only accepts floating-point numbers
and enforces a specified numeric range (useful for latitude/longitude).

Usage:
- Attach FloatRangeValidator(min_val=-90, max_val=90) to a TextCtrl for latitude.
- Attach FloatRangeValidator(min_val=-180, max_val=180) to a TextCtrl for longitude.

This validator:
- Filters most illegal keystrokes (only digits, one leading '-', one '.', navigation keys).
- Sanitizes pasted text to keep only a valid partial float format.
- Performs full validation on focus loss / when wx.Validator.Validate() is called:
    - Ensures the text is a valid float (no scientific notation).
    - Ensures the float lies within the provided [min_val, max_val] range.
"""
import re

import wx

_PARTIAL_FLOAT_RE = re.compile(r"^-?\d*\.?\d*$")      # allowed intermediate states (partial typing)
_FULL_FLOAT_RE = re.compile(r"^-?\d+(\.\d+)?$")       # full float (no exponent)


class FloatRangeValidator(wx.Validator):
    def __init__(self, min_val=None, max_val=None, allow_empty=False):
        """
        min_val, max_val: numeric bounds (inclusive). Use None for unbounded.
        allow_empty: whether empty string is permitted.
        """
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.allow_empty = allow_empty
        # Bind events in Clone/Init pattern
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_TEXT, self.OnText)

    def Clone(self):
        # Required by wx.Validator
        return FloatRangeValidator(self.min_val, self.max_val, self.allow_empty)

    def Validate(self, win):
        """Called by wx's validation system (e.g. panel.Validate())."""
        tc = self.GetWindow()
        if not isinstance(tc, wx.TextCtrl):
            return True

        text = tc.GetValue().strip()
        if text == "":
            if self.allow_empty:
                return True
            else:
                wx.Bell()
                tc.SetBackgroundColour(wx.Colour(255, 220, 220))
                tc.Refresh()
                return False

        if not _FULL_FLOAT_RE.match(text):
            wx.Bell()
            tc.SetBackgroundColour(wx.Colour(255, 220, 220))
            tc.Refresh()
            return False

        try:
            val = float(text)
        except ValueError:
            wx.Bell()
            tc.SetBackgroundColour(wx.Colour(255, 220, 220))
            tc.Refresh()
            return False

        if (self.min_val is not None and val < self.min_val) or (self.max_val is not None and val > self.max_val):
            wx.Bell()
            tc.SetBackgroundColour(wx.Colour(255, 220, 220))
            tc.Refresh()
            return False

        # valid => reset background and return True
        tc.SetBackgroundColour(wx.NullColour)
        tc.Refresh()
        return True

    def TransferToWindow(self):
        # nothing special to transfer
        return True

    def TransferFromWindow(self):
        # nothing special to transfer
        return True

    def OnChar(self, event):
        """Filter keystrokes:
         - Allow digits.
         - Allow one leading '-' at position 0.
         - Allow one '.' (decimal point).
         - Allow navigation keys, Ctrl+C/Ctrl+V/Ctrl+X, etc.
        """
        keycode = event.GetKeyCode()

        # allow navigation and control keys through
        if keycode < 256:
            ch = chr(keycode)
        else:
            ch = ""

        # Control keys (arrows, delete, backspace, tab, enter)
        if keycode in (wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_HOME, wx.WXK_END, wx.WXK_TAB, wx.WXK_RETURN):
            event.Skip()
            return

        # Allow Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A
        if event.ControlDown():
            event.Skip()
            return

        # Allow digits
        if ch.isdigit():
            event.Skip()
            return

        tc = self.GetWindow()
        text = tc.GetValue()
        sel_start, sel_end = tc.GetSelection()

        # '-' allowed only at start (position 0) and if not already present
        if ch == "-":
            # If there is an active selection that includes the leading char, handle normally
            if "-" in text and not (sel_start == 0 and sel_end > 0):
                wx.Bell()
                return
            # allow '-' only if insertion point is at 0
            if tc.GetInsertionPoint() != 0:
                wx.Bell()
                return
            event.Skip()
            return

        # '.' allowed only once
        if ch == ".":
            if "." in text and not (sel_start < text.find(".") < sel_end):
                wx.Bell()
                return
            event.Skip()
            return

        # Everything else: block
        wx.Bell()
        # do not call event.Skip() -> character is eaten

    def OnText(self, event):
        """
        Handle pasted text and other programmatic changes by sanitizing the TextCtrl content
        into a legal partial float form (keeps a leading '-', at most one '.', digits).
        We allow empty string if configured.
        """
        tc = self.GetWindow()
        raw = tc.GetValue()

        # Quick accept for already-valid partial-form text
        if raw == "" and self.allow_empty:
            event.Skip()
            return
        if _PARTIAL_FLOAT_RE.match(raw):
            event.Skip()
            return

        # Otherwise sanitize: keep digits, at most one leading '-', at most one '.'
        cleaned = []
        seen_dot = False
        seen_minus = False
        for i, ch in enumerate(raw):
            if ch.isdigit():
                cleaned.append(ch)
            elif ch == "." and not seen_dot:
                cleaned.append(ch)
                seen_dot = True
            elif ch == "-" and not seen_minus and len(cleaned) == 0 and i == 0:
                cleaned.append(ch)
                seen_minus = True
            # ignore everything else

        new = "".join(cleaned)
        if new != raw:
            # replace text but try to preserve insertion point sensibly
            ins = tc.GetInsertionPoint()
            tc.ChangeValue(new)
            tc.SetInsertionPoint(min(ins, len(new)))
        event.Skip()


# Demo application to show usage
class DemoFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="FloatRangeValidator demo", size=(420, 200))
        panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        fg = wx.FlexGridSizer(2, 2, 10, 10)
        fg.AddGrowableCol(1, 1)

        lbl_lat = wx.StaticText(panel, label="Latitude (-90..90):")
        self.tc_lat = wx.TextCtrl(panel, validator=FloatRangeValidator(min_val=-90.0, max_val=90.0))
        fg.Add(lbl_lat, 0, wx.ALIGN_CENTER_VERTICAL)
        fg.Add(self.tc_lat, 1, wx.EXPAND)

        lbl_lon = wx.StaticText(panel, label="Longitude (-180..180):")
        self.tc_lon = wx.TextCtrl(panel, validator=FloatRangeValidator(min_val=-180.0, max_val=180.0))
        fg.Add(lbl_lon, 0, wx.ALIGN_CENTER_VERTICAL)
        fg.Add(self.tc_lon, 1, wx.EXPAND)

        sizer.Add(fg, 1, wx.ALL | wx.EXPAND, 20)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, label="Submit")
        btn_cancel = wx.Button(panel, label="Cancel")
        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)

        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        panel.SetSizer(sizer)

        btn_ok.Bind(wx.EVT_BUTTON, self.OnSubmit)
        btn_cancel.Bind(wx.EVT_BUTTON, lambda evt: self.Close())

        # Pre-fill examples
        self.tc_lat.SetValue("51.5074")
        self.tc_lon.SetValue("-0.1278")

    def OnSubmit(self, event):
        # Validate both controls using the validators
        if not self.Validate():
            wx.MessageBox("Please fix the highlighted fields.", "Validation failed", wx.ICON_ERROR)
            return

        lat = float(self.tc_lat.GetValue())
        lon = float(self.tc_lon.GetValue())
        wx.MessageBox(f"Latitude: {lat}\nLongitude: {lon}", "Values", wx.ICON_INFORMATION)


def run_demo():
    app = wx.App(False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    run_demo()