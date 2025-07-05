import wx
import time, threading, inspect
import shutil, json
from pathlib import Path
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.journal_controller import JournalController
from EDXD.data_handler.status_json_watcher import StatusWatcher
from EDXD.globals import CACHE_DIR, logging, log_context
from EDXD.gui.helper.dynamic_frame import DynamicFrame
from EDXD.gui.helper.gui_dynamic_button import DynamicButton
from EDXD.gui.helper.gui_handler import init_widget
from EDXD.gui.helper.window_properties import WindowProperties
from EDXD.globals import DEFAULT_HEIGHT, DEFAULT_WIDTH, DEFAULT_POS_Y, DEFAULT_POS_X, RESIZE_MARGIN

TITLE = "ED journal historian"
WINID = "EDXD_JOURNAL_HISTORIAN"

class JournalHistorian(DynamicFrame):
    def __init__(self, journal_reader: JournalReader, journal_controller:JournalController, status_json_watcher: StatusWatcher):
        # 1. Load saved properties (or use defaults)
        props = WindowProperties.load(WINID, default_height=DEFAULT_HEIGHT, default_width=DEFAULT_WIDTH, default_posx=DEFAULT_POS_X, default_posy=DEFAULT_POS_Y)
        DynamicFrame.__init__(self, title=TITLE, win_id=WINID, parent=None, style=wx.NO_BORDER | wx.FRAME_SHAPED | wx.STAY_ON_TOP, show_minimize=True, show_maximize=True, show_close=True)
        # 2. Apply geometry
        init_widget(self, width=props.width, height=props.height, posx=props.posx, posy=props.posy, title=TITLE)

        self.journal_reader = journal_reader
        self.journal_controller = journal_controller
        self.status_json_watcher = status_json_watcher

        self.journal_dir = self.journal_reader.folder
        self.files = []
        self.total_files = 0
        self.current_index = 0
        self.start_time = None
        self.end_time = None

        self.lbl_current    = wx.StaticText(parent=self, label="Current File: N/A")
        self.lbl_filecount  = wx.StaticText(parent=self, label="File 0/0")
        self.lbl_start      = wx.StaticText(parent=self, label="Start Time: N/A")
        self.lbl_end        = wx.StaticText(parent=self, label="End Time: N/A")
        self.lbl_total      = wx.StaticText(parent=self, label="Total Time: N/A")
        self.progress       = wx.Gauge(parent=self, range=100, size=wx.Size(400, 30))
        self.btn_start      = DynamicButton(parent=self, label="Start Processing")

        init_widget(self.lbl_current)
        init_widget(self.lbl_filecount)
        init_widget(self.lbl_start)
        init_widget(self.lbl_end)
        init_widget(self.lbl_total)
        init_widget(self.progress)
        init_widget(self.btn_start)

        self.window_box.Add(self.lbl_current, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.lbl_filecount, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.lbl_start, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.lbl_end, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.lbl_total, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.progress, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)
        self.window_box.Add(self.btn_start, 0, wx.EXPAND | wx.EAST | wx.WEST | wx.SOUTH, RESIZE_MARGIN)

        self.SetSizer(self.window_box)

        self.btn_start.Bind(wx.EVT_BUTTON, self.on_start)

    def on_start(self, event):
        # Gather files
        self.files = self._get_sorted_journal_files(self.journal_dir)
        self.total_files = len(self.files)
        if self.total_files == 0:
            wx.MessageBox("No journal files found!", "Info")
            return
        self.current_index = 0
        self.progress.SetRange(self.total_files)
        self.start_time = time.time()
        self.lbl_start.SetLabel(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}")
        self.lbl_end.SetLabel("End Time: N/A")
        self.lbl_total.SetLabel("Total Time: N/A")
        self.btn_start.Disable()

        # Start processing in a background thread
        threading.Thread(target=self.process_all_journals, daemon=True).start()

    def _pause_threads(self):
        self.status_json_watcher.pause()
        self.journal_controller.pause()
        self.journal_reader.pause()

    def _resume_threads(self):
        self.journal_reader.resume()
        self.journal_controller.resume()
        self.status_json_watcher.resume()

    def process_all_journals(self):
        self._pause_threads()
        self._empty_directory(CACHE_DIR)

        journal_files = self._get_sorted_journal_files(self.journal_dir)
        for idx, file_path in enumerate(journal_files, 1):
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        evt = json.loads(line)
                        self.journal_controller.process_event(evt=evt, update_gui=False)
                    except Exception as e:
                        log_context(level=logging.WARN, frame=inspect.currentframe(), e=e)
                        continue
                    wx.CallAfter(self._update_ui, idx, file_path)

        self.end_time = time.time()
        wx.CallAfter(self._finish)
        self._resume_threads()

    @staticmethod
    def _empty_directory(directory: Path):
        for item in directory.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    @staticmethod
    def _get_sorted_journal_files(journal_dir: Path):
        journal_files = list(journal_dir.glob("Journal.*.log"))
        # Sort by last modified time (or use 'stat().st_ctime' for creation time on some systems)
        return sorted(journal_files, key=lambda f: f.stat().st_mtime)

    def _update_ui(self, idx, file_path):
        self.current_index = idx
        self.lbl_current.SetLabel(f"Current File: {file_path}")
        self.lbl_filecount.SetLabel(f"File {idx}/{self.total_files}")
        self.progress.SetValue(idx)

    def _finish(self):
        self.lbl_end.SetLabel(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time))}")
        total = self.end_time - self.start_time
        self.lbl_total.SetLabel(f"Total Time: {time.strftime('%H:%M:%S', time.gmtime(total))}")
        self.btn_start.Enable()