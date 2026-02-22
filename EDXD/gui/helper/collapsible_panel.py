import wx
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.gui_dynamic_toggle_button import DynamicToggleButton

class CollapsiblePanel(wx.Panel):
    def __init__(self, parent, label="Panel Title", collapsed=False):
        super().__init__(parent)
        self.parent = parent
        self.label = label
        self.collapsed = collapsed
        self.animation_duration = 200  # ms
        self.content_height = 0

        # Main sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header (clickable)
        self.header = wx.Panel(self)
        self.header.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.header_label = wx.StaticText(self.header, label=self.label)
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

        self.header_sizer.Add(self.toggle_button, 0, wx.ALL, 5)
        self.header_sizer.Add(self.header_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.header.SetSizer(self.header_sizer)

        # Content container
        self.content = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content.SetSizer(self.content_sizer)
        self.content.Hide() if collapsed else self.content.Show()

        # Layout
        self.main_sizer.Add(self.header, 0, wx.EXPAND)
        self.main_sizer.Add(self.content, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)

        # Initial layout
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_toggle(self, event):
        """Toggle collapse/expand state with animation."""
        self.collapsed = not self.collapsed
        target_height = 0 if self.collapsed else self.content_height

        # Update button icon
        self.toggle_button.SetLabelText("+" if self.collapsed else "–")

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

    def add_content(self, widget, proportion=1, flag=wx.EXPAND, border=5):
        """Add a widget to the content area."""
        if hasattr(widget, 'Name'):
            init_widget(widget)
        else:
            for item in widget.GetChildren():
                if hasattr(item, 'Name'):
                    init_widget(item)

        self.content_sizer.Add(widget, proportion, flag, border)
        self.content_height = self.content.GetBestSize().height
        self.main_sizer.Layout()

    def set_label(self, label):
        """Update the panel label."""
        self.label = label
        self.header_label.SetLabel(label)

    def is_collapsed(self):
        """Return collapse state."""
        return self.collapsed

    def collapse(self):
        """Collapse the panel."""
        if not self.collapsed:
            self.on_toggle(None)

    def expand(self):
        """Expand the panel."""
        if self.collapsed:
            self.on_toggle(None)
