import threading, time
# ---------------------------------------------------------------------------
# pausable threads
# ---------------------------------------------------------------------------
class PausableThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.paused = threading.Event()  # Add this
        self.paused.clear()  # Not paused by default

    def pause(self):
        self.paused.set()

    def resume(self):
        self.paused.clear()

    def run(self):
        while True:
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            self._process_data()

    def _process_data(self):
        # implement
        pass
    