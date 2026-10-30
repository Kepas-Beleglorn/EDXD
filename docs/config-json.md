# `config.json` — Application Configuration

**Location:** `APP_DIR/config.json`

**Purpose:** Central application configuration file. Read at startup by `main.py` and `globals.py`; read/written by the config dialog (`gui/config.py`) and by window state persistence (`gui/helper/window_properties.py`). Controls journal paths, cache location, display filters, thresholds, and per-window geometry.

**Written by:** `main.py` (onboarding and defaults), `gui/config.py` (config dialog), `gui/helper/window_properties.py` (window state)

**Read by:** All modules via `globals.CFG_FILE`

## Structure

```json
{
  "journal_dir": "/home/user/Saved Games/Frontier Developments/Elite Dangerous",
  "cache_dir": "/home/user/.local/share/EDXD/system-data",
  "log_level": "INFO",
  "worthwhile_threshold": 1000000,
  "fuel_low_threshold": 10,
  "land": false,
  "ringed": false,
  "mat_sel": {
    "antimony": true,
    "arsenic": true,
    "boron": true,
    "cadmium": true,
    "carbon": true,
    "chromium": true,
    "germanium": true,
    "iron": true,
    "lead": true,
    "manganese": true,
    "mercury": true,
    "molybdenum": true,
    "nickel": true,
    "niobium": true,
    "phosphorus": true,
    "polonium": true,
    "rhenium": true,
    "ruthenium": true,
    "selenium": true,
    "sulphur": true,
    "technetium": true,
    "tellurium": true,
    "tin": true,
    "tungsten": true,
    "vanadium": true,
    "yttrium": true,
    "zinc": true,
    "zirconium": true
  },
  "amount_of_plotted_upcoming_systems_to_show": 10,
  "amount_of_plotted_passed_systems_to_show": 2,
  "first_run_done": true,
  "EDXD_MAIN": {
    "height": 800,
    "width": 1200,
    "posx": 500,
    "posy": 500,
    "is_hidden": false
  }
}
```

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `journal_dir` | `str` | `""` | Absolute path to the Elite Dangerous journal files directory |
| `cache_dir` | `str` | `APP_DIR / "system-data"` | Directory for `<systemID>.json` cache files |
| `log_level` | `str` | `"INFO"` | Logging verbosity: `"DEBUG"`, `"INFO"`, `"WARN"`, `"ERROR"` |
| `worthwhile_threshold` | `int` | `1000000` | Minimum estimated credit value to mark a body as "worthwhile" (💰 icon) |
| `fuel_low_threshold` | `int` | `10` | Fuel level (tonnes) below which a low-fuel warning is shown |
| `land` | `bool` | `false` | If `true`, filter table to show only landable bodies |
| `ringed` | `bool` | `false` | If `true`, filter table to show only ringed bodies |
| `mat_sel` | `dict` | All `true` | Per-material visibility toggles for the 28 planetary surface materials. Each key is a material name (see list below); each value is a boolean controlling column visibility |
| `amount_of_plotted_upcoming_systems_to_show` | `int` | `10` | Number of upcoming navigation route systems to display (max: 30) |
| `amount_of_plotted_passed_systems_to_show` | `int` | `2` | Number of passed navigation route systems to display (max: 10) |
| `first_run_done` | `bool` | — | If `true`, the onboarding flow is skipped on subsequent launches |
| `<window_id>` | `object` | — | Per-window state objects (one per window; see below) |

## Per-Window State Object

Each window in EDXD stores its geometry and visibility state under a unique window ID key. Common window IDs include `EDXD_MAIN`, `EDXD_CONFIGURATION`, and various detail panel IDs.

| Field | Type | Description |
|-------|------|-------------|
| `height` | `int` | Window height in pixels |
| `width` | `int` | Window width in pixels |
| `posx` | `int` | Window X position in pixels |
| `posy` | `int` | Window Y position in pixels |
| `is_hidden` | `bool` | Whether the window was hidden on last exit |

## Material Names (`mat_sel` keys)

The 28 planetary surface materials tracked by EDXD:

`antimony`, `arsenic`, `boron`, `cadmium`, `carbon`, `chromium`, `germanium`, `iron`, `lead`, `manganese`, `mercury`, `molybdenum`, `nickel`, `niobium`, `phosphorus`, `polonium`, `rhenium`, `ruthenium`, `selenium`, `sulphur`, `technetium`, `tellurium`, `tin`, `tungsten`, `vanadium`, `yttrium`, `zinc`, `zirconium`
