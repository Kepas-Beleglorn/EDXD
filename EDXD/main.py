#!/usr/bin/env python3
import os
import sys
from pathlib import Path

os.environ['GIO_MODULE_SKIP'] = 'gvfs'
os.environ.pop("GTK_IM_MODULE", None)

# Handle Wayland/X11 backend selection - MUST be before ANY wx import
if 'WAYLAND_DISPLAY' in os.environ:
    os.environ['GDK_BACKEND'] = 'x11'
    os.environ['GTK_BACKEND'] = 'x11'
    # Don't set DISPLAY here - let the system handle it
    print("🖥️  Wayland detected. Forcing X11 backend...")

# Workaround for wxPython + GTK3 + KDE Plasma crashes:
# The Breeze GTK theme engine can cause segfaults in wxPython's MainLoop().
# Setting GTK_THEME=Adwaita:Dark can also crash if the theme variant is missing.
# Instead, write the theme preference to GTK settings.ini so GTK uses Adwaita
# with the dark variant natively, without GTK_THEME override.
# See: https://github.com/wxWidgets/Phoenix/issues/2455
desktop_env = os.getenv("XDG_CURRENT_DESKTOP", "")
if "KDE" in desktop_env:
    gtk_settings_dir = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "gtk-3.0"
    gtk_settings = gtk_settings_dir / "settings.ini"

    # Write Adwaita theme to settings.ini so GTK uses it natively.
    # This avoids the GTK_THEME env var which can cause crashes.
    # GTK will use Adwaita:Dark automatically when gtk-application-prefer-dark-theme is true.
    try:
        gtk_settings_dir.mkdir(parents=True, exist_ok=True)
        # Read existing settings to preserve them
        existing = ""
        if gtk_settings.is_file():
            existing = gtk_settings.read_text(encoding="utf-8")

        # Build new settings, preserving existing [Settings] section content
        has_settings_section = "[Settings]" in existing
        lines = []
        in_settings = False
        found_theme = False
        found_dark = False

        if has_settings_section:
            for line in existing.splitlines():
                if line.strip() == "[Settings]":
                    in_settings = True
                    lines.append(line)
                elif line.strip().startswith("[") and in_settings:
                    in_settings = False
                    lines.append(line)
                elif in_settings and line.strip().startswith("gtk-theme-name"):
                    lines.append("gtk-theme-name = Adwaita")
                    found_theme = True
                elif in_settings and line.strip().startswith("gtk-application-prefer-dark-theme"):
                    lines.append("gtk-application-prefer-dark-theme = true")
                    found_dark = True
                else:
                    lines.append(line)
            if not found_theme:
                # Add theme name to [Settings] section
                insert_idx = None
                for i, line in enumerate(lines):
                    if line.strip() == "[Settings]":
                        insert_idx = i + 1
                        break
                if insert_idx is not None:
                    lines.insert(insert_idx, "gtk-theme-name = Adwaita")
            if not found_dark:
                # Add dark theme preference to [Settings] section
                insert_idx = None
                for i, line in enumerate(lines):
                    if line.strip() == "[Settings]":
                        insert_idx = i + 1
                        break
                if insert_idx is not None:
                    lines.insert(insert_idx, "gtk-application-prefer-dark-theme = true")
        else:
            # Create new [Settings] section
            if existing and not existing.endswith("\n\n"):
                existing += "\n" if existing.endswith("\n") else "\n\n"
            lines = [existing, "[Settings]", "gtk-theme-name = Adwaita", "gtk-application-prefer-dark-theme = true"]

        gtk_settings.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass

# Initialize logging early, before any other module logs
from EDXD.globals import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)

import queue
# version handling
from pathlib import Path

