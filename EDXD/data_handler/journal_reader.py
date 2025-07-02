import threading, time, queue
import EDXD.data_handler.helper.data_helper as dh
from EDXD.data_handler.helper.pausable_thread import PausableThread
from pathlib import Path

# ---------------------------------------------------------------------------
# tailer thread – reads the newest Journal file
# ---------------------------------------------------------------------------
class JournalReader(PausableThread, threading.Thread):
    def __init__(self, folder: Path, out_queue: "queue.Queue[str]"):
        super().__init__()
        self.folder = folder
        self.queue  = out_queue
        self.fp     = None
        self.cur    = None

    def _process_data(self):
        if self.fp is None:
            self.cur = dh.latest_journal(self.folder)
            if not self.cur:
                time.sleep(1)
                return
            self.fp = self.cur.open("r", encoding="utf-8")  # start at top

        line = self.fp.readline()
        if line:
            self.queue.put(line)
        else:
            lat = dh.latest_journal(self.folder)
            if lat and lat != self.cur:
                self.fp.close()
                self.cur = lat
                self.fp = self.cur.open("r", encoding="utf-8")
            else:
                time.sleep(0.2)
