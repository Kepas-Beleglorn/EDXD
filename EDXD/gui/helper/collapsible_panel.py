import wx
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton

class CollapsiblePanel(wx.Panel):
    def __init__(self, parent, label="Panel Title", collapsed=False, columns: int = 1):
        super().__init__(parent)
        self.parent = parent
        self.label = label
        self.collapsed = collapsed
        self.columns = columns
        self.animation_duration = 200  # ms
        self.content_height = 0

        # Main sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        self.header = wx.Panel(self)
        self.header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.header_label = wx.StaticText(self.header, label=self.label)
        # Toggle button
        self.toggle_button = DynamicToggleButton(parent=self.header,
                label="–",
                is_toggled=self.collapsed,
                size=wx.Size(20,20),
                style=wx.FONTWEIGHT_BOLD
        )
        self.toggle_button.Bind(wx.EVT_BUTTON, self.on_toggle)

        init_widget(widget=self.header, title=self.label)
        init_widget(widget=self.header_label, title=self.label)
        init_widget(widget=self.toggle_button)

        self.header.SetBackgroundColour(wx.Colour("#221511"))

        self.header_sizer.Add(self.toggle_button, 0, wx.ALL, 5)
        self.header_sizer.Add(self.header_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.header.SetSizer(self.header_sizer)

        # Content container
        self.content = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content.SetSizer(self.content_sizer)
        self.content.Hide() if collapsed else self.content.Show()

        # Setup table
        self.table_sizer = None
        self.setup_table()

        # Layout
        self.main_sizer.Add(self.header, 0, wx.EXPAND)
        self.main_sizer.Add(self.content, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)

        # Initial layout
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.on_size)

    def setup_table(self):
        """Set up a table-like layout with two columns."""
        self.table_sizer = wx.FlexGridSizer(cols=self.columns)  # 2 columns, 5px gaps
        self.table_sizer.AddGrowableCol(self.columns - 1)
        self.content_sizer.Add(self.table_sizer, 1, wx.EXPAND | wx.ALL, 5)
        self.content_height = self.content.GetBestSize().height
        self.main_sizer.Layout()

    def reset_table(self):
        """Reset the table-like layout to its initial state."""
        """Clear all rows from the table."""
        for child in self.table_sizer.GetChildren():
            if child.GetWindow():
                child.GetWindow().Destroy()
        self.table_sizer.Clear()

    def add_table_item(self, label_text, align=wx.ALIGN_LEFT) -> wx.StaticText:
        """Add a row to the table."""
        label = wx.StaticText(self.content)
        init_widget(widget=label, title=label_text)
        self.table_sizer.Add(label, 0, align | wx.EXPAND, 5)
        return label

    def on_toggle(self, event):
        """Toggle collapse/expand state with animation."""
        self.collapsed = not self.collapsed
        target_height = 0 if self.collapsed else self.content_height

        # Update button label
        self.toggle_button.SetLabel("+" if self.collapsed else "–")

        # Animate
        self.animate_height(target_height)

    def animate_height(self, target_height):
        """Smoothly animate the content height."""
        start_height = self.content.GetSize().height
        steps = 10
        step_duration = self.animation_duration // steps
        delta = (target_height - start_height) / steps

        for i in range(steps):
            wx.CallLater(i * step_duration, self._set_content_height, start_height + delta * i)

        wx.CallLater(steps * step_duration, self._finalize_animation, target_height)

    def _set_content_height(self, height):
        """Set content height during animation."""
        self.content.SetMinSize((-1, height))
        self.content_sizer.Layout()
        self.main_sizer.Layout()
        self.Layout()

    def _finalize_animation(self, target_height):
        """Finalize animation and visibility."""
        self.content.SetMinSize((-1, target_height))
        self.content.Show() if target_height > 0 else self.content.Hide()
        self.main_sizer.Layout()
        self.Layout()

        # Call Layout on the top-level window to ensure everything is updated
        if self.GetParent():
            self.GetParent().Layout()

    def on_size(self, event):
        """Update content height on resize."""
        if not self.collapsed:
            self.content_height = self.content.GetBestSize().height
        event.Skip()

    def force_render(self):
        self.content.SetMinSize((-1, -1))
        self.content.Layout()
        self.content_sizer.Layout()
        self.main_sizer.Layout()
        self.Layout()
        if self.GetParent():
            self.GetParent().Layout()
