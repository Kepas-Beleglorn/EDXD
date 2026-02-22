from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import wx
import wx.grid as gridlib
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Collapsible Panel Demo")

        # Main sizer for the frame
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        init_widget(self)
        # Create panels
        self.panel1 = CollapsiblePanel(self, label="Details", columns=2)

        # Add rows
        self.panel1.add_table_row("short", "long first row")
        self.panel1.add_table_row("short2", "looooooong")


        self.panel2 = CollapsiblePanel(self, label="Details2", columns=2)
        self.panel2.add_table_row("short", "long first row")
        self.panel2.add_table_row("short2", "looooooong")

        # Add panels to the main sizer with wx.EXPAND flag
        main_sizer.Add(self.panel1, 0, wx.EXPAND)
        main_sizer.Add(self.panel2, 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.Fit()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
