# EDXD/gui/helper/icon_loader.py
import base64
from io import BytesIO
import wx
from EDXD.globals import ICON_PNG_B64

def make_icon_bundle() -> wx.IconBundle:
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
