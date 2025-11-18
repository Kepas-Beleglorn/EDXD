"""
Runtime utilities to register fonts that were embedded into the package
(as bytes in EDXD/fonts_embedded.py) so they become available to the process.

Call register_embedded_fonts() early in your wx.App.OnInit (before creating windows).
"""
import atexit
import ctypes
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# try to import the generated module; if it's missing, nothing to do
try:
    from EDXD.resources.fonts import fonts_embedded

    _FONT_FILES = getattr(fonts_embedded, "FONT_FILES", {}) or {}
except Exception:
    _FONT_FILES = {}

# track temp files/dirs for cleanup
_temp_dir = None
_registered_windows_buffers = []


def _ensure_temp_dir():
    global _temp_dir
    if _temp_dir is None:
        _temp_dir = Path(tempfile.mkdtemp(prefix="edxd_fonts_"))
    return _temp_dir


def _write_fonts_to_temp():
    td = _ensure_temp_dir()
    written = []
    for name, data in _FONT_FILES.items():
        p = td / name
        if not p.exists():
            p.write_bytes(data)
        written.append(p)
    return written


# ---------------- Windows: register from memory ----------------
def _register_fonts_windows_from_memory():
    if not _FONT_FILES:
        return False
    try:
        gdi32 = ctypes.windll.gdi32
    except Exception:
        return False
    added = False
    # AddFontMemResourceEx signature: HANDLE AddFontMemResourceEx(PVOID pbFont, DWORD cbFont, PVOID pdv, DWORD *pcFonts)
    AddFontMemResourceEx = gdi32.AddFontMemResourceEx
    AddFontMemResourceEx.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
    AddFontMemResourceEx.restype = ctypes.c_void_p

    for name, data in _FONT_FILES.items():
        buf = ctypes.create_string_buffer(data)
        count = ctypes.c_uint(0)
        res = AddFontMemResourceEx(ctypes.byref(buf), ctypes.c_uint(len(data)), None, ctypes.byref(count))
        if res:
            # keep the buffer alive for process lifetime so the font stays registered
            _registered_windows_buffers.append(buf)
            added = True
    return added


# ---------------- macOS: write to temp and register via CoreText ----------------
def _register_fonts_macos_from_files(file_paths):
    # Use CTFontManagerRegisterFontsForURL to register for process.
    try:
        cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        ct = ctypes.CDLL('/System/Library/Frameworks/CoreText.framework/CoreText')
    except Exception:
        return False
    # CFURLCreateFromFileSystemRepresentation
    CFURLCreateFromFileSystemRepresentation = cf.CFURLCreateFromFileSystemRepresentation
    CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
    CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
    CTFontManagerRegisterFontsForURL = ct.CTFontManagerRegisterFontsForURL
    CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
    CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
    success = False
    kCTFontManagerScopeProcess = 1
    for p in file_paths:
        b_path = str(p).encode('utf-8')
        cfurl = CFURLCreateFromFileSystemRepresentation(None, b_path, len(b_path), False)
        if not cfurl:
            continue
        ok = CTFontManagerRegisterFontsForURL(cfurl, kCTFontManagerScopeProcess, None)
        if ok:
            success = True
    return success


# ---------------- Linux: write to temp and run fc-cache on that directory ----------------
def _register_fonts_linux_from_files(dir_path):
    try:
        # run fc-cache only for our temp directory
        subprocess.run(["fc-cache", "-f", str(dir_path)], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def register_embedded_fonts():
    """
    Register embedded fonts for the running process.
    Returns True if any registration succeeded.
    Call before creating GUI windows.
    """
    if not _FONT_FILES:
        return False

    if sys.platform.startswith("win"):
        return _register_fonts_windows_from_memory()

    # for other platforms, write to a temp directory and register
    written = _write_fonts_to_temp()
    if not written:
        return False

    td = Path(_ensure_temp_dir())
    ok = False
    if sys.platform.startswith("linux"):
        ok = _register_fonts_linux_from_files(td)
    elif sys.platform.startswith("darwin"):
        ok = _register_fonts_macos_from_files(written)
    else:
        # unknown platform -> leave as written files (they might be picked up)
        ok = True
    return ok


def cleanup_embedded_fonts(remove_temp=True):
    """
    Remove temporary files and cleanup. On Windows the AddFontMem registration
    stays for the process lifetime; we only release temp dir.
    """
    global _temp_dir
    if _temp_dir and remove_temp:
        try:
            shutil.rmtree(_temp_dir)
        except Exception:
            pass
        _temp_dir = None
    # keep the windows buffers alive until process exit; no extra cleanup required


# ensure we remove temp dir on process exit
atexit.register(cleanup_embedded_fonts)