from EDXD.data_handler.journal_controller import JournalController
from EDXD.data_handler.journal_reader import JournalReader
from EDXD.data_handler.model import Model
from EDXD.data_handler.status_json_watcher import StatusWatcher
from EDXD.globals import CFG_FILE, RAW_MATS, DEFAULT_WORTHWHILE_THRESHOLD, DEFAULT_FUEL_LOW_THRESHOLD, args, \
    DEFAULT_AMOUNT_OF_PLOTTED_UPCOMING_SYSTEMS_TO_SHOW, DEFAULT_AMOUNT_OF_PLOTTED_PASSED_SYSTEMS_TO_SHOW
from EDXD.gui.main_window import MainFrame

import wx
if "--debug" not in sys.argv:
    wx.Log.SetLogLevel(wx.LOG_Error)

def _from_pyproject() -> str | None:
    try:
        try:
            import tomllib  # py311+
        except ModuleNotFoundError:
            import tomli as tomllib
        pyproj = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if not pyproj.exists():
            return None
        data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        return data.get("project", {}).get("version")
    except Exception:
        return None
try:
    from EDXD._version import VERSION as __version__
except Exception:
    __version__ = "0.0.0.0"

# Safely import the runtime font utilities (optional — no hard failure if absent)
try:
    from EDXD.gui.helper import font_utils as _font_utils
except Exception:
    _font_utils = None

from EDXD.edxd_single_instance import SingleInstance
from typing import Optional
_instance: Optional[SingleInstance] = None

def _is_first_run(cfg: dict) -> bool:
    """
    Check if this is a truly fresh install of EDXD.
    
    A fresh install is one where:
    - first_run_done is not set AND
    - no journal_dir is configured (meaning the user has never set up the app)
    
    This ensures that users upgrading from an older version (which may not have
    the first_run_done flag) do not see the welcome screen unnecessarily.
    """
    if cfg.get("first_run_done", False):
        return False
    # If journal_dir is already configured, this is an existing installation (possibly upgraded)
    if cfg.get("journal_dir"):
        return False
    return True

def _mark_first_run_done(cfg: dict) -> None:
    """Mark the first run as complete in the config."""
    cfg["first_run_done"] = True

def _show_onboarding_flow(app: wx.App, cfg: dict) -> dict:
    """
    Show the welcome screen and configuration panel for first-time users.
    Returns the updated config dict with journal_dir set.
    """
    from EDXD.gui.welcome_screen import WelcomeScreen
    from EDXD.gui.config import EDXDConfig

    # Show welcome screen
    welcome = WelcomeScreen(parent=None)
    welcome.ShowModal()
    welcome.Destroy()

    # Mark first run as complete BEFORE showing the config dialog.
    # This ensures that if the config dialog triggers a restart, the flag is already saved.
    _mark_first_run_done(cfg)

    # Set default values before showing the config dialog so they are pre-filled
    cfg.setdefault("worthwhile_threshold", DEFAULT_WORTHWHILE_THRESHOLD)
    cfg.setdefault("amount_of_plotted_upcoming_systems_to_show", DEFAULT_AMOUNT_OF_PLOTTED_UPCOMING_SYSTEMS_TO_SHOW)
    cfg.setdefault("amount_of_plotted_passed_systems_to_show", DEFAULT_AMOUNT_OF_PLOTTED_PASSED_SYSTEMS_TO_SHOW)

    # Save the config with first_run_done and defaults before showing the config dialog
    import json
    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}
        CFG_FILE.write_text(json.dumps(data, indent=2))
    cfg["save"] = _save
    cfg["save"]()

    # Show configuration panel
    config_dlg = EDXDConfig(parent=None)
    config_dlg.ShowModal()
    config_dlg.Destroy()

    # Reload config after user has set it
    cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}

    return cfg

