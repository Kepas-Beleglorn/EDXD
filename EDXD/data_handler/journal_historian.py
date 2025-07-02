import shutil, json
from EDXD.globals import logging
from pathlib import Path
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.journal_controller import JournalController
from EDXD.data_handler.status_json_watcher import StatusWatcher
from EDXD.globals import CACHE_DIR

class JournalHistorian:
    def __init__(self, journal_reader: JournalReader, journal_controller:JournalController, status_json_watcher: StatusWatcher):
        self.journal_reader = journal_reader
        self.journal_controller = journal_controller
        self.status_json_watcher = status_json_watcher

    def _pause_threads(self):
        self.status_json_watcher.pause()
        self.journal_controller.pause()
        self.journal_reader.pause()

    def _resume_threads(self):
        self.journal_reader.resume()
        self.journal_controller.resume()
        self.status_json_watcher.resume()

    def process_all_journals(self):
        logging.info("Processing all journals")
        self._pause_threads()
        self._empty_directory(CACHE_DIR)

        journal_files = self._get_sorted_journal_files(self.journal_reader.folder)
        for file_path in journal_files:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        evt = json.loads(line)
                        self.journal_controller.process_event(evt=evt, update_gui=False)
                    except Exception:
                        continue
        self._resume_threads()
        logging.info("Journals processed")

    def _empty_directory(self, directory: Path):
        for item in directory.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def _get_sorted_journal_files(self, journal_dir: Path):
        journal_files = list(journal_dir.glob("Journal.*.log"))
        # Sort by last modified time (or use 'stat().st_ctime' for creation time on some systems)
        return sorted(journal_files, key=lambda f: f.stat().st_mtime)