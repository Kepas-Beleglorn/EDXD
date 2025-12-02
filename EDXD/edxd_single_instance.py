#!/usr/bin/env python3
"""
Single-instance helper for EDXD.

Usage:
    from edxd.single_instance import SingleInstance
    instance = SingleInstance()            # defaults to filelock if installed
    instance.acquire_or_exit()
    # keep `instance` alive for the duration of the program

This module:
 - prefers a file lock (requires `filelock` package)
 - falls back to a localhost socket bind if `filelock` is not available
 - cleans up on atexit and common signals
"""
from __future__ import annotations

import atexit
import os
import signal
import socket
import sys
from pathlib import Path
from typing import Optional

# try filelock
try:
    from filelock import FileLock, Timeout  # type: ignore
    _HAS_FILELOCK = True
except Exception:
    _HAS_FILELOCK = False
    FileLock = None  # type: ignore
    Timeout = Exception  # type: ignore


def _default_lock_dir() -> Path:
    """Return a per-user directory suitable for storing the lock file."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home()
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_RUNTIME_DIR") or
                    os.environ.get("XDG_CONFIG_HOME") or
                    Path.home() / ".config")
    path = Path(base) / "EDXD"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        # fallback to temp dir if creation fails
        path = Path(os.path.abspath(os.path.join(os.path.sep, "tmp"))) / "edxd"
        path.mkdir(parents=True, exist_ok=True)
    return path


class SingleInstance:
    """
    Manage single-instance behavior.

    By default uses filelock if installed; otherwise falls back to socket.
    """
    def __init__(self, method: str = "auto", socket_port: int = 45067) -> None:
        """
        method: "filelock" or "socket" or "auto" (auto -> use filelock if installed)
        socket_port: port used when using the socket fallback (localhost only)
        """
        self.method = method.lower()
        if self.method == "auto":
            self.method = "filelock" if _HAS_FILELOCK else "socket"
        if self.method == "filelock" and not _HAS_FILELOCK:
            raise RuntimeError("filelock package is not installed; set method='socket' or install filelock")
        self.socket_port = socket_port

        # internals
        self._file_lock: Optional["FileLock"] = None
        self._socket: Optional[socket.socket] = None
        self._locked = False

    def acquire_or_exit(self) -> None:
        """Try to acquire the lock. If another instance holds it, exit(0) immediately."""
        if self.method == "filelock":
            self._acquire_filelock_or_exit()
        elif self.method == "socket":
            self._acquire_socket_or_exit()
        else:
            raise ValueError("unknown method: %r" % self.method)

        # register cleanup and signal handlers so lock is released
        atexit.register(self.release)
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._signal_handler)
            except Exception:
                # some environments (e.g., windows or threads) may not allow us to register all signals
                pass

    def _acquire_filelock_or_exit(self) -> None:
        lockfile = _default_lock_dir() / "edxd.lock"
        # FileLock will create the file and apply an OS-level advisory lock
        lock = FileLock(str(lockfile))
        try:
            lock.acquire(timeout=0)  # timeout=0 -> raise immediately if locked
        except Timeout:
            # another instance is running
            # lightweight, non-verbose exit (change to logging if you prefer)
            print("EDXD is already running (file lock). Exiting.")
            sys.exit(0)
        self._file_lock = lock
        self._locked = True

    def _acquire_socket_or_exit(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to localhost only
        try:
            # On some platforms you may want to set SO_REUSEADDR, but that can let
            # another recent process rebind the same port; skipping for exclusivity.
            s.bind(("127.0.0.1", self.socket_port))
            s.listen(1)
        except OSError:
            print(f"EDXD is already running (socket {self.socket_port}). Exiting.")
            try:
                s.close()
            except Exception:
                pass
            sys.exit(0)
        # keep socket open for the lifetime of the process
        self._socket = s
        self._locked = True

    def _signal_handler(self, signum, frame):
        # release and re-raise default to allow termination
        self.release()
        try:
            signal.signal(signum, signal.SIG_DFL)
        except Exception:
            pass
        os.kill(os.getpid(), signum)

    def release(self) -> None:
        """Release the held lock (safe to call multiple times)."""
        if not self._locked:
            return
        if self._file_lock is not None:
            try:
                self._file_lock.release()
            except Exception:
                pass
            self._file_lock = None
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._locked = False

    def is_locked(self) -> bool:
        return self._locked


# Simple test/demo when run as a script
if __name__ == "__main__":
    inst = SingleInstance(method="auto")
    inst.acquire_or_exit()
    print("Lock acquired. Press Ctrl+C to exit.")
    try:
        # keep running
        while True:
            signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        inst.release()