def main():
    logger.info("Application starting")

    # check if another instance of EDXD is already running (working from v0.6.0.0)
    global _instance
    _instance = SingleInstance()
    _instance.acquire_or_exit()

    import json
    app = wx.App(False)
    app.SetAppName("EDXD")
    app.SetVendorName("EDXD")

    # Register embedded fonts for the running process (if the helper is present).
    # This should run before any controls/windows are created so font discovery/fallback works.
    try:
        if _font_utils is not None:
            _font_utils.register_embedded_fonts()
    except Exception:
        # keep startup robust — don't crash if font registration fails
        import logging
        logging.getLogger(__name__).exception("Embedded font registration failed")

    cfg = json.loads(CFG_FILE.read_text()) if CFG_FILE.exists() else {}

    if args.journals:
        cfg["journal_dir"] = str(args.journals.expanduser())
        # If first run with --journals, mark onboarding as complete
        if _is_first_run(cfg):
            _mark_first_run_done(cfg)
        CFG_FILE.write_text(json.dumps(cfg, indent=2))

    # Check if this is a first run and show onboarding flow
    journal_dir = Path(cfg.get("journal_dir", ""))

    # First-run onboarding: show welcome screen regardless of whether journal_dir is set
    # Skip onboarding if --journals is provided on command line (user is configuring manually)
    if not args.journals and (_is_first_run(cfg) or not CFG_FILE.exists()):
        logger.info("First run detected, showing onboarding flow")
        cfg = _show_onboarding_flow(app, cfg)
        # Reload journal_dir from the updated config
        journal_dir = Path(cfg.get("journal_dir", ""))
        logger.info("Onboarding flow completed, journal_dir: %s", journal_dir)

    # If still no valid journal directory after onboarding, exit
    if not journal_dir.is_dir():
        logger.error("Invalid journal directory: %s", journal_dir)
        sys.exit("Run once with --journals <Saved Games …>")
    else:
        logger.info("Journal directory: %s", journal_dir)

    cfg.setdefault("land", False)
    cfg.setdefault("ringed", False)
    cfg.setdefault("mat_sel", {m: True for m in RAW_MATS})
    cfg.setdefault("amount_of_plotted_upcoming_systems_to_show", DEFAULT_AMOUNT_OF_PLOTTED_UPCOMING_SYSTEMS_TO_SHOW)
    cfg.setdefault("amount_of_plotted_passed_systems_to_show", DEFAULT_AMOUNT_OF_PLOTTED_PASSED_SYSTEMS_TO_SHOW)
    if "worthwhile_threshold" not in cfg.keys():
        cfg["worthwhile_threshold"] = DEFAULT_WORTHWHILE_THRESHOLD

    if "fuel_low_threshold" not in cfg.keys():
        cfg["fuel_low_threshold"] = DEFAULT_FUEL_LOW_THRESHOLD

    q = queue.Queue()
    model = Model()
    journal_reader = JournalReader(journal_dir, q)
    journal_reader.start()
    logger.info("Journal reader started")
    journal_controller = JournalController(q, model, cfg)
    journal_controller.start()
    logger.info("Journal controller started")

    def _save():
        data = {k: v for k, v in cfg.items() if k != "save"}
        CFG_FILE.write_text(json.dumps(data, indent=2))

    # ensure defaults even if file is old
    cfg["save"] = _save  # ← make the save-function available
    cfg["save"]()

    status_watcher = StatusWatcher(journal_dir / "Status.json", model)
    status_watcher.start()
    logger.info("Status watcher started")

    frame = MainFrame(model=model, prefs=cfg, journal_reader=journal_reader, journal_controller=journal_controller, status_watcher=status_watcher)
    logger.info("Main window created")

    # Try to apply the app font/theme using the font_utils helper (if available).
    # This is optional: if font_utils implements apply_app_fonts or set helpers, use them.
    try:
        if _font_utils is not None:
            # If your font_utils provides apply_app_fonts, this will set fonts recursively.
            apply_fn = getattr(_font_utils, "apply_app_fonts", None)
            if callable(apply_fn):
                apply_fn(frame, text_face="Noto Sans", emoji_face="Noto Color Emoji", base_size=10)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Applying app fonts failed")

    frame.Show()
    logger.info("Application main loop starting")

    app.MainLoop()

    logger.info("Application shutting down")
    if _instance is not None:
        _instance.release()

if __name__ == "__main__":
    main()
