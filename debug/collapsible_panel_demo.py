from EDXD.gui.helper.collapsible_panel import CollapsiblePanel
import wx
import wx.grid as gridlib
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Collapsible Panel Demo")
        self.panel = CollapsiblePanel(self, label="Details")
        sizer = wx.FlexGridSizer(cols=1, hgap=0, vgap=0)
        sizer.AddGrowableCol(0)
        init_widget(self)
        # Config items grid
        self.grid = gridlib.Grid(self.panel.content)
        self.grid.CreateGrid(2, 2)

        self.grid.SetRowLabelSize(0)
        self.grid.SetSelectionMode(gridlib.Grid.GridSelectNone)
        self.grid.DisableDragGridSize()  # Prevents grid line drag-resizing
        self.grid.EnableDragRowSize(False)  # Disables row resizing
        self.grid.EnableDragColSize(False)  # Disables column resizing
        self.grid.EnableEditing(False)  # Already in your code
        self.grid.HideColLabels()
        self.grid.ClearSelection()  # To clear any selection if needed

        self.grid.SetCellValue(0, 0, "short")
        self.grid.SetCellValue(0, 1, "long first row")
        self.grid.SetCellValue(1, 0, "short2")
        self.grid.SetCellValue(1, 1, "looooooong")

        self.grid.SetColSize(0, 50)
        self.grid.SetColSize(1, 300)

        self.panel.add_content(self.grid)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.panel, 1, wx.EXPAND | wx.ALL, 1)
        sizer.Add(box, 1, wx.EXPAND | wx.ALL, 1)
        #todo: try flex grid for data, instead of nested Grid
        self.panel2 = CollapsiblePanel(self, label="Details2")

        self.grid2 = gridlib.Grid(self.panel2.content)
        self.grid2.CreateGrid(2, 2)

        self.grid2.SetRowLabelSize(0)
        self.grid2.SetSelectionMode(gridlib.Grid.GridSelectNone)
        self.grid2.DisableDragGridSize()  # Prevents grid line drag-resizing
        self.grid2.EnableDragRowSize(False)  # Disables row resizing
        self.grid2.EnableDragColSize(False)  # Disables column resizing
        self.grid2.EnableEditing(False)  # Already in your code
        self.grid2.HideColLabels()
        self.grid2.ClearSelection()  # To clear any selection if needed

        self.grid2.SetCellValue(0, 0, "short")
        self.grid2.SetCellValue(0, 1, "long first row")
        self.grid2.SetCellValue(1, 0, "short2")
        self.grid2.SetCellValue(1, 1, "looooooong")

        self.grid2.SetColSize(0, 50)
        self.grid2.SetColSize(1, 300)

        self.panel2.add_content(self.grid2)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.panel2, 1, wx.EXPAND | wx.ALL, 1)
        sizer.Add(box2, 1, wx.EXPAND | wx.ALL, 1)


        sizer.AddGrowableRow(sizer.EffectiveRowsCount - 1)

        self.SetSizer(sizer)
        #self.Fit()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
