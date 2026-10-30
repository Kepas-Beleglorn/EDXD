# EDXD Data Formats

This document describes the JSON data files used by EDXD at runtime. All files are stored in the application data directory (`APP_DIR`), which defaults to the platform-specific user data folder (e.g., `~/.local/share/EDXD` on Linux, `~/Library/Application Support/EDXD` on macOS, `%APPDATA%\EDXD` on Windows). When running in `--portable` mode, all files are stored alongside the binary.

---

## Format Reference

| File | Description | Documentation |
|------|-------------|---------------|
| `<systemID>.json` | Per-system scan data cache | [system-id-json.md](system-id-json.md) |
| `edxd_ship_status.json` | Current ship identity and fuel characteristics | [edxd-ship-status-json.md](edxd-ship-status-json.md) |
| `edxd_timestamp.json` | Last processed journal entry timestamp | [edxd-timestamp-json.md](edxd-timestamp-json.md) |
| `config.json` | Application configuration | [config-json.md](config-json.md) |
| `slef_loadout.json` | Spansh loadout exchange format | [slef-loadout-json.md](slef-loadout-json.md) |

---

## File Relationships

The following diagram shows how the data files interact:

```
Journal files ──► JournalController
                     │
                     ├─► edxd_timestamp.json    (tracks progress)
                     ├─► edxd_ship_status.json  (ship identity & fuel)
                     ├─► slef_loadout.json      (on Loadout event)
                     └─► <systemID>.json        (scan/mapping data)

config.json ──► All modules (controls behavior, paths, thresholds)
slef_loadout.json ──► SpanshRoutePlotter ──► Route calculation
edxd_ship_status.json ──► Engine status display, jump range display
```
