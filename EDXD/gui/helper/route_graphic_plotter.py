class RouteGraphicPanel(wx.Panel):
    def __init__(self, parent, route_data, line_height=20, width=40):
        """
        :param parent: The parent widget (usually the scroll_container or route_panel)
        :param route_data: List of dicts containing {'type': str, 'is_last': bool}
        :param line_height: Fixed height in pixels for each row
        :param width: Fixed width of the graphic column
        """
        super().__init__(parent, style=wx.NO_BORDER)
        self.route_data = route_data
        self.line_height = line_height

        # Set a fixed minimum size to prevent layout shifting
        total_height = len(route_data) * line_height
        self.SetMinSize((width, total_height))
        self.SetMaxSize((width, total_height))  # Force exact size

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        # Force a refresh when resized to ensure clean drawing
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()

        # Enable Anti-aliasing for smooth circles and lines
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        width = self.GetSize().GetWidth()
        center_x = width // 2

        # Colors based on your theme/logic
        color_orange = wx.Colour(255, 165, 0)  # 🟠
        color_blue = wx.Colour(0, 120, 255)  # 🔵 (Adjusted for visibility)
        color_line = wx.Colour(200, 200, 200)  # Subtle line color

        for i, data in enumerate(self.route_data):
            y_center = (i * self.line_height) + (self.line_height // 2)

            # 1. Draw the vertical line segment downwards
            # Only draw if this is not the very last item
            if i < len(self.route_data) - 1:
                dc.SetPen(wx.Pen(color_line, 2))
                dc.DrawLine(center_x, y_center, center_x, y_center + self.line_height)

            # 2. Draw the Circle (Node)
            radius = 6
            dc.SetPen(wx.Pen(wx.WHITE, 1))  # White border for contrast

            if data.get('is_neutron'):
                dc.SetBrush(wx.Brush(color_blue))
            else:
                dc.SetBrush(wx.Brush(color_orange))

            dc.DrawCircle(center_x, y_center, radius)

        # Optional: Draw a final endpoint marker if needed
        if self.route_data:
            last_y = (len(self.route_data) - 1) * self.line_height + (self.line_height // 2)
            dc.SetPen(wx.Pen(color_line, 2))
            # Draw a small tick at the very bottom if desired
            # dc.DrawLine(center_x - 5, last_y + self.line_height//2, center_x + 5, last_y + self.line_height//2)
