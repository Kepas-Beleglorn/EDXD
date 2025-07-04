import json, threading, time, inspect
from EDXD.data_handler.model import Model
from EDXD.data_handler.helper.pausable_thread import PausableThread
from pathlib import Path
from EDXD.globals import DEBUG_STATUS_JSON, DEBUG_PATH, BODY_ID_PREFIX, logging, log_context
bip = BODY_ID_PREFIX

# ---------------------------------------------------------------------------
# StatusWatcher – polls Status.json for Destination.Name
# ---------------------------------------------------------------------------
class StatusWatcher(PausableThread, threading.Thread):
    def __init__(self, status_file: Path, model: Model, poll=0.5):
        super().__init__()
        self.path   = status_file
        self.model  = model
        self.poll   = poll
        self.last_body   = None           # last Destination.Name we saw
        self.last_timestamp = None        # last timestamp, so we can log only new lines

    def _process_data(self):
        try:
            data = json.loads(self.path.read_text())
            dest = data.get("Destination", {})
            body_id = bip + str(dest.get("Body"))
            timestamp = data.get("timestamp")
            if DEBUG_STATUS_JSON and timestamp and timestamp != self.last_timestamp:
                self.last_timestamp = timestamp
                self._write_debug_log(data)

            if body_id and body_id != self.last_body:
                self.last_body = body_id
                self.model.set_target(body_id)

        except Exception as e:
            log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
            pass  # ignore read/JSON errors
        time.sleep(self.poll)

    @staticmethod
    def _write_debug_log(data):
        if not DEBUG_PATH.exists():
            DEBUG_PATH.mkdir()
        output_path = DEBUG_PATH / "DEBUG_Status.json"
        # Serialize the data
        serialized = json.dumps(data, separators=(',', ':'))
        # Append to the file
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(serialized + "\n")
