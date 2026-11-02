# EDXD/gui/helper/icon_loader.py
import base64
from io import BytesIO
import wx


def make_icon_bundle() -> wx.IconBundle:
    from EDXD.globals import ICON_PNG_B64
    raw = base64.b64decode(ICON_PNG_B64)
    img = wx.Image(BytesIO(raw), wx.BITMAP_TYPE_PNG)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    bundle = wx.IconBundle()
    for s in sizes:
        scaled = img.Scale(s, s, wx.IMAGE_QUALITY_HIGH)
        bmp = wx.Bitmap(scaled)
        ico = wx.Icon()
        ico.CopyFromBitmap(bmp)
        bundle.AddIcon(ico)
    return bundle

def get_bitmap_from_base64(base64_string, icon_size) -> wx.Bitmap:
    # Decode base64 -> bytes and load as wx.Image from memory
    raw = base64.b64decode(base64_string)
    stream = BytesIO(raw)
    image = wx.Image(stream, wx.BITMAP_TYPE_PNG)

    # Scale and convert to Bitmap
    scaled = image.Scale(icon_size, icon_size, wx.IMAGE_QUALITY_HIGH)
    bmp = wx.Bitmap(scaled)

    # StaticBitmap expects a wx.Bitmap (not a BitmapBundle)
    return bmp