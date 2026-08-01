import re
import wx

# Regex: Allows optional negative sign, then either '0' alone or a non-zero digit followed by anything.
# Used for final validation.
_FULL_INT_RE = re.compile(r'^-?(0|[1-9]\d*)$')


class IntRangeValidator(wx.Validator):
    """
    wxPython Validator for integers within a specific range [min_val, max_val].

    Behavior:
    - Typing: Prevents non-integer characters and leading zeros immediately.
    - Real-time: Checks range constraints as you type.
    - Visual Feedback: Sets background to dark red (70, 20, 20) and bells on error.
    - Auto-Correct: Sanitizes pasted text (strips leading zeros) automatically.

    Usage:
        txt = wx.TextCtrl(panel, validator=IntRangeValidator(0, 100, allow_empty=False))
    """

    def __init__(self, min_val: int, max_val: int, allow_empty: bool = False):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.allow_empty = allow_empty
        self._original_bg_color = None

        # Bind events for real-time interception and validation
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def Clone(self):
        """Required by wx.Validator to create copies."""
        return IntRangeValidator(self.min_val, self.max_val, self.allow_empty)

    def Validate(self, win):
        """
        Called by wx's validation system (e.g., panel.Validate()).
        Performs final strict check.
        """
        tc = self.GetWindow()
        if not isinstance(tc, wx.TextCtrl):
            return True

        if self._original_bg_color is None:
            self._original_bg_color = tc.GetBackgroundColour()

        text = tc.GetValue().strip()
        err_color = wx.Colour(70, 20, 20)

        # 1. Check Empty
        if text == "":
            if self.allow_empty:
                tc.SetBackgroundColour(self._original_bg_color)
                tc.SetToolTip("")
                tc.Refresh()
                return True
            else:
                self._show_error(tc, "Value cannot be empty.", err_color)
                return False

        # 2. Check Integer Format (including no leading zeros)
        if not _FULL_INT_RE.match(text):
            self._show_error(tc, "Invalid format (no leading zeros).", err_color)
            return False

        # 3. Parse and Check Range
        try:
            val = int(text)
        except ValueError:
            self._show_error(tc, "Invalid integer format.", err_color)
            return False

        if val < self.min_val or val > self.max_val:
            self._show_error(tc, f"Value must be between {self.min_val} and {self.max_val}.", err_color)
            return False

        # Valid: Reset
        tc.SetBackgroundColour(self._original_bg_color)
        tc.SetToolTip("")
        tc.Refresh()
        return True

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True

    def OnChar(self, event):
        """
        Intercept keystrokes.
        Prevents invalid characters and leading zeros.
        """
        keycode = event.GetKeyCode()
        tc = self.GetWindow()
        if not tc:
            event.Skip()
            return

        current_val = tc.GetValue()
        cursor_pos = tc.GetInsertionPoint()
        selection = tc.GetSelection()
        is_selection_active = selection and selection[1] > 0

        # Allow Control/Meta keys (Copy/Paste/Undo/etc)
        if event.ControlDown() or event.MetaDown():
            event.Skip()
            return

        # Allow Navigation and Editing keys
        if keycode in (wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_LEFT, wx.WXK_RIGHT,
                       wx.WXK_HOME, wx.WXK_END, wx.WXK_TAB, wx.WXK_RETURN):
            event.Skip()
            return

        # Handle Digits
        if 48 <= keycode <= 57:
            digit_char = chr(keycode)

            # LOGIC: Prevent Leading Zeros
            # Determine what the text would look like if we allow this keystroke
            # We need to handle insertion vs replacement

            start, end = cursor_pos, cursor_pos
            if is_selection_active:
                start, end = selection[0], selection[1]

            # Construct potential new value
            potential_val = current_val[:start] + digit_char + current_val[end:]

            # If user is typing at the very beginning (or replacing start)
            if start == 0:
                # Case 1: Typing '0' as the first char
                if digit_char == '0':
                    # Allow if the result is just "0" or "-0" (though -0 is usually normalized later)
                    # Block if followed by more digits (e.g., "04")
                    if len(potential_val) > 1 and potential_val[1].isdigit():
                        # If the next char is a digit, this is a leading zero attempt
                        wx.Bell()
                        return

                # Case 2: Typing non-zero digit after a leading '0' that was already there?
                # Actually, OnText handles cleanup, but let's try to prevent it here too.
                # If current val is "0" and user types "5", we want "5", not "05".
                if current_val == "0" and not is_selection_active:
                    # Replace the 0 instead of appending
                    tc.ChangeValue(digit_char)
                    tc.SetInsertionPoint(1)
                    self._check_range_visual_only()
                    return  # Skip default processing since we manually changed value

            event.Skip()
            return

        # Allow Negative Sign '-'
        if keycode == ord('-'):
            # Only allow if not present, and cursor is at start
            if '-' in current_val:
                wx.Bell()
                return

            if cursor_pos == 0 or is_selection_active:
                # Check if adding '-' creates invalid state like "-05" immediately?
                # Usually okay to type "-", validation happens on next digit
                event.Skip()
                return
            else:
                wx.Bell()
                return

        # Block everything else
        wx.Bell()

    def OnText(self, event):
        """
        Sanitize pasted text or programmatic changes.
        Removes invalid chars and STRIPS leading zeros.
        """
        tc = self.GetWindow()
        if not tc:
            event.Skip()
            return

        raw = tc.GetValue()

        # 1. Keep only digits and one '-' at the start
        clean = ""
        has_dash = False

        for i, char in enumerate(raw):
            if char == '-' and i == 0 and not has_dash:
                clean += char
                has_dash = True
            elif char.isdigit():
                clean += char

        # 2. Remove Leading Zeros (Critical Step)
        # Pattern: If we have "0" followed by digits, remove the "0".
        # Exception: If the number is just "0" or "-0", keep it.
        if has_dash:
            # Handle negative numbers: "-007" -> "-7", "-0" -> "-0" (then maybe normalized to 0)
            body = clean[1:]
            if len(body) > 1:
                body = body.lstrip('0') or '0'  # Ensure at least one 0 remains if all were zeros
            clean = "-" + body
        else:
            # Handle positive numbers: "007" -> "7", "0" -> "0"
            if len(clean) > 1:
                clean = clean.lstrip('0') or '0'

        # If cleaning changed the value, update the control
        if clean != raw:
            pos = tc.GetInsertionPoint()
            tc.ChangeValue(clean)
            # Restore cursor roughly
            tc.SetInsertionPoint(min(pos, len(clean)))

        # Trigger real-time validation logic immediately
        self._check_range_visual_only()

        event.Skip()

    def OnKillFocus(self, event):
        """Final validation when user leaves the field."""
        self.Validate(self.GetWindow())
        event.Skip()

    def _check_range_visual_only(self):
        """
        Checks range and updates color/tooltips without blocking input.
        """
        tc = self.GetWindow()
        if not tc:
            return

        if self._original_bg_color is None:
            self._original_bg_color = tc.GetBackgroundColour()

        text = tc.GetValue().strip()
        err_color = wx.Colour(70, 20, 20)

        # If empty
        if text == "":
            if not self.allow_empty:
                pass
            tc.SetBackgroundColour(self._original_bg_color)
            tc.SetToolTip("")
            tc.Refresh()
            return

        # If incomplete (just "-"), treat as neutral
        if text == "-":
            tc.SetBackgroundColour(self._original_bg_color)
            tc.SetToolTip("")
            tc.Refresh()
            return

        # If valid integer format (matches our no-leading-zero regex)
        if _FULL_INT_RE.match(text):
            try:
                val = int(text)
                if val < self.min_val or val > self.max_val:
                    tc.SetBackgroundColour(err_color)
                    tc.SetToolTip(f"Must be between {self.min_val} and {self.max_val}")
                    tc.Refresh()
                else:
                    tc.SetBackgroundColour(self._original_bg_color)
                    tc.SetToolTip("")
                    tc.Refresh()
            except ValueError:
                pass
        else:
            # Invalid format (e.g. leading zero detected, or other garbage)
            tc.SetBackgroundColour(err_color)
            tc.SetToolTip("Invalid format (no leading zeros)")
            tc.Refresh()

    def _show_error(self, tc, message, color):
        """Helper to apply error state."""
        tc.SetBackgroundColour(color)
        tc.SetToolTip(message)
        tc.Refresh()
        wx.Bell()
