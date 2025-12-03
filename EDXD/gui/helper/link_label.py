import wx

class LinkLabel(wx.StaticText):
    def __init__(self, parent, label="", url=""):
        super().__init__(parent, label=label, style=wx.ST_NO_AUTORESIZE)
        self.url = url
        self.SetForegroundColour(wx.Colour(200, 150, 50))
        font = self.GetFont()
        font.SetUnderlined(True)
        self.SetFont(font)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        self.Bind(wx.EVT_LEFT_UP, self.on_click)

    def on_click(self, _evt):
        # Either:
        # webbrowser.open(self.url)  # stdlib
        # Or:
        wx.LaunchDefaultBrowser(self.url)  # uses OS default handler
