# A small helper to copy text into the system clipboard using wx.
# Put this under a utils or common package (adjust imports accordingly).
import wx

def copy_text_to_clipboard(text: str) -> bool:
    """Copy `text` to the system clipboard. Returns True on success."""
    if not text:
        return False
    try:
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(wx.TextDataObject(text))
            finally:
                wx.TheClipboard.Close()
            return True
    except Exception:
        # If the clipboard is busy or an unexpected error happens, swallow it.
        pass
    return False
