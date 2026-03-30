import re
import wx

# Regex for internal logic: only digits allowed
_DIGITS_RE = re.compile(r"^\d*$")


class PositiveIntFormatterValidator(wx.Validator):
    """
    wxPython Validator for positive integers with automatic thousands-separator
    formatting and a currency suffix (' Cr').

    Behavior:
    - Typing: Only digits (0-9) are allowed.
    - On Focus Loss (Tab/Click away): Formats value as '1,000,000 Cr'.
    - On Focus Gain (Click/Tab in): Reverts to raw '1000000' for easy editing.
    - Validation: Ensures content is a valid positive integer.

    Usage:
        txt = wx.TextCtrl(panel, validator=PositiveIntFormatterValidator())
    """

    # Define the suffix constant here for easy modification
    SUFFIX = " Cr"

    def __init__(self):
        super().__init__()
        # Bind events required for formatting logic
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFormat)
        self.Bind(wx.EVT_SET_FOCUS, self.OnUnformat)

    def Clone(self):
        """Required by wx.Validator to create copies."""
        return PositiveIntFormatterValidator()

    def Validate(self, win):
        """
        Called when panel.Validate() is invoked or dialog is closed.
        Ensures the current content is a valid positive integer.
        """
        tc = self.GetWindow()
        if not isinstance(tc, wx.TextCtrl):
            return True

        text = tc.GetValue().strip()

        # If empty, treat as invalid (unless you specifically want to allow empty)
        if not text:
            self._show_error(tc, "Value cannot be empty.")
            return False

        # Strip the suffix and any whitespace for validation
        clean_text = text.replace(self.SUFFIX, '').strip()

        if not clean_text.isdigit():
            self._show_error(tc, "Must be a positive integer.")
            return False

        # Optional: Check range here if needed (e.g., > 0)
        val = int(clean_text)
        if val < 0:
            self._show_error(tc, "Must be positive.")
            return False

        # Valid: Reset color and tooltip
        tc.SetBackgroundColour(wx.NullColour)
        tc.SetToolTip("")
        tc.Refresh()
        return True

    def TransferToWindow(self):
        """Called when data is transferred from validator to window."""
        return True

    def TransferFromWindow(self):
        """Called when data is transferred from window to validator."""
        # Ensure the raw value is available if the parent reads it directly
        return True

    def OnChar(self, event):
        """Filter keystrokes: Allow only digits and control keys."""
        keycode = event.GetKeyCode()

        # Allow control keys (Backspace, Delete, Arrows, Tab, Enter, Ctrl+C/V/X/A)
        if keycode in (wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_LEFT, wx.WXK_RIGHT,
                       wx.WXK_HOME, wx.WXK_END, wx.WXK_TAB, wx.WXK_RETURN):
            event.Skip()
            return

        if event.ControlDown() or event.MetaDown():
            event.Skip()
            return

        # Allow only digits (0-9)
        if 48 <= keycode <= 57:
            event.Skip()
            return

        # Block everything else (including '.', '-', letters, etc.)
        wx.Bell()

    def OnText(self, event):
        """Sanitize pasted text or programmatic changes."""
        tc = self.GetWindow()
        raw = tc.GetValue()

        # Remove anything that isn't a digit
        # We also strip the suffix here if it was pasted in accidentally
        clean = re.sub(r'[^0-9]', '', raw)

        if clean != raw:
            pos = tc.GetInsertionPoint()
            tc.ChangeValue(clean)
            # Try to restore cursor position reasonably
            tc.SetInsertionPoint(min(pos, len(clean)))

        event.Skip()

    def OnFormat(self, event):
        """
        Called when focus leaves the control.
        Converts '1000000' -> '1,000,000 Cr'.
        """
        tc = self.GetWindow()
        raw = tc.GetValue().strip()

        # Strip existing suffix and spaces to get raw digits
        clean = raw.replace(self.SUFFIX, '').strip()

        if clean and clean.isdigit():
            num = int(clean)
            formatted = f"{num:,}{self.SUFFIX}"

            # Only update if the display needs to change
            if formatted != raw:
                tc.ChangeValue(formatted)

        event.Skip()

    def OnUnformat(self, event):
        """
        Called when focus enters the control.
        Converts '1,000,000 Cr' -> '1000000' for easy editing.
        """
        tc = self.GetWindow()
        raw = tc.GetValue()

        # Check if suffix exists to avoid unnecessary updates
        if self.SUFFIX in raw:
            clean = raw.replace(self.SUFFIX, '').strip()
            clean = clean.replace(',', '').strip()
            tc.ChangeValue(clean)
            # Place cursor at the end for convenience
            tc.SetInsertionPointEnd()

        event.Skip()

    def RefreshFormatAndValidate(self):
        """
        Call this after SetValue() to force formatting (commas/suffix)
        and validation checks immediately.
        """
        tc = self.GetWindow()
        if not tc:
            return False

        # 1. Force the formatting logic (OnFormat)
        dummy_event = wx.FocusEvent(wx.wxEVT_KILL_FOCUS)
        result = self.Validate(tc)
        self.OnFormat(dummy_event)

        # 2. Run standard validation
        return result

    def _show_error(self, tc, message):
        """Helper to show visual error feedback."""
        tc.SetBackgroundColour(wx.Colour(70, 20, 20))  # Dark red background
        tc.SetToolTip(message)
        tc.Refresh()
        wx.Bell()

